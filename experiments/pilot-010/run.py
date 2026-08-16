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
from collections import deque
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
from pollicino.compression.sequential_routing import (
    SequentialSpecialistRouterCDFProvider,
    sequential_router_fingerprint,
)
from pollicino.compression.stability_routing import (
    StabilityValueSpecialistRouterCDFProvider,
    stability_value_router_fingerprint,
)

PRECISION = 18
MEANINGFUL_GAIN_BPB = 0.05
DEV_TRACE_BYTES = 128
HOLDOUT_SLICE = 4096
MIN_OBSERVATIONS = 8
ACTIVATE_RATIO = 256
REJECT_RATIO_DEN = 256
RECENT_WINDOWS = (4, 8, 16, 32)
PERSISTENCE = (2, 4, 8)
RECENT_GAIN_BITS = (1, 2, 3, 4)
MIN_PROJECTED_GAIN_BITS = (0, 32, 64, 128, 256)
MAX_PROBES = (64, 96, 128)

CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)

SILESIA_BASE = "https://sun.aei.polsl.pl/~sdeor/corpus"
UNUSED_SILESIA = {
    "mozilla": ("mixed-executables-tar", 51_220_480, "c7789a2097f1ff944b0c737430a339b3"),
    "mr": ("medical-mri-dicom", 9_970_564, "38e623e3093b7bf2003ca4b1bbc19927"),
    "nci": ("chemical-database-sdf", 33_553_445, "31f85bc8706f3c921104e7c169e2e2e1"),
    "samba": ("source-project-tar", 21_606_400, "154eaea7ea70e89f6339ff0abf4112ca"),
    "sao": ("astronomical-binary-database", 7_251_944, "79e95a22e18cd82b7e42bf91b380d30b"),
    "webster": ("english-dictionary-html", 41_458_703, "474931ad907ac27bf962c75ded46c069"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


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


def baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def cdf_term(cdf, symbol: int) -> tuple[int, int]:
    return int(cdf[symbol + 1]) - int(cdf[symbol]), int(cdf[-1])


def ratio_gt(sn: int, sd: int, cn: int, cd: int, num: int, den: int = 1) -> bool:
    return sn * cd * den > cn * sd * num


def ratio_lt(sn: int, sd: int, cn: int, cd: int, num: int, den: int) -> bool:
    return sn * cd * den < cn * sd * num


def projected_gain_bits(stream_bytes: int, seen: int, recent_window: int, recent_gain_bits: int) -> int:
    return (max(0, stream_bytes - seen) // recent_window) * recent_gain_bits


def simulate_policy(trace: list[tuple[int, int, int, int]], stream_bytes: int, policy: dict) -> tuple[str, int, str]:
    if projected_gain_bits(
        stream_bytes,
        MIN_OBSERVATIONS,
        policy["recent_window"],
        policy["recent_gain_bits"],
    ) < policy["min_projected_gain_bits"]:
        return "cheap-gate", 0, "ineligible"

    cn = cd = sn = sd = 1
    recent: deque[tuple[int, int, int, int]] = deque(maxlen=policy["recent_window"])
    streak = 0
    for seen, term in enumerate(trace[: policy["max_probe_bytes"]], start=1):
        tcn, tcd, tsn, tsd = term
        cn *= tcn
        cd *= tcd
        sn *= tsn
        sd *= tsd
        recent.append(term)
        if seen < MIN_OBSERVATIONS:
            continue
        if ratio_lt(sn, sd, cn, cd, 1, REJECT_RATIO_DEN):
            return "cheap-gate", seen, "cumulative-reject"

        candidate = False
        if ratio_gt(sn, sd, cn, cd, ACTIVATE_RATIO):
            if len(recent) == policy["recent_window"]:
                rcn = rcd = rsn = rsd = 1
                for xcn, xcd, xsn, xsd in recent:
                    rcn *= xcn
                    rcd *= xcd
                    rsn *= xsn
                    rsd *= xsd
                recent_ok = ratio_gt(
                    rsn,
                    rsd,
                    rcn,
                    rcd,
                    1 << policy["recent_gain_bits"],
                )
                value_ok = projected_gain_bits(
                    stream_bytes,
                    seen,
                    policy["recent_window"],
                    policy["recent_gain_bits"],
                ) >= policy["min_projected_gain_bits"]
                candidate = recent_ok and value_ok
        streak = streak + 1 if candidate else 0
        if streak >= policy["persistence_observations"]:
            return "neural-gate", seen, "stable-value-activate"

        if projected_gain_bits(
            stream_bytes,
            seen,
            policy["recent_window"],
            policy["recent_gain_bits"],
        ) < policy["min_projected_gain_bits"]:
            return "cheap-gate", seen, "value-exhausted"
        if seen >= policy["max_probe_bytes"]:
            return "cheap-gate", seen, "probe-cap"
    return "cheap-gate", min(len(trace), policy["max_probe_bytes"]), "trace-end"


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004_for_p10")
    p6 = load_module(ROOT / "experiments/pilot-006/run.py", "pilot006_for_p10")
    p7 = load_module(ROOT / "experiments/pilot-007/run.py", "pilot007_for_p10")
    p8 = load_module(ROOT / "experiments/pilot-008/run.py", "pilot008_for_p10")
    p9 = load_module(ROOT / "experiments/pilot-009/run.py", "pilot009_for_p10")
    p9exact = load_module(ROOT / "experiments/pilot-009/exact_checkpoint.py", "pilot009_exact_for_p10")

    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
    p9_results = json.loads((ROOT / "experiments/pilot-009/results.json").read_text())

    model, spec, checkpoint = p9exact.load_exact_checkpoint()
    neural_fp = torch_model_fingerprint(model, spec)
    expected_neural_fp = p9_results["model"]["canonical_neural_fingerprint"]
    if neural_fp.hex() != expected_neural_fp:
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

    def trace_evidence(data: bytes, limit: int = DEV_TRACE_BYTES) -> list[tuple[int, int, int, int]]:
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
        if hasattr(encoder, "selected_route"):
            assert encoder.selected_route == decoder.selected_route
        if hasattr(encoder, "decision_byte"):
            assert encoder.decision_byte == decoder.decision_byte
        if hasattr(encoder, "decision_reason"):
            assert encoder.decision_reason == decoder.decision_reason
        if hasattr(encoder, "choice_counts"):
            assert encoder.choice_counts == decoder.choice_counts
        info = inspect_pol(blob)
        result = {
            "payload_bpb": info["payload_bpb"],
            "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc,
            "decode_seconds": dec,
        }
        for attr in (
            "selected_route",
            "decision_byte",
            "decision_reason",
            "probe_count",
            "specialist_calls",
            "activation_candidate_count",
            "max_candidate_streak",
        ):
            if hasattr(encoder, attr):
                result[attr] = getattr(encoder, attr)
        return result

    # ------------------------------------------------------------------
    # Development: only already-consumed files from PILOT-007/008/009.
    # ------------------------------------------------------------------
    dev: list[dict] = []

    silesia_files, _ = p7.download_silesia()
    for row in read_csv(ROOT / "experiments/pilot-007/silesia.csv"):
        name = row["file"]
        sample_bytes = int(row["sample_bytes"])
        cheap_bpb = float(row["cheap_payload_bpb"])
        neural_bpb = float(row["neural_gate_payload_bpb"])
        dev.append({
            "file": name,
            "source": "pilot-007-silesia",
            "category": row["category"],
            "stream_bytes": sample_bytes,
            "sample": silesia_files[name][:sample_bytes],
            "cheap_bpb": cheap_bpb,
            "neural_bpb": neural_bpb,
            "target": "neural-gate" if cheap_bpb - neural_bpb >= MEANINGFUL_GAIN_BPB else "cheap-gate",
        })

    largezip = p4.download(p8.LARGE_URL, OUT / "large-dev.zip")
    large = p4.unpack(largezip, p8.LARGE)
    for row in read_csv(ROOT / "experiments/pilot-008/large.csv"):
        name = row["file"]
        sample_bytes = int(row["sample_bytes"])
        cheap_bpb = float(row["cheap_payload_bpb"])
        neural_bpb = float(row["neural_payload_bpb"])
        dev.append({
            "file": name,
            "source": "pilot-008-large",
            "category": row["category"],
            "stream_bytes": sample_bytes,
            "sample": large[name][:sample_bytes],
            "cheap_bpb": cheap_bpb,
            "neural_bpb": neural_bpb,
            "target": "neural-gate" if cheap_bpb - neural_bpb >= MEANINGFUL_GAIN_BPB else "cheap-gate",
        })

    p9_holdout = {row["file"]: row for row in read_csv(ROOT / "experiments/pilot-009/holdout.csv")}
    for name, (category, filename) in p9.PSEUDO_REAL.items():
        sample, _manifest = p9.extract_pseudo_real(name, category, filename)
        row = p9_holdout[name]
        cheap_bpb = float(row["cheap_payload_bpb"])
        neural_bpb = float(row["neural_payload_bpb"])
        dev.append({
            "file": name,
            "source": "pilot-009-pseudo-real",
            "category": category,
            "stream_bytes": len(sample),
            "sample": sample,
            "cheap_bpb": cheap_bpb,
            "neural_bpb": neural_bpb,
            "target": "neural-gate" if cheap_bpb - neural_bpb >= MEANINGFUL_GAIN_BPB else "cheap-gate",
        })

    if len(dev) != 14:
        raise RuntimeError(f"expected 14 development files, got {len(dev)}")

    for item in dev:
        item["trace"] = trace_evidence(item["sample"], DEV_TRACE_BYTES)
        print("DEV-TRACE", item["file"], item["target"], flush=True)

    candidate_rows = []
    for max_probe in MAX_PROBES:
        for recent_window in RECENT_WINDOWS:
            for persistence in PERSISTENCE:
                for recent_gain_bits in RECENT_GAIN_BITS:
                    for min_projected in MIN_PROJECTED_GAIN_BITS:
                        policy = {
                            "max_probe_bytes": max_probe,
                            "recent_window": recent_window,
                            "persistence_observations": persistence,
                            "recent_gain_bits": recent_gain_bits,
                            "min_projected_gain_bits": min_projected,
                        }
                        decisions = []
                        for item in dev:
                            route, byte, reason = simulate_policy(item["trace"], item["stream_bytes"], policy)
                            decisions.append((item, route, byte, reason))
                        correct = sum(route == item["target"] for item, route, _byte, _reason in decisions)
                        false_positive = sum(
                            route == "neural-gate" and item["target"] == "cheap-gate"
                            for item, route, _byte, _reason in decisions
                        )
                        false_negative = sum(
                            route == "cheap-gate" and item["target"] == "neural-gate"
                            for item, route, _byte, _reason in decisions
                        )
                        regret = []
                        for item, route, _byte, _reason in decisions:
                            selected = item["neural_bpb"] if route == "neural-gate" else item["cheap_bpb"]
                            regret.append(selected - min(item["cheap_bpb"], item["neural_bpb"]))
                        candidate_rows.append({
                            **policy,
                            "correct": correct,
                            "false_positive": false_positive,
                            "false_negative": false_negative,
                            "mean_decision_byte": mean(byte for _item, _route, byte, _reason in decisions),
                            "mean_oracle_regret_bpb": mean(regret),
                        })

    # Predeclared ranking: classification first, then false-positive compute risk,
    # then compression regret and decision latency.
    selected = min(
        candidate_rows,
        key=lambda r: (
            -r["correct"],
            r["false_positive"],
            r["false_negative"],
            r["mean_oracle_regret_bpb"],
            r["mean_decision_byte"],
            r["max_probe_bytes"],
            r["recent_window"],
            r["persistence_observations"],
            r["recent_gain_bits"],
            r["min_projected_gain_bits"],
        ),
    )
    policy = {key: int(selected[key]) for key in (
        "max_probe_bytes",
        "recent_window",
        "persistence_observations",
        "recent_gain_bits",
        "min_projected_gain_bits",
    )}
    print("SELECTED", json.dumps(policy, sort_keys=True), flush=True)

    dev_routes = []
    for item in dev:
        route, byte, reason = simulate_policy(item["trace"], item["stream_bytes"], policy)
        dev_routes.append({
            "file": item["file"],
            "source": item["source"],
            "category": item["category"],
            "cheap_bpb": item["cheap_bpb"],
            "neural_bpb": item["neural_bpb"],
            "neural_gain_bpb": item["cheap_bpb"] - item["neural_bpb"],
            "target": item["target"],
            "route": route,
            "decision_byte": byte,
            "decision_reason": reason,
            "correct": route == item["target"],
        })

    def stability_factory(stream_bytes: int, *, specialist_available: bool = True):
        def factory():
            return StabilityValueSpecialistRouterCDFProvider(
                cheap_factory(),
                neural_factory() if specialist_available else None,
                stream_bytes=stream_bytes,
                min_stream_bytes=0,
                min_observations=MIN_OBSERVATIONS,
                max_probe_bytes=policy["max_probe_bytes"],
                activate_ratio_num=ACTIVATE_RATIO,
                activate_ratio_den=1,
                reject_ratio_num=1,
                reject_ratio_den=REJECT_RATIO_DEN,
                recent_window=policy["recent_window"],
                recent_gain_bits=policy["recent_gain_bits"],
                persistence_observations=policy["persistence_observations"],
                min_projected_gain_bits=policy["min_projected_gain_bits"],
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
        return factory

    def stability_fp(stream_bytes: int, *, specialist_available: bool = True) -> bytes:
        return stability_value_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp if specialist_available else None,
            stream_bytes=stream_bytes,
            min_stream_bytes=0,
            min_observations=MIN_OBSERVATIONS,
            max_probe_bytes=policy["max_probe_bytes"],
            activate_ratio_num=ACTIVATE_RATIO,
            activate_ratio_den=1,
            reject_ratio_num=1,
            reject_ratio_den=REJECT_RATIO_DEN,
            recent_window=policy["recent_window"],
            recent_gain_bits=policy["recent_gain_bits"],
            persistence_observations=policy["persistence_observations"],
            min_projected_gain_bits=policy["min_projected_gain_bits"],
        )

    p9_policy = p9_results["development"]["selected_policy"]

    def sequential_factory(stream_bytes: int):
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

    def sequential_fp(stream_bytes: int) -> bytes:
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

    # ------------------------------------------------------------------
    # New holdout: six Silesia files not used in PILOT-007.
    # ------------------------------------------------------------------
    holdout_rows = []
    holdout_manifest = []
    for name, (category, expected_size, expected_md5) in UNUSED_SILESIA.items():
        url = f"{SILESIA_BASE}/{name}.bz2"
        request = urllib.request.Request(url, headers={"User-Agent": "POLLICINO-PILOT-010/1.0"})
        compressed = urllib.request.urlopen(request, timeout=180).read()
        raw = bz2.decompress(compressed)
        if len(raw) != expected_size:
            raise RuntimeError(f"Silesia {name}: {len(raw)} != {expected_size}")
        if md5(raw) != expected_md5:
            raise RuntimeError(f"Silesia {name}: MD5 mismatch")
        sample = raw[:HOLDOUT_SLICE]

        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        seq = roundtrip(sample, sequential_factory(len(sample)), sequential_fp(len(sample)))
        stab = roundtrip(sample, stability_factory(len(sample)), stability_fp(len(sample)))
        no_model = roundtrip(
            sample,
            stability_factory(len(sample), specialist_available=False),
            stability_fp(len(sample), specialist_available=False),
        )
        base = baselines(sample)
        target = "neural-gate" if cheap["payload_bpb"] - neural["payload_bpb"] >= MEANINGFUL_GAIN_BPB else "cheap-gate"
        oracle = min(cheap["payload_bpb"], neural["payload_bpb"])
        row = {
            "file": name,
            "category": category,
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "sequential_payload_bpb": seq["payload_bpb"],
            "stability_payload_bpb": stab["payload_bpb"],
            "stability_pol1_bpb": stab["pol1_bpb"],
            "oracle_payload_bpb": oracle,
            "sequential_oracle_regret_bpb": seq["payload_bpb"] - oracle,
            "stability_oracle_regret_bpb": stab["payload_bpb"] - oracle,
            "target_route": target,
            "sequential_route": seq["selected_route"],
            "sequential_decision_byte": seq["decision_byte"],
            "sequential_specialist_calls": seq["specialist_calls"],
            "stability_route": stab["selected_route"],
            "stability_decision_byte": stab["decision_byte"],
            "stability_decision_reason": stab["decision_reason"],
            "stability_specialist_calls": stab["specialist_calls"],
            "stability_max_candidate_streak": stab["max_candidate_streak"],
            "stability_correct_route": stab["selected_route"] == target,
            "sequential_correct_route": seq["selected_route"] == target,
            "cheap_encode_seconds": cheap["encode_seconds"],
            "neural_encode_seconds": neural["encode_seconds"],
            "sequential_encode_seconds": seq["encode_seconds"],
            "stability_encode_seconds": stab["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "neural_decode_seconds": neural["decode_seconds"],
            "sequential_decode_seconds": seq["decode_seconds"],
            "stability_decode_seconds": stab["decode_seconds"],
            "no_model_payload_bpb": no_model["payload_bpb"],
            "no_model_route": no_model["selected_route"],
            **base,
        }
        holdout_rows.append(row)
        holdout_manifest.append({
            "file": name,
            "category": category,
            "source_url": url,
            "bytes": len(raw),
            "md5": md5(raw),
            "sha256": sha(raw),
            "compressed_bytes": len(compressed),
            "compressed_sha256": sha(compressed),
            "sample_bytes": len(sample),
            "sample_sha256": sha(sample),
        })
        print("HOLDOUT", name, stab["selected_route"], stab["decision_byte"], stab["payload_bpb"], flush=True)
        del raw

    holdout_agg = {
        "files": len(holdout_rows),
        "mean_cheap_bpb": mean(r["cheap_payload_bpb"] for r in holdout_rows),
        "mean_neural_bpb": mean(r["neural_payload_bpb"] for r in holdout_rows),
        "mean_sequential_bpb": mean(r["sequential_payload_bpb"] for r in holdout_rows),
        "mean_stability_bpb": mean(r["stability_payload_bpb"] for r in holdout_rows),
        "mean_oracle_bpb": mean(r["oracle_payload_bpb"] for r in holdout_rows),
        "mean_sequential_oracle_regret_bpb": mean(r["sequential_oracle_regret_bpb"] for r in holdout_rows),
        "mean_stability_oracle_regret_bpb": mean(r["stability_oracle_regret_bpb"] for r in holdout_rows),
        "mean_zlib_bpb": mean(r["zlib_bpb"] for r in holdout_rows),
        "mean_zstd19_bpb": mean(r["zstd19_bpb"] for r in holdout_rows),
        "sequential_correct_routes": sum(r["sequential_correct_route"] for r in holdout_rows),
        "stability_correct_routes": sum(r["stability_correct_route"] for r in holdout_rows),
        "sequential_neural_routes": sum(r["sequential_route"] == "neural-gate" for r in holdout_rows),
        "stability_neural_routes": sum(r["stability_route"] == "neural-gate" for r in holdout_rows),
        "mean_sequential_decision_byte": mean(r["sequential_decision_byte"] for r in holdout_rows),
        "mean_stability_decision_byte": mean(r["stability_decision_byte"] for r in holdout_rows),
        "mean_sequential_specialist_calls": mean(r["sequential_specialist_calls"] for r in holdout_rows),
        "mean_stability_specialist_calls": mean(r["stability_specialist_calls"] for r in holdout_rows),
        "mean_sequential_encode_seconds": mean(r["sequential_encode_seconds"] for r in holdout_rows),
        "mean_stability_encode_seconds": mean(r["stability_encode_seconds"] for r in holdout_rows),
        "mean_neural_encode_seconds": mean(r["neural_encode_seconds"] for r in holdout_rows),
        "mean_cheap_encode_seconds": mean(r["cheap_encode_seconds"] for r in holdout_rows),
    }

    # Regression controls reused from earlier pilots; not tuning data.
    p4_art = p4.download(p4.ART_URL, OUT / "artificl.zip")
    art = p4.unpack(p4_art, p4.ART)
    controls = []
    control_samples = [
        ("self-v2-test", "training-domain-test", p6.frozen_test_split()[:HOLDOUT_SLICE]),
        ("aaa.txt", "repetition", art["aaa.txt"][:HOLDOUT_SLICE]),
        ("random.txt", "random-64-symbol-alphabet", art["random.txt"][:HOLDOUT_SLICE]),
    ]
    for name, category, sample in control_samples:
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        seq = roundtrip(sample, sequential_factory(len(sample)), sequential_fp(len(sample)))
        stab = roundtrip(sample, stability_factory(len(sample)), stability_fp(len(sample)))
        controls.append({
            "file": name,
            "category": category,
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "sequential_payload_bpb": seq["payload_bpb"],
            "sequential_route": seq["selected_route"],
            "sequential_decision_byte": seq["decision_byte"],
            "stability_payload_bpb": stab["payload_bpb"],
            "stability_route": stab["selected_route"],
            "stability_decision_byte": stab["decision_byte"],
            "stability_decision_reason": stab["decision_reason"],
            "stability_specialist_calls": stab["specialist_calls"],
        })

    development_summary = {
        "files": len(dev_routes),
        "correct": sum(r["correct"] for r in dev_routes),
        "false_positive": sum(r["route"] == "neural-gate" and r["target"] == "cheap-gate" for r in dev_routes),
        "false_negative": sum(r["route"] == "cheap-gate" and r["target"] == "neural-gate" for r in dev_routes),
        "mean_decision_byte": mean(r["decision_byte"] for r in dev_routes),
    }

    results = {
        "experiment_id": "pilot-010-stability-aware-value-routing",
        "question": "Can persistence, recent evidence and a deterministic future-value floor reduce false neural activation without losing useful specialists?",
        "development": {
            "corpora": [
                "PILOT-007 six-file Silesia subset",
                "PILOT-008 Large Corpus subset",
                "PILOT-009 Pizza&Chili pseudo-real subset",
            ],
            "meaningful_gain_bpb": MEANINGFUL_GAIN_BPB,
            "files": 14,
            "trace_bytes": DEV_TRACE_BYTES,
            "candidate_grid": {
                "min_observations": MIN_OBSERVATIONS,
                "activate_ratio": ACTIVATE_RATIO,
                "reject_ratio_den": REJECT_RATIO_DEN,
                "max_probe_bytes": list(MAX_PROBES),
                "recent_window": list(RECENT_WINDOWS),
                "persistence_observations": list(PERSISTENCE),
                "recent_gain_bits": list(RECENT_GAIN_BITS),
                "min_projected_gain_bits": list(MIN_PROJECTED_GAIN_BITS),
            },
            "ranking": "maximize correct routes, then minimize false positives, false negatives, oracle regret and decision latency",
            "selected_policy": {
                "min_observations": MIN_OBSERVATIONS,
                "activate_ratio": ACTIVATE_RATIO,
                "reject_ratio_den": REJECT_RATIO_DEN,
                **policy,
            },
            "selected_policy_development": development_summary,
        },
        "new_holdout": {
            "name": "Silesia unused six-file subset",
            "files": list(UNUSED_SILESIA),
            "sample_bytes_per_file": HOLDOUT_SLICE,
            "aggregate": holdout_agg,
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
            "routing_arithmetic": "integer CDF masses only",
            "future_value_floor": "floor(remaining_bytes/recent_window)*recent_gain_bits",
            "holdout_not_used_for_tuning": True,
            "wall_clock_not_used_in_routing": True,
        },
        "run": {
            "github_actions_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
            "head_sha": os.environ.get("GITHUB_SHA", "local"),
        },
        "limits": [
            "The six-file Silesia holdout comes from the same overall corpus family as PILOT-007, but these six individual files were not evaluated in earlier POLLICINO pilots.",
            "Only the first 4096 bytes of each holdout file are entropy-coded; full-file identity is recorded in the manifest.",
            "The 0.05 bpb meaningful-gain label and the projected-gain floor are policy choices, not information-theoretic constants.",
            "The neural checkpoint is assumed shared whenever the neural route is available.",
        ],
    }

    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    csvout(OUT / "candidate-policies.csv", candidate_rows)
    csvout(OUT / "development-routes.csv", dev_routes)
    csvout(OUT / "holdout.csv", holdout_rows)
    csvout(OUT / "controls.csv", controls)
    (OUT / "holdout-manifest.json").write_text(json.dumps(holdout_manifest, indent=2) + "\n")
    print(json.dumps({"policy": policy, "development": development_summary, "holdout": holdout_agg, "controls": controls}, indent=2))


if __name__ == "__main__":
    main()
