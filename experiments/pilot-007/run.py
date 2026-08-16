from __future__ import annotations

import bz2
import csv
import hashlib
import importlib.util
import json
import os
import sys
import time
import urllib.request
import zlib
from pathlib import Path
from statistics import mean

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

PRECISION = 18
SLICE = 2048
DEV_WINDOWS = (16, 64, 256)
CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)
SILESIA_BASE = "https://sun.aei.polsl.pl/~sdeor/corpus"
SILESIA = {
    "dickens": ("english-text", 10_192_446),
    "ooffice": ("windows-dll", 6_152_192),
    "osdb": ("mysql-database", 10_085_684),
    "reymont": ("polish-pdf", 6_627_202),
    "xml": ("xml", 5_345_280),
    "x-ray": ("medical-xray", 8_474_240),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def download_silesia() -> tuple[dict[str, bytes], list[dict]]:
    files: dict[str, bytes] = {}
    manifest = []
    for name, (category, expected_size) in SILESIA.items():
        url = f"{SILESIA_BASE}/{name}.bz2"
        request = urllib.request.Request(url, headers={"User-Agent": "POLLICINO-PILOT-007/1.0"})
        compressed = urllib.request.urlopen(request, timeout=120).read()
        raw = bz2.decompress(compressed)
        if len(raw) != expected_size:
            raise RuntimeError(f"Silesia {name}: {len(raw)} != {expected_size}")
        files[name] = raw
        manifest.append({
            "file": name,
            "category": category,
            "bytes": len(raw),
            "sha256": sha(raw),
            "source_url": url,
            "compressed_bytes": len(compressed),
            "compressed_sha256": sha(compressed),
        })
        print("SILESIA-DOWNLOAD", name, len(raw), flush=True)
    return files, manifest


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004_for_p7")
    p5 = load_module(ROOT / "experiments/pilot-005/run.py", "pilot005_for_p7")
    p6 = load_module(ROOT / "experiments/pilot-006/run.py", "pilot006_for_p7")
    p6_results = json.loads((ROOT / "experiments/pilot-006/results.json").read_text())

    model, spec, training = p5.prepare_frozen_model()
    neural_fp = torch_model_fingerprint(model, spec)
    expected_neural_fp = p6_results["neural_model"]["canonical_fingerprint"]
    if neural_fp.hex() != expected_neural_fp:
        raise RuntimeError("frozen neural fingerprint did not reproduce")
    checkpoint_bytes = int(p6_results["neural_model"]["checkpoint_bytes"])

    adaptive_cfgs = {
        "adaptive-o0": dict(max_order=0, order_weights=(1,), base_count=1),
        "adaptive-o1": dict(max_order=1, order_weights=(1, 4), base_count=1),
        "adaptive-o2": dict(max_order=2, order_weights=(1, 4, 16), base_count=1),
        "adaptive-o3": ADAPTIVE_CFG,
    }
    cheap_fps = [
        adaptive_fingerprint(**adaptive_cfgs[name]) for name in CHEAP_NAMES[:-1]
    ] + [run_length_fingerprint(run_weight=64)]

    def cheap_factory(window: int):
        def factory():
            return DeterministicExpertGateCDFProvider(
                [
                    AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o0"]),
                    AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o1"]),
                    AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o2"]),
                    AdaptiveNGramCDFProvider(**adaptive_cfgs["adaptive-o3"]),
                    RunLengthCDFProvider(run_weight=64),
                ],
                names=CHEAP_NAMES,
                window=window,
            )
        return factory

    def cheap_fp(window: int) -> bytes:
        return expert_gate_fingerprint(expert_fingerprints=cheap_fps, names=CHEAP_NAMES, window=window)

    adaptive_fp = adaptive_fingerprint(**ADAPTIVE_CFG)
    prior256_fp = adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=256, neural_fingerprint=neural_fp)
    prior1024_fp = adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=1024, neural_fingerprint=neural_fp)
    neural_fps = (adaptive_fp, neural_fp, prior256_fp, prior1024_fp)
    neural_window = int(p6_results["gate"]["selected_window"])

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

    neural_gate_fp = expert_gate_fingerprint(
        expert_fingerprints=neural_fps,
        names=NEURAL_NAMES,
        window=neural_window,
    )

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
        if hasattr(encoder, "choice_counts") and hasattr(decoder, "choice_counts"):
            assert encoder.choice_counts == decoder.choice_counts
        info = inspect_pol(blob)
        result = {
            "payload_bpb": info["payload_bpb"],
            "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc,
            "decode_seconds": dec,
        }
        if hasattr(encoder, "choice_fractions"):
            result["choice_fractions"] = encoder.choice_fractions()
        return result

    # Development: tune only the cheap-gate window on already-consumed Canterbury/Artificial slices.
    canzip = p4.download(p4.CAN_URL, OUT / "cantrbry.zip")
    artzip = p4.download(p4.ART_URL, OUT / "artificl.zip")
    can = p4.unpack(canzip, p4.CAN)
    art = p4.unpack(artzip, p4.ART)
    dev_sources = {**can, **art}
    dev_names = list(p5.REPRESENTATIVE) + list(p5.ARTIFICIAL_REP)
    development = []
    for window in DEV_WINDOWS:
        values = []
        for name in dev_names:
            sample = dev_sources[name][:SLICE]
            result = roundtrip(sample, cheap_factory(window), cheap_fp(window))
            values.append(result["payload_bpb"])
            development.append({
                "window": window,
                "file": name,
                "sample_bytes": len(sample),
                **result,
            })
            print("DEV", window, name, result["payload_bpb"], flush=True)
        print("DEV-MEAN", window, mean(values), flush=True)
    dev_means = {w: mean(r["payload_bpb"] for r in development if r["window"] == w) for w in DEV_WINDOWS}
    cheap_window = min(DEV_WINDOWS, key=lambda w: dev_means[w])

    # Calgary replication: cheap gate is newly evaluated; neural-gate numbers are frozen from PILOT-006.
    calzip = p4.download(p6.CAL_URL, OUT / "calgary.zip")
    cal = p4.unpack(calzip, p6.CAL)
    p6_calgary = {row["file"]: row for row in p6_results["calgary"]}
    calgary_rows = []
    for name, raw in cal.items():
        sample = raw[:SLICE]
        cheap = roundtrip(sample, cheap_factory(cheap_window), cheap_fp(cheap_window))
        neural = p6_calgary[name]
        base = baselines(sample)
        row = {
            "file": name,
            "category": p6.CAL[name][0],
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "cheap_pol1_bpb": cheap["pol1_bpb"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "cheap_choice_fractions": cheap["choice_fractions"],
            "neural_gate_payload_bpb": neural["gate_payload_bpb"],
            "neural_gate_pol1_bpb": neural["gate_pol1_bpb"],
            "neural_gate_encode_seconds": neural["gate_encode_seconds"],
            "neural_gate_decode_seconds": neural["gate_decode_seconds"],
            **base,
        }
        calgary_rows.append(row)
        print("CALGARY", name, cheap["payload_bpb"], neural["gate_payload_bpb"], base["zlib_bpb"], flush=True)

    # New holdout: six heterogeneous files from the official Silesia corpus.
    silesia_files, silesia_manifest = download_silesia()
    silesia_rows = []
    for name, raw in silesia_files.items():
        sample = raw[:SLICE]
        cheap = roundtrip(sample, cheap_factory(cheap_window), cheap_fp(cheap_window))
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        base = baselines(sample)
        row = {
            "file": name,
            "category": SILESIA[name][0],
            "file_bytes": len(raw),
            "sha256": sha(raw),
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "cheap_pol1_bpb": cheap["pol1_bpb"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "cheap_choice_fractions": cheap["choice_fractions"],
            "neural_gate_payload_bpb": neural["payload_bpb"],
            "neural_gate_pol1_bpb": neural["pol1_bpb"],
            "neural_gate_encode_seconds": neural["encode_seconds"],
            "neural_gate_decode_seconds": neural["decode_seconds"],
            "neural_choice_fractions": neural["choice_fractions"],
            **base,
        }
        silesia_rows.append(row)
        print("SILESIA", name, cheap["payload_bpb"], neural["payload_bpb"], base["zlib_bpb"], flush=True)

    # Regression controls: in-domain plus strong repetition/random mismatch.
    frozen_test = p6.frozen_test_split()[:SLICE]
    controls = []
    for name, category, sample in [
        ("self-v2-test", "training-domain-test", frozen_test),
        ("aaa.txt", "repetition", art["aaa.txt"][:SLICE]),
        ("random.txt", "random-64-symbol-alphabet", art["random.txt"][:SLICE]),
    ]:
        cheap = roundtrip(sample, cheap_factory(cheap_window), cheap_fp(cheap_window))
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        base = baselines(sample)
        controls.append({
            "file": name,
            "category": category,
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "neural_gate_payload_bpb": neural["payload_bpb"],
            "neural_gate_encode_seconds": neural["encode_seconds"],
            "neural_gate_decode_seconds": neural["decode_seconds"],
            **base,
        })

    def aggregate(rows: list[dict]) -> dict:
        cheap_bpb = mean(r["cheap_payload_bpb"] for r in rows)
        neural_bpb = mean(r["neural_gate_payload_bpb"] for r in rows)
        delta = cheap_bpb - neural_bpb
        return {
            "files": len(rows),
            "mean_cheap_payload_bpb": cheap_bpb,
            "mean_neural_gate_payload_bpb": neural_bpb,
            "mean_zlib_bpb": mean(r["zlib_bpb"] for r in rows),
            "mean_zstd19_bpb": mean(r["zstd19_bpb"] for r in rows),
            "cheap_beats_neural_files": sum(r["cheap_payload_bpb"] < r["neural_gate_payload_bpb"] for r in rows),
            "neural_beats_cheap_files": sum(r["neural_gate_payload_bpb"] < r["cheap_payload_bpb"] for r in rows),
            "cheap_beats_zlib_files": sum(r["cheap_payload_bpb"] < r["zlib_bpb"] for r in rows),
            "neural_beats_zlib_files": sum(r["neural_gate_payload_bpb"] < r["zlib_bpb"] for r in rows),
            "mean_cheap_encode_seconds": mean(r["cheap_encode_seconds"] for r in rows),
            "mean_cheap_decode_seconds": mean(r["cheap_decode_seconds"] for r in rows),
            "mean_neural_encode_seconds": mean(r["neural_gate_encode_seconds"] for r in rows),
            "mean_neural_decode_seconds": mean(r["neural_gate_decode_seconds"] for r in rows),
            "checkpoint_break_even_bytes_if_neural_better": (checkpoint_bytes * 8 / delta) if delta > 0 else None,
        }

    calgary_agg = aggregate(calgary_rows)
    silesia_agg = aggregate(silesia_rows)
    amortization = {
        str(bytes_total): checkpoint_bytes * 8 / bytes_total
        for bytes_total in (SLICE, 1 << 20, 100 << 20, 1 << 30)
    }

    results = {
        "experiment_id": "pilot-007-value-of-neural-expert",
        "base_commit": os.environ.get("GITHUB_SHA", "local"),
        "question": "Does the neural expert justify its model and compute cost versus a deterministic non-neural gate?",
        "cheap_gate": {
            "experts": list(CHEAP_NAMES),
            "candidate_windows": list(DEV_WINDOWS),
            "development_mean_payload_bpb": {str(k): v for k, v in dev_means.items()},
            "selected_window": cheap_window,
            "checkpoint_bytes": 0,
            "fingerprint": cheap_fp(cheap_window).hex(),
        },
        "neural_gate": {
            "experts": list(NEURAL_NAMES),
            "window": neural_window,
            "checkpoint_bytes": checkpoint_bytes,
            "canonical_neural_fingerprint": neural_fp.hex(),
            "fingerprint": neural_gate_fp.hex(),
        },
        "checkpoint_amortization_bpb": amortization,
        "calgary_replication": {"aggregate": calgary_agg, "rows": calgary_rows},
        "silesia_new_holdout": {"aggregate": silesia_agg, "rows": silesia_rows, "manifest": silesia_manifest},
        "controls": controls,
        "source_archives": {
            "canterbury_sha256": sha(canzip),
            "artificial_sha256": sha(artzip),
            "calgary_sha256": sha(calzip),
        },
        "protocol": {
            "precision_bits": PRECISION,
            "slice_bytes": SLICE,
            "selector_side_bits": 0,
            "cheap_gate_tuned_only_on": "Canterbury + Artificial development slices",
            "calgary_role": "replication of PILOT-006 comparison; not used for tuning PILOT-007",
            "silesia_role": "new external holdout; not used for tuning",
            "pareto_metrics": ["payload_bpb", "pol1_bpb", "checkpoint_bytes", "encode_seconds", "decode_seconds"],
        },
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (OUT / "silesia-manifest.json").write_text(json.dumps(silesia_manifest, indent=2) + "\n")
    csvout(OUT / "development.csv", development)
    csvout(OUT / "calgary.csv", calgary_rows)
    csvout(OUT / "silesia.csv", silesia_rows)
    csvout(OUT / "controls.csv", controls)
    print(json.dumps({"calgary": calgary_agg, "silesia": silesia_agg, "amortization": amortization}, indent=2))


if __name__ == "__main__":
    main()
