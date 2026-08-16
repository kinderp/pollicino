from __future__ import annotations

import bz2
import csv
import hashlib
import importlib.util
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
from pollicino.compression.bit_credit_routing import (
    BitCreditSpecialistRouterCDFProvider,
    bit_credit_router_fingerprint,
)
from pollicino.compression.classical_experts import RunLengthCDFProvider, run_length_fingerprint
from pollicino.compression.codec import decode_pol, encode_shared, inspect_pol
from pollicino.compression.gating import DeterministicExpertGateCDFProvider, expert_gate_fingerprint
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint
from pollicino.compression.sequential_routing import (
    SequentialSpecialistRouterCDFProvider,
    sequential_router_fingerprint,
)

PRECISION = 18
TRACE_BYTES = 256
HOLDOUT_SLICE = 4096
MIN_OBSERVATIONS = (4, 8, 16)
MAX_PROBES = (16, 32, 64, 128, 256)
ACTIVATION_BITS = (0, 2, 4, 6, 8, 10, 12)
REJECTION_BITS = (2, 4, 6, 8, 10, 12, 16)
MODE_BUDGETS = {"max": 1.0, "balanced": 0.50, "fast": 0.20}

CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)

REAL_BASE = "https://pizzachili.dcc.uchile.cl/repcorpus/real"
REAL_HOLDOUT = {
    "cere": "yeast-dna",
    "para": "yeast-dna",
    "influenza": "dna-sequences",
    "coreutils": "source-code-versions",
    "kernel": "linux-kernel-source-versions",
    "world_leaders": "documents-text",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def cdf_term(cdf, symbol: int) -> tuple[int, int]:
    return int(cdf[symbol + 1]) - int(cdf[symbol]), int(cdf[-1])


def ratio_gt(sn: int, sd: int, cn: int, cd: int, bits: int) -> bool:
    return sn * cd > cn * sd * (1 << bits)


def ratio_lt(sn: int, sd: int, cn: int, cd: int, bits: int) -> bool:
    return sn * cd * (1 << bits) < cn * sd


def simulate_policy(trace: list[tuple[int, int, int, int]], stream_bytes: int, policy: dict) -> tuple[str, int, float]:
    cn = cd = sn = sd = 1
    cap = min(policy["max_probe_bytes"], stream_bytes, len(trace))
    for seen, (tcn, tcd, tsn, tsd) in enumerate(trace[:cap], start=1):
        cn *= tcn
        cd *= tcd
        sn *= tsn
        sd *= tsd
        if seen < policy["min_observations"]:
            continue
        if ratio_gt(sn, sd, cn, cd, policy["activation_credit_bits"]):
            return "neural-gate", seen, 1.0
        if ratio_lt(sn, sd, cn, cd, policy["rejection_credit_bits"]):
            return "cheap-gate", seen, seen / stream_bytes
        if seen >= policy["max_probe_bytes"]:
            return "cheap-gate", seen, seen / stream_bytes
    return "cheap-gate", cap, cap / stream_bytes if stream_bytes else 0.0


def baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def extract_real_collection(name: str, category: str) -> tuple[bytes, dict]:
    filename = f"{name}.7z"
    url = f"{REAL_BASE}/{filename}"
    request = urllib.request.Request(url, headers={"User-Agent": "POLLICINO-PILOT-011/1.0"})
    archive = urllib.request.urlopen(request, timeout=240).read()
    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        archive_path = td / filename
        archive_path.write_bytes(archive)
        extracted = td / "extracted"
        extracted.mkdir()
        with py7zr.SevenZipFile(archive_path, mode="r") as seven:
            seven.extractall(path=extracted)
        files = [path for path in extracted.rglob("*") if path.is_file()]
        if not files:
            raise RuntimeError(f"{filename}: archive contained no files")
        source = max(files, key=lambda path: path.stat().st_size)
        full_size = source.stat().st_size
        full_sha = hashlib.sha256()
        with source.open("rb") as handle:
            sample = handle.read(HOLDOUT_SLICE)
            full_sha.update(sample)
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                full_sha.update(chunk)
    if len(sample) != HOLDOUT_SLICE:
        raise RuntimeError(f"{filename}: extracted file is shorter than reporting slice")
    return sample, {
        "file": name,
        "category": category,
        "archive_name": filename,
        "source_url": url,
        "archive_bytes": len(archive),
        "archive_sha256": sha256(archive),
        "full_bytes": full_size,
        "full_sha256": full_sha.hexdigest(),
        "sample_bytes": len(sample),
        "sample_sha256": sha256(sample),
    }


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004_for_p11")
    p6 = load_module(ROOT / "experiments/pilot-006/run.py", "pilot006_for_p11")
    p7 = load_module(ROOT / "experiments/pilot-007/run.py", "pilot007_for_p11")
    p8 = load_module(ROOT / "experiments/pilot-008/run.py", "pilot008_for_p11")
    p9 = load_module(ROOT / "experiments/pilot-009/run.py", "pilot009_for_p11")
    p9exact = load_module(ROOT / "experiments/pilot-009/exact_checkpoint.py", "pilot009_exact_for_p11")
    p10 = load_module(ROOT / "experiments/pilot-010/run.py", "pilot010_for_p11")

    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
    p9_results = json.loads((ROOT / "experiments/pilot-009/results.json").read_text())

    model, spec, checkpoint = p9exact.load_exact_checkpoint()
    neural_fp = torch_model_fingerprint(model, spec)
    expected_fp = p9_results["model"]["canonical_neural_fingerprint"]
    if neural_fp.hex() != expected_fp:
        raise RuntimeError("exact PILOT-003 checkpoint fingerprint did not reproduce")

    adaptive_cfgs = {
        "adaptive-o0": dict(max_order=0, order_weights=(1,), base_count=1),
        "adaptive-o1": dict(max_order=1, order_weights=(1, 4), base_count=1),
        "adaptive-o2": dict(max_order=2, order_weights=(1, 4, 16), base_count=1),
        "adaptive-o3": ADAPTIVE_CFG,
    }
    cheap_window = int(p7_results["cheap_gate"]["selected_window"])
    cheap_fps = [adaptive_fingerprint(**adaptive_cfgs[name]) for name in CHEAP_NAMES[:-1]] + [
        run_length_fingerprint(run_weight=64)
    ]
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

    def trace_evidence(data: bytes) -> list[tuple[int, int, int, int]]:
        cheap = cheap_factory()
        neural = neural_factory()
        prefix: list[int] = []
        trace = []
        for index, symbol in enumerate(data[:TRACE_BYTES]):
            ccdf = cheap(index, prefix)
            ncdf = neural(index, prefix)
            cn, cd = cdf_term(ccdf, symbol)
            nn, nd = cdf_term(ncdf, symbol)
            trace.append((cn, cd, nn, nd))
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
        if hasattr(encoder, "selected_route"):
            assert encoder.selected_route == decoder.selected_route
        if hasattr(encoder, "decision_byte"):
            assert encoder.decision_byte == decoder.decision_byte
        info = inspect_pol(blob)
        row = {
            "payload_bpb": info["payload_bpb"],
            "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc,
            "decode_seconds": dec,
        }
        for attr in ("selected_route", "decision_byte", "probe_count", "specialist_calls", "compute_fraction"):
            if hasattr(encoder, attr):
                row[attr] = getattr(encoder, attr)
        return row

    # ------------------------------------------------------------------
    # Development: all 20 benchmark streams already consumed by PILOT-007..010.
    # ------------------------------------------------------------------
    dev: list[dict] = []

    silesia_files, _ = p7.download_silesia()
    for row in read_csv(ROOT / "experiments/pilot-007/silesia.csv"):
        name = row["file"]
        stream_bytes = int(row["sample_bytes"])
        dev.append({
            "file": name,
            "source": "pilot-007-silesia",
            "category": row["category"],
            "stream_bytes": stream_bytes,
            "sample": silesia_files[name][:stream_bytes],
            "cheap_bpb": float(row["cheap_payload_bpb"]),
            "neural_bpb": float(row["neural_gate_payload_bpb"]),
        })

    largezip = p4.download(p8.LARGE_URL, OUT / "large-dev.zip")
    large = p4.unpack(largezip, p8.LARGE)
    for row in read_csv(ROOT / "experiments/pilot-008/large.csv"):
        name = row["file"]
        stream_bytes = int(row["sample_bytes"])
        dev.append({
            "file": name,
            "source": "pilot-008-large",
            "category": row["category"],
            "stream_bytes": stream_bytes,
            "sample": large[name][:stream_bytes],
            "cheap_bpb": float(row["cheap_payload_bpb"]),
            "neural_bpb": float(row["neural_payload_bpb"]),
        })

    p9_rows = {row["file"]: row for row in read_csv(ROOT / "experiments/pilot-009/holdout.csv")}
    for name, (category, filename) in p9.PSEUDO_REAL.items():
        sample, _manifest = p9.extract_pseudo_real(name, category, filename)
        row = p9_rows[name]
        dev.append({
            "file": name,
            "source": "pilot-009-pseudo-real",
            "category": category,
            "stream_bytes": len(sample),
            "sample": sample,
            "cheap_bpb": float(row["cheap_payload_bpb"]),
            "neural_bpb": float(row["neural_payload_bpb"]),
        })

    p10_rows = {row["file"]: row for row in read_csv(ROOT / "experiments/pilot-010/holdout.csv")}
    for name, (category, expected_size, expected_md5) in p10.UNUSED_SILESIA.items():
        url = f"{p10.SILESIA_BASE}/{name}.bz2"
        request = urllib.request.Request(url, headers={"User-Agent": "POLLICINO-PILOT-011/1.0"})
        compressed = urllib.request.urlopen(request, timeout=180).read()
        raw = bz2.decompress(compressed)
        if len(raw) != expected_size or p10.md5(raw) != expected_md5:
            raise RuntimeError(f"development Silesia provenance mismatch: {name}")
        row = p10_rows[name]
        stream_bytes = int(row["sample_bytes"])
        dev.append({
            "file": name,
            "source": "pilot-010-silesia",
            "category": category,
            "stream_bytes": stream_bytes,
            "sample": raw[:stream_bytes],
            "cheap_bpb": float(row["cheap_payload_bpb"]),
            "neural_bpb": float(row["neural_payload_bpb"]),
        })

    if len(dev) != 20:
        raise RuntimeError(f"expected 20 development streams, got {len(dev)}")

    for item in dev:
        item["trace"] = trace_evidence(item["sample"])
        item["oracle_bpb"] = min(item["cheap_bpb"], item["neural_bpb"])
        print("DEV-TRACE", item["file"], item["cheap_bpb"] - item["neural_bpb"], flush=True)

    candidate_rows = []
    for min_obs in MIN_OBSERVATIONS:
        for max_probe in MAX_PROBES:
            if max_probe < min_obs:
                continue
            for activation in ACTIVATION_BITS:
                for rejection in REJECTION_BITS:
                    policy = {
                        "min_observations": min_obs,
                        "max_probe_bytes": max_probe,
                        "activation_credit_bits": activation,
                        "rejection_credit_bits": rejection,
                    }
                    regrets = []
                    compute = []
                    decisions = []
                    for item in dev:
                        route, byte, fraction = simulate_policy(item["trace"], item["stream_bytes"], policy)
                        selected_bpb = item["neural_bpb"] if route == "neural-gate" else item["cheap_bpb"]
                        regrets.append(selected_bpb - item["oracle_bpb"])
                        compute.append(fraction)
                        decisions.append(byte)
                    candidate_rows.append({
                        **policy,
                        "mean_oracle_regret_bpb": mean(regrets),
                        "max_oracle_regret_bpb": max(regrets),
                        "mean_specialist_call_fraction": mean(compute),
                        "mean_decision_byte": mean(decisions),
                    })

    def select_mode(name: str, budget: float) -> dict:
        eligible = [row for row in candidate_rows if row["mean_specialist_call_fraction"] <= budget + 1e-12]
        if not eligible:
            raise RuntimeError(f"no policy satisfies {name} compute budget")
        chosen = min(
            eligible,
            key=lambda row: (
                row["mean_oracle_regret_bpb"],
                row["max_oracle_regret_bpb"],
                row["mean_specialist_call_fraction"],
                row["mean_decision_byte"],
                row["max_probe_bytes"],
                row["activation_credit_bits"],
                row["rejection_credit_bits"],
            ),
        )
        return {key: chosen[key] for key in (
            "min_observations",
            "max_probe_bytes",
            "activation_credit_bits",
            "rejection_credit_bits",
            "mean_oracle_regret_bpb",
            "max_oracle_regret_bpb",
            "mean_specialist_call_fraction",
            "mean_decision_byte",
        )}

    modes = {name: select_mode(name, budget) for name, budget in MODE_BUDGETS.items()}
    print("MODES", json.dumps(modes, sort_keys=True), flush=True)

    pareto = []
    for row in candidate_rows:
        dominated = any(
            other is not row
            and other["mean_oracle_regret_bpb"] <= row["mean_oracle_regret_bpb"]
            and other["mean_specialist_call_fraction"] <= row["mean_specialist_call_fraction"]
            and (
                other["mean_oracle_regret_bpb"] < row["mean_oracle_regret_bpb"]
                or other["mean_specialist_call_fraction"] < row["mean_specialist_call_fraction"]
            )
            for other in candidate_rows
        )
        if not dominated:
            pareto.append(row)
    pareto.sort(key=lambda row: (row["mean_specialist_call_fraction"], row["mean_oracle_regret_bpb"]))

    development_routes = []
    for item in dev:
        for mode, policy in modes.items():
            route, byte, fraction = simulate_policy(item["trace"], item["stream_bytes"], policy)
            selected = item["neural_bpb"] if route == "neural-gate" else item["cheap_bpb"]
            development_routes.append({
                "file": item["file"],
                "source": item["source"],
                "category": item["category"],
                "mode": mode,
                "cheap_bpb": item["cheap_bpb"],
                "neural_bpb": item["neural_bpb"],
                "oracle_bpb": item["oracle_bpb"],
                "selected_route": route,
                "decision_byte": byte,
                "specialist_call_fraction": fraction,
                "oracle_regret_bpb": selected - item["oracle_bpb"],
            })

    p9_policy = p9_results["development"]["selected_policy"]

    def p9_factory(stream_bytes: int):
        def factory():
            return SequentialSpecialistRouterCDFProvider(
                cheap_factory(),
                neural_factory(),
                stream_bytes=stream_bytes,
                min_stream_bytes=0,
                min_observations=int(p9_policy["min_observations"]),
                max_probe_bytes=int(p9_policy["max_probe_bytes"]),
                activate_ratio_num=int(p9_policy["activate_ratio"]),
                activate_ratio_den=1,
                reject_ratio_num=1,
                reject_ratio_den=int(p9_policy["reject_ratio_den"]),
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
        return factory

    def p9_fp(stream_bytes: int) -> bytes:
        return sequential_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp,
            stream_bytes=stream_bytes,
            min_stream_bytes=0,
            min_observations=int(p9_policy["min_observations"]),
            max_probe_bytes=int(p9_policy["max_probe_bytes"]),
            activate_ratio_num=int(p9_policy["activate_ratio"]),
            activate_ratio_den=1,
            reject_ratio_num=1,
            reject_ratio_den=int(p9_policy["reject_ratio_den"]),
        )

    def mode_factory(mode: str, stream_bytes: int):
        policy = modes[mode]
        def factory():
            return BitCreditSpecialistRouterCDFProvider(
                cheap_factory(),
                neural_factory(),
                stream_bytes=stream_bytes,
                min_stream_bytes=0,
                min_observations=int(policy["min_observations"]),
                max_probe_bytes=int(policy["max_probe_bytes"]),
                activation_credit_bits=int(policy["activation_credit_bits"]),
                rejection_credit_bits=int(policy["rejection_credit_bits"]),
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
        return factory

    def mode_fp(mode: str, stream_bytes: int) -> bytes:
        policy = modes[mode]
        return bit_credit_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp,
            stream_bytes=stream_bytes,
            min_stream_bytes=0,
            min_observations=int(policy["min_observations"]),
            max_probe_bytes=int(policy["max_probe_bytes"]),
            activation_credit_bits=int(policy["activation_credit_bits"]),
            rejection_credit_bits=int(policy["rejection_credit_bits"]),
        )

    # ------------------------------------------------------------------
    # New holdout: official Pizza&Chili real repetitive corpus subset.
    # ------------------------------------------------------------------
    holdout_rows = []
    holdout_manifest = []
    for name, category in REAL_HOLDOUT.items():
        sample, manifest = extract_real_collection(name, category)
        holdout_manifest.append(manifest)
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        p9row = roundtrip(sample, p9_factory(len(sample)), p9_fp(len(sample)))
        mode_rows = {
            mode: roundtrip(sample, mode_factory(mode, len(sample)), mode_fp(mode, len(sample)))
            for mode in modes
        }
        oracle = min(cheap["payload_bpb"], neural["payload_bpb"])
        row = {
            "file": name,
            "category": category,
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "oracle_payload_bpb": oracle,
            "p9_payload_bpb": p9row["payload_bpb"],
            "p9_oracle_regret_bpb": p9row["payload_bpb"] - oracle,
            "p9_route": p9row["selected_route"],
            "p9_decision_byte": p9row["decision_byte"],
            "p9_specialist_calls": p9row["specialist_calls"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "neural_encode_seconds": neural["encode_seconds"],
            "p9_encode_seconds": p9row["encode_seconds"],
            **baselines(sample),
        }
        for mode, result in mode_rows.items():
            row[f"{mode}_payload_bpb"] = result["payload_bpb"]
            row[f"{mode}_pol1_bpb"] = result["pol1_bpb"]
            row[f"{mode}_oracle_regret_bpb"] = result["payload_bpb"] - oracle
            row[f"{mode}_route"] = result["selected_route"]
            row[f"{mode}_decision_byte"] = result["decision_byte"]
            row[f"{mode}_specialist_calls"] = result["specialist_calls"]
            row[f"{mode}_compute_fraction"] = result["compute_fraction"]
            row[f"{mode}_encode_seconds"] = result["encode_seconds"]
            row[f"{mode}_decode_seconds"] = result["decode_seconds"]
        holdout_rows.append(row)
        print("HOLDOUT", name, oracle, {m: mode_rows[m]["payload_bpb"] for m in modes}, flush=True)

    holdout_aggregate = {
        "files": len(holdout_rows),
        "mean_oracle_bpb": mean(row["oracle_payload_bpb"] for row in holdout_rows),
        "mean_cheap_bpb": mean(row["cheap_payload_bpb"] for row in holdout_rows),
        "mean_neural_bpb": mean(row["neural_payload_bpb"] for row in holdout_rows),
        "mean_p9_bpb": mean(row["p9_payload_bpb"] for row in holdout_rows),
        "mean_p9_regret_bpb": mean(row["p9_oracle_regret_bpb"] for row in holdout_rows),
        "max_p9_regret_bpb": max(row["p9_oracle_regret_bpb"] for row in holdout_rows),
        "mean_zlib_bpb": mean(row["zlib_bpb"] for row in holdout_rows),
        "mean_zstd19_bpb": mean(row["zstd19_bpb"] for row in holdout_rows),
    }
    for mode in modes:
        holdout_aggregate[f"mean_{mode}_bpb"] = mean(row[f"{mode}_payload_bpb"] for row in holdout_rows)
        holdout_aggregate[f"mean_{mode}_regret_bpb"] = mean(row[f"{mode}_oracle_regret_bpb"] for row in holdout_rows)
        holdout_aggregate[f"max_{mode}_regret_bpb"] = max(row[f"{mode}_oracle_regret_bpb"] for row in holdout_rows)
        holdout_aggregate[f"mean_{mode}_compute_fraction"] = mean(row[f"{mode}_compute_fraction"] for row in holdout_rows)
        holdout_aggregate[f"mean_{mode}_encode_seconds"] = mean(row[f"{mode}_encode_seconds"] for row in holdout_rows)

    # Regression controls are not tuning data.
    p4_art = p4.download(p4.ART_URL, OUT / "artificl.zip")
    art = p4.unpack(p4_art, p4.ART)
    controls = []
    for name, category, sample in (
        ("self-v2-test", "training-domain-test", p6.frozen_test_split()[:HOLDOUT_SLICE]),
        ("aaa.txt", "repetition", art["aaa.txt"][:HOLDOUT_SLICE]),
        ("random.txt", "random-64-symbol-alphabet", art["random.txt"][:HOLDOUT_SLICE]),
    ):
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        oracle = min(cheap["payload_bpb"], neural["payload_bpb"])
        control = {
            "file": name,
            "category": category,
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "oracle_payload_bpb": oracle,
        }
        for mode in modes:
            result = roundtrip(sample, mode_factory(mode, len(sample)), mode_fp(mode, len(sample)))
            control[f"{mode}_payload_bpb"] = result["payload_bpb"]
            control[f"{mode}_route"] = result["selected_route"]
            control[f"{mode}_decision_byte"] = result["decision_byte"]
            control[f"{mode}_compute_fraction"] = result["compute_fraction"]
        controls.append(control)

    results = {
        "experiment_id": "pilot-011-regret-aware-bit-credit-routing",
        "question": "Does direct oracle-regret minimization under explicit deterministic neural-compute budgets outperform equal-cost route classification?",
        "development": {
            "files": 20,
            "sources": ["PILOT-007 Silesia", "PILOT-008 Large", "PILOT-009 pseudo-real", "PILOT-010 Silesia"],
            "trace_bytes": TRACE_BYTES,
            "candidate_grid": {
                "min_observations": list(MIN_OBSERVATIONS),
                "max_probe_bytes": list(MAX_PROBES),
                "activation_credit_bits": list(ACTIVATION_BITS),
                "rejection_credit_bits": list(REJECTION_BITS),
            },
            "mode_budgets": MODE_BUDGETS,
            "selected_modes": modes,
            "pareto_points": len(pareto),
        },
        "new_holdout": {
            "name": "Pizza&Chili real repetitive corpus fixed six-collection subset",
            "files": list(REAL_HOLDOUT),
            "sample_bytes_per_file": HOLDOUT_SLICE,
            "aggregate": holdout_aggregate,
            "per_file_table": "holdout.csv",
            "manifest": "holdout-manifest.json",
        },
        "controls": controls,
        "model": {
            "canonical_neural_fingerprint": neural_fp.hex(),
            "cheap_gate_fingerprint": cheap_fp.hex(),
            "neural_gate_fingerprint": neural_gate_fp.hex(),
        },
        "frozen_checkpoint": {
            "source_experiment": "PILOT-003",
            **checkpoint,
            "canonical_model_fingerprint": neural_fp.hex(),
        },
        "protocol": {
            "precision_bits": PRECISION,
            "selector_side_bits": 0,
            "routing_arithmetic": "integer CDF likelihood products; powers-of-two credit thresholds",
            "policy_objective": "oracle regret under hard mean specialist-call-fraction budgets",
            "holdout_not_used_for_tuning": True,
            "wall_clock_not_used_in_routing_or_policy_selection": True,
            "block_routing_deferred": True,
        },
        "run": {
            "github_actions_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
            "head_sha": os.environ.get("GITHUB_SHA", "local"),
        },
        "limits": [
            "Only the first 4096 bytes of each very large real collection are entropy-coded in this pilot.",
            "The Pizza&Chili real corpus is repetitive by construction and is not a universal real-world benchmark.",
            "The neural checkpoint is assumed shared whenever a neural route is available.",
            "Compute budgets use deterministic specialist-call fraction rather than hardware-dependent wall-clock time.",
            "PILOT-011 retains a single irreversible file-level route; block-local switching is not tested here.",
        ],
    }

    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    csvout(OUT / "candidate-policies.csv", candidate_rows)
    csvout(OUT / "pareto.csv", pareto)
    csvout(OUT / "development-routes.csv", development_routes)
    csvout(OUT / "holdout.csv", holdout_rows)
    csvout(OUT / "controls.csv", controls)
    (OUT / "holdout-manifest.json").write_text(json.dumps(holdout_manifest, indent=2) + "\n")
    print(json.dumps({"modes": modes, "holdout": holdout_aggregate, "controls": controls}, indent=2))


if __name__ == "__main__":
    main()
