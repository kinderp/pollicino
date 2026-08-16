from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import urllib.request
import zlib
from pathlib import Path
from statistics import mean

import py7zr
import torch
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

from pollicino.compression.adaptive import (
    AdaptiveNGramCDFProvider,
    NeuralPriorAdaptiveCDFProvider,
    adaptive_fingerprint,
)
from pollicino.compression.classical_experts import RunLengthCDFProvider, run_length_fingerprint
from pollicino.compression.codec import decode_pol, encode_shared, inspect_pol
from pollicino.compression.gating import DeterministicExpertGateCDFProvider, expert_gate_fingerprint
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint
from pollicino.compression.routing import CostAwareSpecialistRouterCDFProvider, cost_aware_router_fingerprint
from pollicino.compression.sequential_routing import (
    SequentialSpecialistRouterCDFProvider,
    sequential_router_fingerprint,
)

PRECISION = 18
DEV_TRACE_BYTES = 256
HOLDOUT_SLICE = 4096
MEANINGFUL_GAIN_BPB = 0.05
MIN_OBSERVATIONS = (8, 16, 32)
MAX_PROBES = (64, 128, 256)
RATIO_BITS = (1, 2, 4, 8)
CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)

PSEUDO_REAL_BASE = "https://pizzachili.dcc.uchile.cl/repcorpus/pseudo-real"
PSEUDO_REAL = {
    "xml-mut": ("xml-repetitive", "dblp.xml.0001.1.7z"),
    "dna-mut": ("dna-repetitive", "dna.001.1.7z"),
    "english-mut": ("english-repetitive", "english.001.2.7z"),
    "proteins-mut": ("proteins-repetitive", "proteins.001.1.7z"),
    "sources-mut": ("source-code-repetitive", "sources.001.2.7z"),
}
EXPECTED_PSEUDO_REAL_BYTES = 100 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def cdf_term(cdf, symbol: int) -> tuple[int, int]:
    return int(cdf[symbol + 1]) - int(cdf[symbol]), int(cdf[-1])


def compare_ratio(
    specialist_num: int,
    specialist_den: int,
    cheap_num: int,
    cheap_den: int,
    numerator: int,
    denominator: int,
) -> int:
    left = specialist_num * cheap_den * denominator
    right = cheap_num * specialist_den * numerator
    return (left > right) - (left < right)


def simulate_policy(trace: list[tuple[int, int, int, int]], policy: dict) -> tuple[str, int]:
    cheap_num = cheap_den = specialist_num = specialist_den = 1
    for index, (cn, cd, sn, sd) in enumerate(trace, start=1):
        cheap_num *= cn
        cheap_den *= cd
        specialist_num *= sn
        specialist_den *= sd
        if index < policy["min_observations"]:
            continue
        if compare_ratio(
            specialist_num,
            specialist_den,
            cheap_num,
            cheap_den,
            policy["activate_ratio"],
            1,
        ) > 0:
            return "neural-gate", index
        if compare_ratio(
            specialist_num,
            specialist_den,
            cheap_num,
            cheap_den,
            1,
            policy["reject_ratio_den"],
        ) < 0:
            return "cheap-gate", index
        if index >= policy["max_probe_bytes"]:
            return "cheap-gate", index
    return "cheap-gate", min(len(trace), policy["max_probe_bytes"])


def extract_pseudo_real(name: str, category: str, filename: str) -> tuple[bytes, dict]:
    url = f"{PSEUDO_REAL_BASE}/{filename}"
    request = urllib.request.Request(url, headers={"User-Agent": "POLLICINO-PILOT-009/1.0"})
    archive = urllib.request.urlopen(request, timeout=120).read()
    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        archive_path = td / filename
        archive_path.write_bytes(archive)
        extract_dir = td / "out"
        extract_dir.mkdir()
        with py7zr.SevenZipFile(archive_path, mode="r") as seven:
            seven.extractall(path=extract_dir)
        files = [p for p in extract_dir.rglob("*") if p.is_file()]
        if not files:
            raise RuntimeError(f"{filename}: archive contained no files")
        source = max(files, key=lambda p: p.stat().st_size)
        size = source.stat().st_size
        if size != EXPECTED_PSEUDO_REAL_BYTES:
            raise RuntimeError(f"{filename}: extracted {size} bytes, expected {EXPECTED_PSEUDO_REAL_BYTES}")
        with source.open("rb") as handle:
            sample = handle.read(HOLDOUT_SLICE)
        full_sha = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                full_sha.update(chunk)
    return sample, {
        "file": name,
        "category": category,
        "archive_name": filename,
        "source_url": url,
        "archive_bytes": len(archive),
        "archive_sha256": sha(archive),
        "full_bytes": size,
        "full_sha256": full_sha.hexdigest(),
        "sample_bytes": len(sample),
        "sample_sha256": sha(sample),
    }


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004_for_p9")
    p5 = load_module(ROOT / "experiments/pilot-005/run.py", "pilot005_for_p9")
    p6 = load_module(ROOT / "experiments/pilot-006/run.py", "pilot006_for_p9")
    p7 = load_module(ROOT / "experiments/pilot-007/run.py", "pilot007_for_p9")
    p8 = load_module(ROOT / "experiments/pilot-008/run.py", "pilot008_for_p9")
    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
    p8_results = json.loads((ROOT / "experiments/pilot-008/results.json").read_text())

    model, spec, training = p5.prepare_frozen_model()
    neural_fp = torch_model_fingerprint(model, spec)
    if neural_fp.hex() != p7_results["neural_gate"]["canonical_neural_fingerprint"]:
        raise RuntimeError("frozen neural fingerprint did not reproduce")

    adaptive_cfgs = {
        "adaptive-o0": dict(max_order=0, order_weights=(1,), base_count=1),
        "adaptive-o1": dict(max_order=1, order_weights=(1, 4), base_count=1),
        "adaptive-o2": dict(max_order=2, order_weights=(1, 4, 16), base_count=1),
        "adaptive-o3": ADAPTIVE_CFG,
    }
    cheap_fps = [adaptive_fingerprint(**adaptive_cfgs[name]) for name in CHEAP_NAMES[:-1]] + [
        run_length_fingerprint(run_weight=64)
    ]
    cheap_window = int(p7_results["cheap_gate"]["selected_window"])
    cheap_fp = expert_gate_fingerprint(expert_fingerprints=cheap_fps, names=CHEAP_NAMES, window=cheap_window)

    def cheap_factory():
        return DeterministicExpertGateCDFProvider(
            [
                AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o0"]),
                AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o1"]),
                AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o2"]),
                AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o3"]),
                RunLengthCDFProvider(run_weight=64),
            ],
            names=CHEAP_NAMES,
            window=cheap_window,
        )

    adaptive_fp = adaptive_fingerprint(**ADAPTIVE_CFG)
    prior256_fp = adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=256, neural_fingerprint=neural_fp)
    prior1024_fp = adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=1024, neural_fingerprint=neural_fp)
    neural_fps = (adaptive_fp, neural_fp, prior256_fp, prior1024_fp)
    neural_window = int(p7_results["neural_gate"]["window"])
    neural_gate_fp = expert_gate_fingerprint(expert_fingerprints=neural_fps, names=NEURAL_NAMES, window=neural_window)

    def neural_factory():
        shared_prior = PyTorchCDFProvider(model, spec, precision_bits=PRECISION, device="cpu")
        return DeterministicExpertGateCDFProvider(
            [
                AdaptiveNGramCDFProvider(**ADAPTIVE_CFG),
                shared_prior,
                NeuralPriorAdaptiveCDFProvider(shared_prior, prior_strength=256, **ADAPTIVE_CFG),
                NeuralPriorAdaptiveCDFProvider(shared_prior, prior_strength=1024, **ADAPTIVE_CFG),
            ],
            names=NEURAL_NAMES,
            window=neural_window,
        )

    def trace_evidence(data: bytes, limit: int = DEV_TRACE_BYTES):
        cheap = cheap_factory()
        specialist = neural_factory()
        prefix: list[int] = []
        trace = []
        for index, symbol in enumerate(data[:limit]):
            ccdf = cheap(index, prefix)
            scdf = specialist(index, prefix)
            cn, cd = cdf_term(ccdf, symbol)
            sn, sd = cdf_term(scdf, symbol)
            trace.append((cn, cd, sn, sd))
            prefix.append(symbol)
        return trace

    def roundtrip(data: bytes, factory, fingerprint: bytes) -> dict:
        encoder = factory()
        started = time.perf_counter()
        blob = encode_shared(data, encoder, fingerprint, precision_bits=PRECISION)
        enc = time.perf_counter() - started
        decoder = factory()
        started = time.perf_counter()
        restored = decode_pol(blob, shared_provider=decoder, expected_model_fingerprint=fingerprint)
        dec = time.perf_counter() - started
        assert restored == data
        info = inspect_pol(blob)
        result = {
            "payload_bpb": info["payload_bpb"],
            "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc,
            "decode_seconds": dec,
        }
        if hasattr(encoder, "selected_route"):
            result["selected_route"] = encoder.selected_route
        if hasattr(encoder, "decision_byte"):
            result["decision_byte"] = encoder.decision_byte
            result["probe_count"] = encoder.probe_count
            result["specialist_calls"] = encoder.specialist_calls
        return result

    # Development labels come only from already-consumed PILOT-007/008 data.
    dev_bpb = {}
    for row in read_csv(ROOT / "experiments/pilot-007/silesia.csv"):
        dev_bpb[row["file"]] = (float(row["cheap_payload_bpb"]), float(row["neural_gate_payload_bpb"]))
    for row in read_csv(ROOT / "experiments/pilot-008/large.csv"):
        dev_bpb[row["file"]] = (float(row["cheap_payload_bpb"]), float(row["neural_payload_bpb"]))

    silesia_files, _silesia_manifest = p7.download_silesia()
    largezip = p4.download(p8.LARGE_URL, OUT / "large-dev.zip")
    large = p4.unpack(largezip, p8.LARGE)
    dev_samples = {name: raw[:HOLDOUT_SLICE] for name, raw in silesia_files.items()}
    dev_samples.update({name: raw[:HOLDOUT_SLICE] for name, raw in large.items()})

    traces = {}
    dev_targets = {}
    for name, sample in dev_samples.items():
        traces[name] = trace_evidence(sample)
        cheap_bpb, neural_bpb = dev_bpb[name]
        gain = cheap_bpb - neural_bpb
        dev_targets[name] = "neural-gate" if gain >= MEANINGFUL_GAIN_BPB else "cheap-gate"
        print("DEV-TRACE", name, gain, dev_targets[name], flush=True)

    candidate_rows = []
    best_key = None
    best_policy = None
    for min_obs in MIN_OBSERVATIONS:
        for max_probe in MAX_PROBES:
            if max_probe < min_obs:
                continue
            for bits in RATIO_BITS:
                activate = 1 << bits
                reject_den = 1 << bits
                policy = {
                    "min_observations": min_obs,
                    "max_probe_bytes": max_probe,
                    "activate_ratio": activate,
                    "reject_ratio_den": reject_den,
                }
                predictions = {name: simulate_policy(trace, policy) for name, trace in traces.items()}
                correct = sum(predictions[name][0] == dev_targets[name] for name in dev_targets)
                false_positive = sum(
                    dev_targets[name] == "cheap-gate" and predictions[name][0] == "neural-gate"
                    for name in dev_targets
                )
                false_negative = sum(
                    dev_targets[name] == "neural-gate" and predictions[name][0] == "cheap-gate"
                    for name in dev_targets
                )
                mean_decision = mean(value[1] for value in predictions.values())
                row = {
                    **policy,
                    "ratio_bits": bits,
                    "correct": correct,
                    "false_positive": false_positive,
                    "false_negative": false_negative,
                    "mean_decision_byte": mean_decision,
                }
                candidate_rows.append(row)
                key = (correct, -false_positive, -false_negative, -mean_decision, -max_probe, -min_obs)
                if best_key is None or key > best_key:
                    best_key = key
                    best_policy = policy
    assert best_policy is not None
    print("SELECTED", json.dumps(best_policy), flush=True)

    def sequential_factory(stream_bytes: int, *, specialist_available: bool = True, min_stream_bytes: int = 0):
        def factory():
            specialist = neural_factory() if specialist_available else None
            return SequentialSpecialistRouterCDFProvider(
                cheap_factory(),
                specialist,
                stream_bytes=stream_bytes,
                min_stream_bytes=min_stream_bytes,
                min_observations=best_policy["min_observations"],
                max_probe_bytes=best_policy["max_probe_bytes"],
                activate_ratio_num=best_policy["activate_ratio"],
                activate_ratio_den=1,
                reject_ratio_num=1,
                reject_ratio_den=best_policy["reject_ratio_den"],
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
        return factory

    def sequential_fp(stream_bytes: int, *, specialist_available: bool = True, min_stream_bytes: int = 0):
        return sequential_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp if specialist_available else None,
            stream_bytes=stream_bytes,
            min_stream_bytes=min_stream_bytes,
            min_observations=best_policy["min_observations"],
            max_probe_bytes=best_policy["max_probe_bytes"],
            activate_ratio_num=best_policy["activate_ratio"],
            activate_ratio_den=1,
            reject_ratio_num=1,
            reject_ratio_den=best_policy["reject_ratio_den"],
        )

    def fixed_factory(stream_bytes: int):
        def factory():
            return CostAwareSpecialistRouterCDFProvider(
                cheap_factory(),
                neural_factory(),
                stream_bytes=stream_bytes,
                probe_bytes=int(p8_results["primary_policy"]["probe_bytes"]),
                min_stream_bytes=0,
                required_ratio_num=1,
                required_ratio_den=1,
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
        return factory

    def fixed_fp(stream_bytes: int):
        return cost_aware_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp,
            stream_bytes=stream_bytes,
            probe_bytes=int(p8_results["primary_policy"]["probe_bytes"]),
            min_stream_bytes=0,
            required_ratio_num=1,
            required_ratio_den=1,
        )

    # New untouched holdout: small downloadable pseudo-real Pizza&Chili archives.
    holdout_rows = []
    holdout_manifest = []
    for name, (category, archive_name) in PSEUDO_REAL.items():
        sample, manifest = extract_pseudo_real(name, category, archive_name)
        holdout_manifest.append(manifest)
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        fixed = roundtrip(sample, fixed_factory(len(sample)), fixed_fp(len(sample)))
        sequential = roundtrip(sample, sequential_factory(len(sample)), sequential_fp(len(sample)))
        no_model = roundtrip(
            sample,
            sequential_factory(len(sample), specialist_available=False),
            sequential_fp(len(sample), specialist_available=False),
        )
        base = baselines(sample)
        row = {
            "file": name,
            "category": category,
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "fixed_router_payload_bpb": fixed["payload_bpb"],
            "fixed_router_route": fixed["selected_route"],
            "sequential_payload_bpb": sequential["payload_bpb"],
            "sequential_pol1_bpb": sequential["pol1_bpb"],
            "sequential_route": sequential["selected_route"],
            "decision_byte": sequential["decision_byte"],
            "probe_count": sequential["probe_count"],
            "specialist_calls": sequential["specialist_calls"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "neural_encode_seconds": neural["encode_seconds"],
            "fixed_encode_seconds": fixed["encode_seconds"],
            "sequential_encode_seconds": sequential["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "neural_decode_seconds": neural["decode_seconds"],
            "sequential_decode_seconds": sequential["decode_seconds"],
            "no_model_payload_bpb": no_model["payload_bpb"],
            "no_model_route": no_model["selected_route"],
            **base,
        }
        holdout_rows.append(row)
        print("HOLDOUT", name, sequential["selected_route"], sequential["decision_byte"], sequential["payload_bpb"], flush=True)

    # Regression controls are reporting only, never tuning inputs.
    artzip = p4.download(p4.ART_URL, OUT / "artificl.zip")
    art = p4.unpack(artzip, p4.ART)
    self_test = p6.frozen_test_split()[:HOLDOUT_SLICE]
    controls = []
    for name, category, sample in [
        ("self-v2-test", "training-domain-test", self_test),
        ("aaa.txt", "repetition", art["aaa.txt"][:HOLDOUT_SLICE]),
        ("random.txt", "random-64-symbol-alphabet", art["random.txt"][:HOLDOUT_SLICE]),
    ]:
        sequential = roundtrip(sample, sequential_factory(len(sample)), sequential_fp(len(sample)))
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        controls.append({
            "file": name,
            "category": category,
            "sequential_payload_bpb": sequential["payload_bpb"],
            "sequential_route": sequential["selected_route"],
            "decision_byte": sequential["decision_byte"],
            "specialist_calls": sequential["specialist_calls"],
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "sequential_encode_seconds": sequential["encode_seconds"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "neural_encode_seconds": neural["encode_seconds"],
        })

    holdout_agg = {
        "files": len(holdout_rows),
        "mean_cheap_bpb": mean(r["cheap_payload_bpb"] for r in holdout_rows),
        "mean_neural_bpb": mean(r["neural_payload_bpb"] for r in holdout_rows),
        "mean_fixed_router_bpb": mean(r["fixed_router_payload_bpb"] for r in holdout_rows),
        "mean_sequential_bpb": mean(r["sequential_payload_bpb"] for r in holdout_rows),
        "mean_zlib_bpb": mean(r["zlib_bpb"] for r in holdout_rows),
        "mean_zstd19_bpb": mean(r["zstd19_bpb"] for r in holdout_rows),
        "sequential_neural_routes": sum(r["sequential_route"] == "neural-gate" for r in holdout_rows),
        "sequential_cheap_routes": sum(r["sequential_route"] == "cheap-gate" for r in holdout_rows),
        "fixed_neural_routes": sum(r["fixed_router_route"] == "neural-gate" for r in holdout_rows),
        "mean_decision_byte": mean(r["decision_byte"] or 0 for r in holdout_rows),
        "mean_sequential_encode_seconds": mean(r["sequential_encode_seconds"] for r in holdout_rows),
        "mean_fixed_encode_seconds": mean(r["fixed_encode_seconds"] for r in holdout_rows),
        "mean_neural_encode_seconds": mean(r["neural_encode_seconds"] for r in holdout_rows),
        "mean_cheap_encode_seconds": mean(r["cheap_encode_seconds"] for r in holdout_rows),
    }

    results = {
        "experiment_id": "pilot-009-confidence-aware-sequential-routing",
        "base_commit": os.environ.get("GITHUB_SHA", "local"),
        "question": "Can sequential evidence thresholds activate or reject the neural specialist earlier than a fixed probe while preserving deterministic lossless decoding?",
        "development": {
            "corpora": ["PILOT-007 Silesia", "PILOT-008 Large Corpus subset"],
            "meaningful_gain_bpb": MEANINGFUL_GAIN_BPB,
            "trace_bytes": DEV_TRACE_BYTES,
            "targets": dev_targets,
            "candidate_grid": {
                "min_observations": list(MIN_OBSERVATIONS),
                "max_probe_bytes": list(MAX_PROBES),
                "ratio_bits": list(RATIO_BITS),
            },
            "selected_policy": best_policy,
        },
        "new_holdout": {
            "name": "Pizza&Chili pseudo-real fixed five-file subset",
            "aggregate": holdout_agg,
            "rows": holdout_rows,
            "manifest": holdout_manifest,
        },
        "controls": controls,
        "model": {
            "canonical_neural_fingerprint": neural_fp.hex(),
            "cheap_gate_fingerprint": cheap_fp.hex(),
            "neural_gate_fingerprint": neural_gate_fp.hex(),
        },
        "protocol": {
            "precision_bits": PRECISION,
            "holdout_slice_bytes": HOLDOUT_SLICE,
            "selector_side_bits": 0,
            "holdout_not_used_for_tuning": True,
            "default_after_ambiguous_max_probe": "cheap-gate",
        },
        "limits": [
            "The Pizza&Chili pseudo-real subset is deliberately repetitive and is not a universal real-world benchmark.",
            "Only the first 4096 decoded bytes of each 100 MiB pseudo-real file are entropy-coded in this pilot.",
            "Development route labels use a predeclared 0.05 bpb minimum neural gain; this is a policy choice, not an information-theoretic constant.",
            "The neural checkpoint is assumed shared for neural-route payload measurements.",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (OUT / "holdout-manifest.json").write_text(json.dumps(holdout_manifest, indent=2) + "\n")
    csvout(OUT / "candidate-policies.csv", candidate_rows)
    csvout(OUT / "holdout.csv", holdout_rows)
    csvout(OUT / "controls.csv", controls)
    print(json.dumps({"selected_policy": best_policy, "holdout": holdout_agg, "controls": controls}, indent=2))


if __name__ == "__main__":
    main()
