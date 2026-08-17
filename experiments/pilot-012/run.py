from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import random
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
from pollicino.compression.bit_credit_routing import (
    BitCreditSpecialistRouterCDFProvider,
    bit_credit_router_fingerprint,
)
from pollicino.compression.block_routing import (
    BlockLocalBitCreditRouterCDFProvider,
    BlockResetCDFProvider,
    block_local_router_fingerprint,
)
from pollicino.compression.classical_experts import RunLengthCDFProvider, run_length_fingerprint
from pollicino.compression.codec import decode_pol, encode_shared, inspect_pol
from pollicino.compression.gating import DeterministicExpertGateCDFProvider, expert_gate_fingerprint
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint

PRECISION = 18
STREAM_BYTES = 4096
BLOCK_CANDIDATES = (256, 512, 1024)
MODE_BUDGETS = {"max": 1.0, "balanced": 0.50}
CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)

FRESH_SOURCES = {
    "cpython-json-decoder": {
        "url": "https://raw.githubusercontent.com/python/cpython/v3.11.15/Lib/json/decoder.py",
        "git_blob_sha1": "c5d9ae2d0d5d040708f097fbf6450b86eef334dd",
    },
    "linux-sched-core": {
        "url": "https://raw.githubusercontent.com/torvalds/linux/v6.6/kernel/sched/core.c",
        "git_blob_sha1": "802551e0009bf1ef66191441a802633bb57543bc",
    },
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def cycle(data: bytes, n: int, *, offset: int = 0) -> bytes:
    if not data:
        raise ValueError("cannot cycle empty data")
    offset %= len(data)
    source = data[offset:] + data[:offset]
    repeats = (n + len(source) - 1) // len(source)
    return (source * repeats)[:n]


def random_bytes(n: int, seed: int, alphabet: int = 256) -> bytes:
    rng = random.Random(seed)
    return bytes(rng.randrange(alphabet) for _ in range(n))


def dna_bytes(n: int, seed: int) -> bytes:
    rng = random.Random(seed)
    alphabet = b"ACGT"
    return bytes(alphabet[rng.randrange(4)] for _ in range(n))


def json_bytes(n: int, seed: int) -> bytes:
    rng = random.Random(seed)
    rows = []
    for i in range(180):
        row = {
            "id": i,
            "group": i % 11,
            "enabled": (i % 3) != 0,
            "score": rng.randrange(100000),
            "name": f"record-{i:04d}",
            "tags": [f"t{(i+j)%17}" for j in range(3)],
        }
        rows.append(json.dumps(row, sort_keys=True, separators=(",", ":")))
    return cycle(("[" + ",".join(rows) + "]").encode(), n)


def english_bytes(n: int) -> bytes:
    text = (
        "A deterministic compressor should spend expensive computation only when the observed bytes "
        "show that the specialist is buying enough information. The decoder sees the same past and "
        "must therefore make the same decision without receiving a separate selector. "
    ).encode()
    return cycle(text, n)


def compressed_bytes(n: int, seed: int) -> bytes:
    raw = json_bytes(20000, seed) + random_bytes(8000, seed + 1, 64)
    packed = zlib.compress(raw, 9)
    return cycle(packed, n)


def compose(components: dict[str, bytes], recipe: list[tuple[str, int]], total: int = STREAM_BYTES) -> tuple[bytes, list[dict]]:
    out = bytearray()
    manifest = []
    for name, requested in recipe:
        length = requested if requested >= 0 else total - len(out)
        if length < 0 or len(out) + length > total:
            raise ValueError("invalid composition recipe")
        start = len(out)
        out.extend(cycle(components[name], length, offset=start % max(1, len(components[name]))))
        manifest.append({"component": name, "start": start, "end": len(out), "bytes": length})
    if len(out) != total:
        raise ValueError(f"recipe produced {len(out)} bytes, expected {total}")
    return bytes(out), manifest


def download_fresh_sources() -> tuple[dict[str, bytes], list[dict]]:
    sources = {}
    manifest = []
    for name, meta in FRESH_SOURCES.items():
        req = urllib.request.Request(meta["url"], headers={"User-Agent": "POLLICINO-PILOT-012/1.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
        blob = git_blob_sha1(data)
        if blob != meta["git_blob_sha1"]:
            raise RuntimeError(f"{name}: git blob mismatch {blob}")
        sources[name] = data
        manifest.append({
            "name": name,
            "url": meta["url"],
            "git_blob_sha1": blob,
            "bytes": len(data),
            "sha256": sha256(data),
        })
    return sources, manifest


def baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p6 = load_module(ROOT / "experiments/pilot-006/run.py", "pilot006_for_p12")
    p9exact = load_module(ROOT / "experiments/pilot-009/exact_checkpoint.py", "pilot009_exact_for_p12")
    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
    p11_results = json.loads((ROOT / "experiments/pilot-011/results.json").read_text())

    model, spec, checkpoint = p9exact.load_exact_checkpoint()
    neural_fp = torch_model_fingerprint(model, spec)
    expected = p11_results["model"]["canonical_neural_fingerprint"]
    if neural_fp.hex() != expected:
        raise RuntimeError("exact PILOT-003 checkpoint fingerprint mismatch")

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

    mode_policies = p11_results["development"]["selected_modes"]

    def file_router_factory(mode: str, stream_bytes: int):
        policy = mode_policies[mode]
        def factory():
            return BitCreditSpecialistRouterCDFProvider(
                cheap_factory(), neural_factory(), stream_bytes=stream_bytes,
                min_stream_bytes=0,
                min_observations=int(policy["min_observations"]),
                max_probe_bytes=int(policy["max_probe_bytes"]),
                activation_credit_bits=int(policy["activation_credit_bits"]),
                rejection_credit_bits=int(policy["rejection_credit_bits"]),
                cheap_name="cheap-gate", specialist_name="neural-gate",
            )
        return factory

    def file_router_fp(mode: str, stream_bytes: int) -> bytes:
        policy = mode_policies[mode]
        return bit_credit_router_fingerprint(
            cheap_fingerprint=cheap_fp, specialist_fingerprint=neural_gate_fp,
            stream_bytes=stream_bytes, min_stream_bytes=0,
            min_observations=int(policy["min_observations"]),
            max_probe_bytes=int(policy["max_probe_bytes"]),
            activation_credit_bits=int(policy["activation_credit_bits"]),
            rejection_credit_bits=int(policy["rejection_credit_bits"]),
        )

    def block_router_factory(mode: str, stream_bytes: int, block_bytes: int):
        policy = mode_policies[mode]
        def factory():
            return BlockLocalBitCreditRouterCDFProvider(
                cheap_factory, neural_factory,
                stream_bytes=stream_bytes, block_bytes=block_bytes,
                min_observations=int(policy["min_observations"]),
                max_probe_bytes=int(policy["max_probe_bytes"]),
                activation_credit_bits=int(policy["activation_credit_bits"]),
                rejection_credit_bits=int(policy["rejection_credit_bits"]),
                cheap_name="cheap-gate", specialist_name="neural-gate",
            )
        return factory

    def block_router_fp(mode: str, stream_bytes: int, block_bytes: int) -> bytes:
        policy = mode_policies[mode]
        return block_local_router_fingerprint(
            cheap_fingerprint=cheap_fp, specialist_fingerprint=neural_gate_fp,
            stream_bytes=stream_bytes, block_bytes=block_bytes,
            min_observations=int(policy["min_observations"]),
            max_probe_bytes=int(policy["max_probe_bytes"]),
            activation_credit_bits=int(policy["activation_credit_bits"]),
            rejection_credit_bits=int(policy["rejection_credit_bits"]),
        )

    def reset_fp(base_fp: bytes, stream_bytes: int, block_bytes: int, label: str) -> bytes:
        payload = b"p12-block-reset-v1\0" + label.encode() + base_fp + stream_bytes.to_bytes(8, "big") + block_bytes.to_bytes(4, "big")
        return hashlib.sha256(payload).digest()

    def encode_only(data: bytes, factory, fp: bytes) -> dict:
        provider = factory()
        started = time.perf_counter()
        blob = encode_shared(data, provider, fp, precision_bits=PRECISION)
        elapsed = time.perf_counter() - started
        info = inspect_pol(blob)
        out = {"payload_bpb": info["payload_bpb"], "pol1_bpb": info["realized_bpb"], "encode_seconds": elapsed}
        if hasattr(provider, "compute_fraction"):
            out["compute_fraction"] = float(provider.compute_fraction)
        if hasattr(provider, "switch_count"):
            out["switch_count"] = int(provider.switch_count)
            out["block_summary"] = provider.block_summary()
        return out

    def roundtrip(data: bytes, factory, fp: bytes) -> dict:
        enc_provider = factory()
        started = time.perf_counter()
        blob = encode_shared(data, enc_provider, fp, precision_bits=PRECISION)
        enc_seconds = time.perf_counter() - started
        dec_provider = factory()
        started = time.perf_counter()
        restored = decode_pol(blob, shared_provider=dec_provider, expected_model_fingerprint=fp)
        dec_seconds = time.perf_counter() - started
        assert restored == data
        if hasattr(enc_provider, "block_summary"):
            assert enc_provider.block_summary() == dec_provider.block_summary()
        info = inspect_pol(blob)
        out = {
            "payload_bpb": info["payload_bpb"], "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc_seconds, "decode_seconds": dec_seconds,
        }
        if hasattr(enc_provider, "compute_fraction"):
            out["compute_fraction"] = float(enc_provider.compute_fraction)
        if hasattr(enc_provider, "switch_count"):
            out["switch_count"] = int(enc_provider.switch_count)
            out["block_summary"] = enc_provider.block_summary()
        return out

    # ---------------------------------------------------------------
    # Development: no fresh external sources.  These deterministic mixed streams
    # use the already-consumed self-v2 test bytes plus generated controls.
    # ---------------------------------------------------------------
    self_v2 = p6.frozen_test_split()
    dev_components = {
        "self": cycle(self_v2, STREAM_BYTES),
        "json": json_bytes(STREAM_BYTES, 1201),
        "dna": dna_bytes(STREAM_BYTES, 1202),
        "random64": random_bytes(STREAM_BYTES, 1203, 64),
        "random256": random_bytes(STREAM_BYTES, 1204, 256),
        "repeat": cycle(b"AAAAAAAABBBBBBBB", STREAM_BYTES),
        "compressed": compressed_bytes(STREAM_BYTES, 1205),
        "english": english_bytes(STREAM_BYTES),
    }
    dev_recipes = {
        "dev-a": [("self", 901), ("random256", 703), ("json", 1097), ("repeat", 599), ("self", -1)],
        "dev-b": [("json", 1301), ("dna", 777), ("random64", 899), ("repeat", -1)],
        "dev-c": [("self", 1499), ("compressed", 653), ("dna", 1199), ("random256", -1)],
        "dev-d": [("repeat", 337), ("english", 811), ("self", 1201), ("random64", 1021), ("json", -1)],
    }
    dev_streams = {name: compose(dev_components, recipe)[0] for name, recipe in dev_recipes.items()}

    development_rows = []
    selected_blocks = {}
    for mode, budget in MODE_BUDGETS.items():
        candidates = []
        for block_bytes in BLOCK_CANDIDATES:
            rows = []
            for name, data in dev_streams.items():
                result = encode_only(data, block_router_factory(mode, len(data), block_bytes), block_router_fp(mode, len(data), block_bytes))
                rows.append(result)
                development_rows.append({
                    "mode": mode, "block_bytes": block_bytes, "stream": name,
                    "payload_bpb": result["payload_bpb"], "compute_fraction": result["compute_fraction"],
                    "switch_count": result["switch_count"], "encode_seconds": result["encode_seconds"],
                })
            candidates.append({
                "mode": mode, "block_bytes": block_bytes,
                "mean_payload_bpb": mean(r["payload_bpb"] for r in rows),
                "mean_compute_fraction": mean(r["compute_fraction"] for r in rows),
                "mean_switch_count": mean(r["switch_count"] for r in rows),
            })
        feasible = [row for row in candidates if row["mean_compute_fraction"] <= budget + 1e-12]
        if not feasible:
            selected_blocks[mode] = None
        else:
            selected_blocks[mode] = min(feasible, key=lambda r: (r["mean_payload_bpb"], r["mean_compute_fraction"], r["block_bytes"]))

    # ---------------------------------------------------------------
    # Fresh holdout opened only after block sizes are frozen.
    # ---------------------------------------------------------------
    fresh, source_manifest = download_fresh_sources()
    hold_components = {
        "cpython": fresh["cpython-json-decoder"],
        "linux": fresh["linux-sched-core"],
        "json": json_bytes(STREAM_BYTES, 2201),
        "dna": dna_bytes(STREAM_BYTES, 2202),
        "random64": random_bytes(STREAM_BYTES, 2203, 64),
        "random256": random_bytes(STREAM_BYTES, 2204, 256),
        "repeat": cycle(b"POLLICINO-POLLICINO-", STREAM_BYTES),
        "compressed": compressed_bytes(STREAM_BYTES, 2205),
        "english": english_bytes(STREAM_BYTES),
    }
    hold_recipes = {
        "mix-a": [("cpython", 851), ("random256", 457), ("linux", 1099), ("repeat", 389), ("json", -1)],
        "mix-b": [("linux", 727), ("dna", 901), ("cpython", 1027), ("compressed", -1)],
        "mix-c": [("english", 667), ("cpython", 947), ("random64", 557), ("linux", -1)],
        "mix-d": [("json", 877), ("linux", 823), ("repeat", 353), ("compressed", 701), ("cpython", -1)],
        "mix-e": [("random256", 499), ("cpython", 1157), ("dna", 751), ("linux", -1)],
        "mix-f": [("cpython", 461), ("repeat", 607), ("linux", 443), ("random256", 719), ("json", -1)],
    }
    hold_streams = {}
    composition_manifest = []
    for name, recipe in hold_recipes.items():
        data, segments = compose(hold_components, recipe)
        hold_streams[name] = data
        composition_manifest.append({"stream": name, "bytes": len(data), "sha256": sha256(data), "segments": segments})

    holdout_rows = []
    block_rows = []
    for name, data in hold_streams.items():
        cheap_global = roundtrip(data, cheap_factory, cheap_fp)
        neural_global = roundtrip(data, neural_factory, neural_gate_fp)
        base = baselines(data)
        row = {
            "stream": name, "sample_bytes": len(data),
            "cheap_global_bpb": cheap_global["payload_bpb"],
            "neural_global_bpb": neural_global["payload_bpb"],
            **base,
        }
        for mode in MODE_BUDGETS:
            selected = selected_blocks[mode]
            if selected is None:
                row[f"{mode}_status"] = "development-budget-infeasible"
                continue
            block_bytes = int(selected["block_bytes"])
            file_result = roundtrip(data, file_router_factory(mode, len(data)), file_router_fp(mode, len(data)))
            block_result = roundtrip(data, block_router_factory(mode, len(data), block_bytes), block_router_fp(mode, len(data), block_bytes))
            cheap_reset_factory = lambda bb=block_bytes: BlockResetCDFProvider(cheap_factory, stream_bytes=len(data), block_bytes=bb)
            neural_reset_factory = lambda bb=block_bytes: BlockResetCDFProvider(neural_factory, stream_bytes=len(data), block_bytes=bb)
            cheap_reset = roundtrip(data, cheap_reset_factory, reset_fp(cheap_fp, len(data), block_bytes, "cheap"))
            neural_reset = roundtrip(data, neural_reset_factory, reset_fp(neural_gate_fp, len(data), block_bytes, "neural"))

            oracle_bits = 0
            for block_index, start in enumerate(range(0, len(data), block_bytes)):
                block = data[start : start + block_bytes]
                cb = encode_only(block, cheap_factory, cheap_fp)
                nb = encode_only(block, neural_factory, neural_gate_fp)
                cbits = round(cb["payload_bpb"] * len(block))
                nbits = round(nb["payload_bpb"] * len(block))
                oracle_bits += min(cbits, nbits)
                route = block_result["block_summary"][block_index]
                block_rows.append({
                    "stream": name, "mode": mode, "block_bytes": block_bytes,
                    "block_index": block_index, "start": start, "bytes": len(block),
                    "cheap_payload_bits": cbits, "neural_payload_bits": nbits,
                    "oracle_route": "cheap-gate" if cbits <= nbits else "neural-gate",
                    "selected_route": route["route"], "decision_byte": route["decision_byte"],
                    "specialist_calls": route["specialist_calls"],
                })
            oracle_bpb = oracle_bits / len(data)
            row.update({
                f"{mode}_block_bytes": block_bytes,
                f"{mode}_file_bpb": file_result["payload_bpb"],
                f"{mode}_file_compute_fraction": file_result.get("compute_fraction", 0.0),
                f"{mode}_block_bpb": block_result["payload_bpb"],
                f"{mode}_block_pol1_bpb": block_result["pol1_bpb"],
                f"{mode}_block_compute_fraction": block_result["compute_fraction"],
                f"{mode}_block_switch_count": block_result["switch_count"],
                f"{mode}_block_oracle_bpb": oracle_bpb,
                f"{mode}_block_oracle_regret_bpb": block_result["payload_bpb"] - oracle_bpb,
                f"{mode}_cheap_reset_bpb": cheap_reset["payload_bpb"],
                f"{mode}_neural_reset_bpb": neural_reset["payload_bpb"],
                f"{mode}_block_encode_seconds": block_result["encode_seconds"],
                f"{mode}_block_decode_seconds": block_result["decode_seconds"],
            })
        holdout_rows.append(row)
        print("HOLDOUT", name, json.dumps(row, sort_keys=True), flush=True)

    aggregates = {}
    for mode in MODE_BUDGETS:
        selected = selected_blocks[mode]
        if selected is None:
            aggregates[mode] = {"status": "development-budget-infeasible"}
            continue
        aggregates[mode] = {
            "block_bytes": int(selected["block_bytes"]),
            "development_mean_payload_bpb": selected["mean_payload_bpb"],
            "development_mean_compute_fraction": selected["mean_compute_fraction"],
            "mean_file_bpb": mean(r[f"{mode}_file_bpb"] for r in holdout_rows),
            "mean_block_bpb": mean(r[f"{mode}_block_bpb"] for r in holdout_rows),
            "mean_block_oracle_bpb": mean(r[f"{mode}_block_oracle_bpb"] for r in holdout_rows),
            "mean_block_oracle_regret_bpb": mean(r[f"{mode}_block_oracle_regret_bpb"] for r in holdout_rows),
            "mean_block_compute_fraction": mean(r[f"{mode}_block_compute_fraction"] for r in holdout_rows),
            "mean_block_switch_count": mean(r[f"{mode}_block_switch_count"] for r in holdout_rows),
            "block_beats_file_streams": sum(r[f"{mode}_block_bpb"] < r[f"{mode}_file_bpb"] for r in holdout_rows),
        }

    results = {
        "experiment_id": "pilot-012-block-local-regret-routing",
        "question": "Can deterministic block-local re-routing exploit domain changes inside a stream better than one irreversible file-level regret-aware decision?",
        "development": {
            "streams": list(dev_streams),
            "stream_bytes": STREAM_BYTES,
            "block_candidates": list(BLOCK_CANDIDATES),
            "mode_compute_budgets": MODE_BUDGETS,
            "selection_rule": "for each frozen PILOT-011 mode, minimize real payload bpb among block sizes satisfying the same deterministic mean specialist-call budget",
            "selected_blocks": selected_blocks,
            "fresh_external_sources_used": False,
        },
        "new_holdout": {
            "name": "PILOT-012 deterministic mixed-source holdout",
            "streams": list(hold_streams),
            "stream_bytes": STREAM_BYTES,
            "external_sources": source_manifest,
            "aggregate": aggregates,
            "mean_zlib_bpb": mean(r["zlib_bpb"] for r in holdout_rows),
            "mean_zstd19_bpb": mean(r["zstd19_bpb"] for r in holdout_rows),
            "per_stream_table": "holdout.csv",
            "per_block_table": "blocks.csv",
            "composition_manifest": "holdout-manifest.json",
        },
        "model": {
            "canonical_neural_fingerprint": neural_fp.hex(),
            "cheap_gate_fingerprint": cheap_fp.hex(),
            "neural_gate_fingerprint": neural_gate_fp.hex(),
        },
        "frozen_checkpoint": {"source_experiment": "PILOT-003", **checkpoint, "canonical_model_fingerprint": neural_fp.hex()},
        "protocol": {
            "precision_bits": PRECISION,
            "selector_side_bits": 0,
            "block_state": "cheap and neural expert state reset at every fixed block boundary",
            "inner_policies": "frozen PILOT-011 max and balanced policies; thresholds are not retuned",
            "holdout_not_used_for_block_size_selection": True,
            "wall_clock_not_used_in_routing_or_selection": True,
        },
        "run": {"github_actions_run_id": os.environ.get("GITHUB_RUN_ID", "local"), "head_sha": os.environ.get("GITHUB_SHA", "local")},
        "limits": [
            "The fresh holdout is deliberately constructed to contain within-stream domain changes; it is a mechanism benchmark, not a universal corpus.",
            "Only 4096 bytes per mixed stream are coded.",
            "Generated DNA/random/repetition/JSON segments are deterministic controls rather than naturally occurring files.",
            "Block resets change model state and therefore block-local results must be compared with the block-reset oracle/baselines as well as file-level routing.",
            "The neural checkpoint is assumed shared whenever neural routing is available.",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    csvout(OUT / "development.csv", development_rows)
    csvout(OUT / "holdout.csv", holdout_rows)
    csvout(OUT / "blocks.csv", block_rows)
    (OUT / "holdout-manifest.json").write_text(json.dumps({"sources": source_manifest, "streams": composition_manifest}, indent=2) + "\n")
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()
