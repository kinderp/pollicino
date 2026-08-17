from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
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
from pollicino.compression.admission_routing import (
    CheapCodelengthAdmissionBlockCDFProvider,
    cheap_codelength_admission_fingerprint,
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
BLOCK_BYTES = 512
MAX_ADMITTED_BYTES = STREAM_BYTES // 2
PROBE_CANDIDATES = (16, 32, 64)
# Thresholds are expressed in half-bits/byte and converted to exact integer
# codelength bounds over a fixed-size probe.
LOWER_BPB_X2 = (0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
UPPER_BPB_X2 = (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
VALIDATION_CANDIDATES = 8
RETAINED_GAIN_SUCCESS = 0.50
CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)

FRESH_SOURCES = {
    "go-http-server": {
        "url": "https://raw.githubusercontent.com/golang/go/go1.22.12/src/net/http/server.go",
        "git_blob_sha1": "23a603c91bc0aadc51203b50642c558920525bc1",
    },
    "node-cjs-loader": {
        "url": "https://raw.githubusercontent.com/nodejs/node/v20.19.1/lib/internal/modules/cjs/loader.js",
        "git_blob_sha1": "ebccdb81da2ed30b92edb1eaebfa7b84107cf53b",
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


def payload_bits(info: dict, source_bytes: int) -> int:
    return round(float(info["payload_bpb"]) * source_bytes)


def reset_fp(base_fp: bytes, stream_bytes: int, label: str) -> bytes:
    payload = (
        b"p13-block-reset-v1\0"
        + label.encode()
        + base_fp
        + stream_bytes.to_bytes(8, "big")
        + BLOCK_BYTES.to_bytes(4, "big")
    )
    return hashlib.sha256(payload).digest()


def baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def codelength_integer_bounds(num: int, den: int) -> tuple[int, int]:
    """Return floor/ceil(-log2(num/den)) without floating point."""
    if num <= 0 or den <= 0 or num > den:
        raise ValueError("invalid likelihood ratio")
    floor_bits = max(0, den.bit_length() - num.bit_length())
    while floor_bits > 0 and (num << floor_bits) > den:
        floor_bits -= 1
    while (num << (floor_bits + 1)) <= den:
        floor_bits += 1
    exact = (num << floor_bits) == den
    return floor_bits, floor_bits if exact else floor_bits + 1


def measure_cheap_probe(cheap_factory, block: bytes, probe_bytes: int) -> tuple[int, int]:
    provider = cheap_factory()
    num = 1
    den = 1
    prefix: list[int] = []
    for index, symbol in enumerate(block[:probe_bytes]):
        cdf = provider(index, prefix)
        mass = int(cdf[symbol + 1]) - int(cdf[symbol])
        total = int(cdf[-1])
        if mass <= 0 or total <= 0:
            raise RuntimeError("cheap provider returned invalid CDF")
        num *= mass
        den *= total
        prefix.append(symbol)
    return codelength_integer_bounds(num, den)


def download_sources() -> tuple[dict[str, bytes], list[dict]]:
    sources: dict[str, bytes] = {}
    manifest: list[dict] = []
    for name, meta in FRESH_SOURCES.items():
        req = urllib.request.Request(meta["url"], headers={"User-Agent": "POLLICINO-PILOT-013/1.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
        blob = git_blob_sha1(data)
        if blob != meta["git_blob_sha1"]:
            raise RuntimeError(f"{name}: git blob mismatch {blob}")
        sources[name] = data
        manifest.append(
            {
                "name": name,
                "url": meta["url"],
                "git_blob_sha1": blob,
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    return sources, manifest


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p9exact = load_module(ROOT / "experiments/pilot-009/exact_checkpoint.py", "pilot009_exact_for_p13")
    p12 = load_module(ROOT / "experiments/pilot-012/run.py", "pilot012_for_p13")
    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
    p11_results = json.loads((ROOT / "experiments/pilot-011/results.json").read_text())
    p12_results = json.loads((ROOT / "experiments/pilot-012/results.json").read_text())

    model, spec, checkpoint = p9exact.load_exact_checkpoint()
    neural_fp = torch_model_fingerprint(model, spec)
    expected = p12_results["model"]["canonical_neural_fingerprint"]
    if neural_fp.hex() != expected:
        raise RuntimeError("exact frozen checkpoint fingerprint mismatch")

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
    neural_gate_fp = expert_gate_fingerprint(
        expert_fingerprints=neural_fps,
        names=NEURAL_NAMES,
        window=neural_window,
    )

    class TrackingNeuralFactory:
        def __init__(self):
            self.priors: list[PyTorchCDFProvider] = []

        def __call__(self):
            shared_prior = PyTorchCDFProvider(model, spec, precision_bits=PRECISION, device="cpu")
            self.priors.append(shared_prior)
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

        @property
        def model_evaluations(self) -> int:
            return sum(int(prior.model_evaluations) for prior in self.priors)

        @property
        def cache_hits(self) -> int:
            return sum(int(prior.cache_hits) for prior in self.priors)

    def encode_only(data: bytes, provider, fp: bytes) -> dict:
        started = time.perf_counter()
        blob = encode_shared(data, provider, fp, precision_bits=PRECISION)
        elapsed = time.perf_counter() - started
        info = inspect_pol(blob)
        return {
            "blob": blob,
            "payload_bits": payload_bits(info, len(data)),
            "payload_bpb": float(info["payload_bpb"]),
            "pol1_bpb": float(info["realized_bpb"]),
            "encode_seconds": elapsed,
        }

    def admission_fp(params: dict, stream_bytes: int) -> bytes:
        return cheap_codelength_admission_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp,
            stream_bytes=stream_bytes,
            block_bytes=BLOCK_BYTES,
            probe_bytes=int(params["probe_bytes"]),
            min_probe_code_bits=int(params["min_probe_code_bits"]),
            max_probe_code_bits=int(params["max_probe_code_bits"]),
            max_admitted_bytes=min(MAX_ADMITTED_BYTES, stream_bytes),
        )

    def run_admission(data: bytes, params: dict, *, verify: bool) -> dict:
        enc_tracker = TrackingNeuralFactory()
        enc_provider = CheapCodelengthAdmissionBlockCDFProvider(
            cheap_factory,
            enc_tracker,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            probe_bytes=int(params["probe_bytes"]),
            min_probe_code_bits=int(params["min_probe_code_bits"]),
            max_probe_code_bits=int(params["max_probe_code_bits"]),
            max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
            cheap_name="cheap-gate",
            specialist_name="neural-gate",
        )
        fp = admission_fp(params, len(data))
        encoded = encode_only(data, enc_provider, fp)
        out = {
            **{key: value for key, value in encoded.items() if key != "blob"},
            "model_evaluations": enc_tracker.model_evaluations,
            "model_eval_fraction": enc_tracker.model_evaluations / len(data),
            "neural_cache_hits": enc_tracker.cache_hits,
            "admitted_blocks": enc_provider.admitted_blocks,
            "admitted_bytes": enc_provider.admitted_bytes,
            "admitted_byte_fraction": enc_provider.admitted_byte_fraction,
            "block_summary": enc_provider.block_summary(),
        }
        if verify:
            dec_tracker = TrackingNeuralFactory()
            dec_provider = CheapCodelengthAdmissionBlockCDFProvider(
                cheap_factory,
                dec_tracker,
                stream_bytes=len(data),
                block_bytes=BLOCK_BYTES,
                probe_bytes=int(params["probe_bytes"]),
                min_probe_code_bits=int(params["min_probe_code_bits"]),
                max_probe_code_bits=int(params["max_probe_code_bits"]),
                max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
            started = time.perf_counter()
            restored = decode_pol(
                encoded["blob"],
                shared_provider=dec_provider,
                expected_model_fingerprint=fp,
            )
            out["decode_seconds"] = time.perf_counter() - started
            if restored != data:
                raise RuntimeError("PILOT-013 roundtrip failed")
            if enc_provider.block_summary() != dec_provider.block_summary():
                raise RuntimeError("encoder/decoder admission summaries diverged")
            if enc_tracker.model_evaluations != dec_tracker.model_evaluations:
                raise RuntimeError("encoder/decoder neural evaluation counts diverged")
            out["roundtrip"] = True
        return out

    def encode_direct_neural(data: bytes) -> dict:
        tracker = TrackingNeuralFactory()
        provider = tracker()
        result = encode_only(data, provider, neural_gate_fp)
        result["model_evaluations"] = tracker.model_evaluations
        return result

    def block_precompute(streams: dict[str, bytes]) -> list[dict]:
        rows: list[dict] = []
        for stream_name, data in streams.items():
            for block_index, start in enumerate(range(0, len(data), BLOCK_BYTES)):
                block = data[start : start + BLOCK_BYTES]
                cheap_result = encode_only(block, cheap_factory(), cheap_fp)
                neural_result = encode_direct_neural(block)
                for probe_bytes in PROBE_CANDIDATES:
                    floor_bits, ceil_bits = measure_cheap_probe(cheap_factory, block, probe_bytes)
                    tracker = TrackingNeuralFactory()
                    force_params = {
                        "probe_bytes": probe_bytes,
                        "min_probe_code_bits": 0,
                        "max_probe_code_bits": 1_000_000,
                    }
                    provider = CheapCodelengthAdmissionBlockCDFProvider(
                        cheap_factory,
                        tracker,
                        stream_bytes=len(block),
                        block_bytes=BLOCK_BYTES,
                        probe_bytes=probe_bytes,
                        min_probe_code_bits=0,
                        max_probe_code_bits=1_000_000,
                        max_admitted_bytes=len(block),
                        cheap_name="cheap-gate",
                        specialist_name="neural-gate",
                    )
                    hybrid_result = encode_only(block, provider, admission_fp(force_params, len(block)))
                    if provider.admitted_blocks != 1:
                        raise RuntimeError("forced development hybrid did not admit its block")
                    rows.append(
                        {
                            "stream": stream_name,
                            "block_index": block_index,
                            "start": start,
                            "bytes": len(block),
                            "probe_bytes": probe_bytes,
                            "probe_code_bits_floor": floor_bits,
                            "probe_code_bits_ceil": ceil_bits,
                            "cheap_payload_bits": cheap_result["payload_bits"],
                            "neural_payload_bits": neural_result["payload_bits"],
                            "neural_model_evaluations": neural_result["model_evaluations"],
                            "hybrid_payload_bits": hybrid_result["payload_bits"],
                            "hybrid_model_evaluations": tracker.model_evaluations,
                            "hybrid_saving_bits": cheap_result["payload_bits"] - hybrid_result["payload_bits"],
                        }
                    )
        return rows

    def simulate_policy(block_rows: list[dict], params: dict, stream_names: list[str]) -> dict:
        total_bits = 0
        total_evals = 0
        total_admitted_bytes = 0
        admitted_blocks = 0
        total_source_bytes = 0
        for stream_name in stream_names:
            rows = sorted(
                (
                    row
                    for row in block_rows
                    if row["stream"] == stream_name and row["probe_bytes"] == params["probe_bytes"]
                ),
                key=lambda row: row["block_index"],
            )
            spent = 0
            for row in rows:
                total_source_bytes += int(row["bytes"])
                match = (
                    int(row["probe_code_bits_floor"]) >= int(params["min_probe_code_bits"])
                    and int(row["probe_code_bits_ceil"]) <= int(params["max_probe_code_bits"])
                )
                admit = match and spent + int(row["bytes"]) <= MAX_ADMITTED_BYTES
                if admit:
                    spent += int(row["bytes"])
                    total_admitted_bytes += int(row["bytes"])
                    admitted_blocks += 1
                    total_bits += int(row["hybrid_payload_bits"])
                    total_evals += int(row["hybrid_model_evaluations"])
                else:
                    total_bits += int(row["cheap_payload_bits"])
        return {
            **params,
            "simulated_payload_bpb": total_bits / total_source_bytes,
            "simulated_model_eval_fraction": total_evals / total_source_bytes,
            "simulated_admitted_byte_fraction": total_admitted_bytes / total_source_bytes,
            "simulated_admitted_blocks": admitted_blocks,
        }

    # ------------------------------------------------------------------
    # DEVELOPMENT. Reconstruct the already-consumed PILOT-012 holdout.
    # No Go/Node PILOT-013 holdout bytes are opened before policy freeze.
    # ------------------------------------------------------------------
    consumed, consumed_manifest = p12.download_fresh_sources()
    dev_components = {
        "cpython": consumed["cpython-json-decoder"],
        "linux": consumed["linux-sched-core"],
        "json": p12.json_bytes(STREAM_BYTES, 2201),
        "dna": p12.dna_bytes(STREAM_BYTES, 2202),
        "random64": p12.random_bytes(STREAM_BYTES, 2203, 64),
        "random256": p12.random_bytes(STREAM_BYTES, 2204, 256),
        "repeat": p12.cycle(b"POLLICINO-POLLICINO-", STREAM_BYTES),
        "compressed": p12.compressed_bytes(STREAM_BYTES, 2205),
        "english": p12.english_bytes(STREAM_BYTES),
    }
    dev_recipes = {
        "p12-mix-a": [("cpython", 851), ("random256", 457), ("linux", 1099), ("repeat", 389), ("json", -1)],
        "p12-mix-b": [("linux", 727), ("dna", 901), ("cpython", 1027), ("compressed", -1)],
        "p12-mix-c": [("english", 667), ("cpython", 947), ("random64", 557), ("linux", -1)],
        "p12-mix-d": [("json", 877), ("linux", 823), ("repeat", 353), ("compressed", 701), ("cpython", -1)],
        "p12-mix-e": [("random256", 499), ("cpython", 1157), ("dna", 751), ("linux", -1)],
        "p12-mix-f": [("cpython", 461), ("repeat", 607), ("linux", 443), ("random256", 719), ("json", -1)],
    }
    dev_streams = {name: p12.compose(dev_components, recipe)[0] for name, recipe in dev_recipes.items()}
    dev_block_rows = block_precompute(dev_streams)

    candidates: list[dict] = []
    for probe_bytes in PROBE_CANDIDATES:
        for lower_x2 in LOWER_BPB_X2:
            for upper_x2 in UPPER_BPB_X2:
                if lower_x2 > upper_x2:
                    continue
                params = {
                    "probe_bytes": probe_bytes,
                    "min_probe_code_bits": probe_bytes * lower_x2 // 2,
                    "max_probe_code_bits": probe_bytes * upper_x2 // 2,
                    "min_probe_bpb_x2": lower_x2,
                    "max_probe_bpb_x2": upper_x2,
                }
                candidates.append(simulate_policy(dev_block_rows, params, list(dev_streams)))
    candidates.sort(
        key=lambda row: (
            row["simulated_payload_bpb"],
            row["simulated_model_eval_fraction"],
            row["probe_bytes"],
            row["min_probe_code_bits"],
            row["max_probe_code_bits"],
        )
    )

    # Validate the best coarse-screened policies with the actual whole-stream coder.
    validation_rows: list[dict] = []
    for rank, candidate in enumerate(candidates[:VALIDATION_CANDIDATES], start=1):
        per_stream = []
        for stream_name, data in dev_streams.items():
            result = run_admission(data, candidate, verify=False)
            per_stream.append(result)
            validation_rows.append(
                {
                    "screen_rank": rank,
                    "stream": stream_name,
                    "probe_bytes": candidate["probe_bytes"],
                    "min_probe_code_bits": candidate["min_probe_code_bits"],
                    "max_probe_code_bits": candidate["max_probe_code_bits"],
                    "min_probe_bpb": candidate["min_probe_bpb_x2"] / 2,
                    "max_probe_bpb": candidate["max_probe_bpb_x2"] / 2,
                    "payload_bpb": result["payload_bpb"],
                    "model_eval_fraction": result["model_eval_fraction"],
                    "admitted_byte_fraction": result["admitted_byte_fraction"],
                    "admitted_blocks": result["admitted_blocks"],
                }
            )
        candidate["validated_mean_payload_bpb"] = mean(r["payload_bpb"] for r in per_stream)
        candidate["validated_mean_model_eval_fraction"] = mean(r["model_eval_fraction"] for r in per_stream)
        candidate["validated_mean_admitted_byte_fraction"] = mean(
            r["admitted_byte_fraction"] for r in per_stream
        )

    validated = candidates[:VALIDATION_CANDIDATES]
    selected_policy = min(
        validated,
        key=lambda row: (
            row["validated_mean_payload_bpb"],
            row["validated_mean_model_eval_fraction"],
            row["probe_bytes"],
            row["min_probe_code_bits"],
            row["max_probe_code_bits"],
        ),
    )
    frozen_params = {
        "probe_bytes": int(selected_policy["probe_bytes"]),
        "min_probe_code_bits": int(selected_policy["min_probe_code_bits"]),
        "max_probe_code_bits": int(selected_policy["max_probe_code_bits"]),
        "min_probe_bpb": selected_policy["min_probe_bpb_x2"] / 2,
        "max_probe_bpb": selected_policy["max_probe_bpb_x2"] / 2,
        "max_admitted_bytes": MAX_ADMITTED_BYTES,
    }

    # Retrospective feasibility bound on consumed data: best <=4 neural-reset blocks.
    oracle_retained = []
    for stream_name in dev_streams:
        rows = [
            row
            for row in dev_block_rows
            if row["stream"] == stream_name and row["probe_bytes"] == PROBE_CANDIDATES[0]
        ]
        rows.sort(key=lambda row: row["block_index"])
        cheap_bits = sum(int(row["cheap_payload_bits"]) for row in rows)
        neural_bits = sum(int(row["neural_payload_bits"]) for row in rows)
        savings = sorted(
            (max(0, int(row["cheap_payload_bits"]) - int(row["neural_payload_bits"])) for row in rows),
            reverse=True,
        )
        budget_bits = cheap_bits - sum(savings[: MAX_ADMITTED_BYTES // BLOCK_BYTES])
        available = cheap_bits - neural_bits
        retained = (cheap_bits - budget_bits) / available if available > 0 else 0.0
        oracle_retained.append(retained)

    print("POLICY_FROZEN", json.dumps(frozen_params, sort_keys=True), flush=True)

    # ------------------------------------------------------------------
    # FRESH HOLDOUT. Only now are Go and Node bytes downloaded.
    # ------------------------------------------------------------------
    fresh, source_manifest = download_sources()
    hold_components = {
        "go": fresh["go-http-server"],
        "node": fresh["node-cjs-loader"],
        "json": p12.json_bytes(STREAM_BYTES, 3301),
        "dna": p12.dna_bytes(STREAM_BYTES, 3302),
        "random64": p12.random_bytes(STREAM_BYTES, 3303, 64),
        "random256": p12.random_bytes(STREAM_BYTES, 3304, 256),
        "repeat": p12.cycle(b"admit-cheap-or-neural-", STREAM_BYTES),
        "compressed": p12.compressed_bytes(STREAM_BYTES, 3305),
        "english": p12.english_bytes(STREAM_BYTES),
    }
    hold_recipes = {
        "fresh-a": [("go", 811), ("random256", 503), ("node", 1109), ("repeat", 421), ("json", -1)],
        "fresh-b": [("node", 727), ("dna", 933), ("go", 1001), ("compressed", -1)],
        "fresh-c": [("english", 689), ("go", 971), ("random64", 541), ("node", -1)],
        "fresh-d": [("json", 893), ("node", 809), ("repeat", 371), ("compressed", 683), ("go", -1)],
        "fresh-e": [("random256", 487), ("node", 1169), ("dna", 769), ("go", -1)],
        "fresh-f": [("go", 479), ("repeat", 593), ("node", 457), ("random256", 733), ("json", -1)],
    }
    hold_streams: dict[str, bytes] = {}
    composition_manifest: list[dict] = []
    for name, recipe in hold_recipes.items():
        data, segments = p12.compose(hold_components, recipe)
        hold_streams[name] = data
        composition_manifest.append(
            {"stream": name, "bytes": len(data), "sha256": sha256(data), "segments": segments}
        )

    max_policy = p11_results["development"]["selected_modes"]["max"]

    def p12_max_result(data: bytes) -> dict:
        tracker = TrackingNeuralFactory()
        provider = BlockLocalBitCreditRouterCDFProvider(
            cheap_factory,
            tracker,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            min_observations=int(max_policy["min_observations"]),
            max_probe_bytes=int(max_policy["max_probe_bytes"]),
            activation_credit_bits=int(max_policy["activation_credit_bits"]),
            rejection_credit_bits=int(max_policy["rejection_credit_bits"]),
            cheap_name="cheap-gate",
            specialist_name="neural-gate",
        )
        fp = block_local_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            min_observations=int(max_policy["min_observations"]),
            max_probe_bytes=int(max_policy["max_probe_bytes"]),
            activation_credit_bits=int(max_policy["activation_credit_bits"]),
            rejection_credit_bits=int(max_policy["rejection_credit_bits"]),
        )
        encoded = encode_only(data, provider, fp)
        dec_tracker = TrackingNeuralFactory()
        dec_provider = BlockLocalBitCreditRouterCDFProvider(
            cheap_factory,
            dec_tracker,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            min_observations=int(max_policy["min_observations"]),
            max_probe_bytes=int(max_policy["max_probe_bytes"]),
            activation_credit_bits=int(max_policy["activation_credit_bits"]),
            rejection_credit_bits=int(max_policy["rejection_credit_bits"]),
            cheap_name="cheap-gate",
            specialist_name="neural-gate",
        )
        restored = decode_pol(encoded["blob"], shared_provider=dec_provider, expected_model_fingerprint=fp)
        if restored != data or provider.block_summary() != dec_provider.block_summary():
            raise RuntimeError("PILOT-012 comparison roundtrip failed")
        return {
            "payload_bpb": encoded["payload_bpb"],
            "model_eval_fraction": tracker.model_evaluations / len(data),
            "model_evaluations": tracker.model_evaluations,
            "specialist_call_fraction": provider.compute_fraction,
        }

    def reset_roundtrip(data: bytes, *, neural: bool) -> dict:
        tracker = TrackingNeuralFactory() if neural else None
        base_factory = tracker if neural else cheap_factory
        base_fp = neural_gate_fp if neural else cheap_fp
        provider = BlockResetCDFProvider(base_factory, stream_bytes=len(data), block_bytes=BLOCK_BYTES)
        fp = reset_fp(base_fp, len(data), "neural" if neural else "cheap")
        encoded = encode_only(data, provider, fp)
        dec_tracker = TrackingNeuralFactory() if neural else None
        dec_factory = dec_tracker if neural else cheap_factory
        dec_provider = BlockResetCDFProvider(dec_factory, stream_bytes=len(data), block_bytes=BLOCK_BYTES)
        restored = decode_pol(encoded["blob"], shared_provider=dec_provider, expected_model_fingerprint=fp)
        if restored != data:
            raise RuntimeError("block-reset baseline roundtrip failed")
        return {
            "payload_bpb": encoded["payload_bpb"],
            "model_eval_fraction": (tracker.model_evaluations / len(data)) if tracker is not None else 0.0,
            "model_evaluations": tracker.model_evaluations if tracker is not None else 0,
        }

    holdout_rows: list[dict] = []
    holdout_block_rows: list[dict] = []
    for stream_name, data in hold_streams.items():
        cheap_reset = reset_roundtrip(data, neural=False)
        neural_reset = reset_roundtrip(data, neural=True)
        p12_max = p12_max_result(data)
        p13 = run_admission(data, frozen_params, verify=True)
        base = baselines(data)

        # Fresh diagnostic block outcomes for a non-causal 50%-budget oracle using
        # the same cheap-probe-then-neural mechanism as the frozen P13 policy.
        diagnostic: list[dict] = []
        for block_index, start in enumerate(range(0, len(data), BLOCK_BYTES)):
            block = data[start : start + BLOCK_BYTES]
            cheap_result = encode_only(block, cheap_factory(), cheap_fp)
            neural_result = encode_direct_neural(block)
            floor_bits, ceil_bits = measure_cheap_probe(
                cheap_factory, block, int(frozen_params["probe_bytes"])
            )
            tracker = TrackingNeuralFactory()
            force_params = {
                "probe_bytes": int(frozen_params["probe_bytes"]),
                "min_probe_code_bits": 0,
                "max_probe_code_bits": 1_000_000,
            }
            force_provider = CheapCodelengthAdmissionBlockCDFProvider(
                cheap_factory,
                tracker,
                stream_bytes=len(block),
                block_bytes=BLOCK_BYTES,
                probe_bytes=int(frozen_params["probe_bytes"]),
                min_probe_code_bits=0,
                max_probe_code_bits=1_000_000,
                max_admitted_bytes=len(block),
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
            hybrid_result = encode_only(block, force_provider, admission_fp(force_params, len(block)))
            diagnostic.append(
                {
                    "stream": stream_name,
                    "block_index": block_index,
                    "start": start,
                    "bytes": len(block),
                    "probe_code_bits_floor": floor_bits,
                    "probe_code_bits_ceil": ceil_bits,
                    "cheap_payload_bits": cheap_result["payload_bits"],
                    "neural_payload_bits": neural_result["payload_bits"],
                    "hybrid_payload_bits": hybrid_result["payload_bits"],
                    "hybrid_model_evaluations": tracker.model_evaluations,
                    "hybrid_saving_bits": cheap_result["payload_bits"] - hybrid_result["payload_bits"],
                }
            )

        oracle_candidates = sorted(
            diagnostic,
            key=lambda row: (row["hybrid_saving_bits"], -row["block_index"]),
            reverse=True,
        )
        oracle_selected = {
            int(row["block_index"])
            for row in oracle_candidates[: MAX_ADMITTED_BYTES // BLOCK_BYTES]
            if int(row["hybrid_saving_bits"]) > 0
        }
        oracle_bits = sum(
            int(row["hybrid_payload_bits"])
            if int(row["block_index"]) in oracle_selected
            else int(row["cheap_payload_bits"])
            for row in diagnostic
        )
        oracle_evals = sum(
            int(row["hybrid_model_evaluations"])
            for row in diagnostic
            if int(row["block_index"]) in oracle_selected
        )

        summaries = {int(row["block_index"]): row for row in p13["block_summary"]}
        for row in diagnostic:
            selected = summaries[int(row["block_index"])]
            holdout_block_rows.append(
                {
                    **row,
                    "p13_band_match": selected["band_match"],
                    "p13_budget_limited": selected["budget_limited"],
                    "p13_admitted": selected["admitted"],
                    "oracle_admitted": int(row["block_index"]) in oracle_selected,
                }
            )

        available_gain = cheap_reset["payload_bpb"] - neural_reset["payload_bpb"]
        retained_gain = (
            (cheap_reset["payload_bpb"] - p13["payload_bpb"]) / available_gain
            if available_gain > 0
            else 0.0
        )
        row = {
            "stream": stream_name,
            "sample_bytes": len(data),
            "cheap_reset_bpb": cheap_reset["payload_bpb"],
            "neural_reset_bpb": neural_reset["payload_bpb"],
            "neural_reset_model_eval_fraction": neural_reset["model_eval_fraction"],
            "p12_max_bpb": p12_max["payload_bpb"],
            "p12_max_model_eval_fraction": p12_max["model_eval_fraction"],
            "p12_max_specialist_call_fraction": p12_max["specialist_call_fraction"],
            "p13_bpb": p13["payload_bpb"],
            "p13_model_eval_fraction": p13["model_eval_fraction"],
            "p13_admitted_byte_fraction": p13["admitted_byte_fraction"],
            "p13_admitted_blocks": p13["admitted_blocks"],
            "p13_retained_gain_fraction": retained_gain,
            "oracle50_blocksum_bpb": oracle_bits / len(data),
            "oracle50_model_eval_fraction": oracle_evals / len(data),
            **base,
        }
        holdout_rows.append(row)
        print("HOLDOUT", stream_name, json.dumps(row, sort_keys=True), flush=True)

    aggregate = {
        "mean_cheap_reset_bpb": mean(row["cheap_reset_bpb"] for row in holdout_rows),
        "mean_neural_reset_bpb": mean(row["neural_reset_bpb"] for row in holdout_rows),
        "mean_p12_max_bpb": mean(row["p12_max_bpb"] for row in holdout_rows),
        "mean_p12_max_model_eval_fraction": mean(
            row["p12_max_model_eval_fraction"] for row in holdout_rows
        ),
        "mean_p12_max_specialist_call_fraction": mean(
            row["p12_max_specialist_call_fraction"] for row in holdout_rows
        ),
        "mean_p13_bpb": mean(row["p13_bpb"] for row in holdout_rows),
        "mean_p13_model_eval_fraction": mean(row["p13_model_eval_fraction"] for row in holdout_rows),
        "max_p13_model_eval_fraction": max(row["p13_model_eval_fraction"] for row in holdout_rows),
        "mean_p13_admitted_byte_fraction": mean(
            row["p13_admitted_byte_fraction"] for row in holdout_rows
        ),
        "mean_p13_retained_gain_fraction": mean(
            row["p13_retained_gain_fraction"] for row in holdout_rows
        ),
        "mean_oracle50_blocksum_bpb": mean(row["oracle50_blocksum_bpb"] for row in holdout_rows),
        "mean_zlib_bpb": mean(row["zlib_bpb"] for row in holdout_rows),
        "mean_zstd19_bpb": mean(row["zstd19_bpb"] for row in holdout_rows),
        "p13_beats_cheap_streams": sum(
            row["p13_bpb"] < row["cheap_reset_bpb"] for row in holdout_rows
        ),
        "p13_beats_p12_max_streams": sum(
            row["p13_bpb"] < row["p12_max_bpb"] for row in holdout_rows
        ),
    }
    aggregate["success"] = bool(
        aggregate["max_p13_model_eval_fraction"] <= 0.50 + 1e-12
        and aggregate["mean_p13_bpb"] < aggregate["mean_cheap_reset_bpb"]
        and aggregate["mean_p13_retained_gain_fraction"] >= RETAINED_GAIN_SUCCESS
    )

    results = {
        "experiment_id": "pilot-013-cheap-admission",
        "question": "Can cheap-only causal admission preserve useful block-reset neural compression under a hard 50% neural-forward budget?",
        "development": {
            "source": "reconstructed, already-consumed PILOT-012 holdout",
            "streams": list(dev_streams),
            "stream_bytes": STREAM_BYTES,
            "block_bytes": BLOCK_BYTES,
            "probe_candidates": list(PROBE_CANDIDATES),
            "lower_bpb_x2": list(LOWER_BPB_X2),
            "upper_bpb_x2": list(UPPER_BPB_X2),
            "validation_candidates": VALIDATION_CANDIDATES,
            "hard_max_admitted_bytes": MAX_ADMITTED_BYTES,
            "mean_retrospective_50pct_neural_reset_gain_retained": mean(oracle_retained),
            "selected_policy": frozen_params,
            "selected_validated_mean_payload_bpb": selected_policy["validated_mean_payload_bpb"],
            "selected_validated_mean_model_eval_fraction": selected_policy[
                "validated_mean_model_eval_fraction"
            ],
            "new_holdout_sources_opened_during_selection": False,
            "consumed_source_manifest": consumed_manifest,
        },
        "new_holdout": {
            "name": "PILOT-013 Go/Node mixed-source holdout",
            "streams": list(hold_streams),
            "external_sources": source_manifest,
            "aggregate": aggregate,
            "per_stream_table": "holdout.csv",
            "per_block_table": "holdout-blocks.csv",
            "composition_manifest": "holdout-manifest.json",
        },
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
            "block_bytes": BLOCK_BYTES,
            "hard_max_admitted_bytes": MAX_ADMITTED_BYTES,
            "hard_max_admitted_fraction": MAX_ADMITTED_BYTES / STREAM_BYTES,
            "primary_compute_metric": "uncached PyTorch model forward evaluations / source bytes",
            "policy_selection": "coarse cheap-codelength screen followed by real whole-stream range-coder validation",
            "retained_gain_success_threshold": RETAINED_GAIN_SUCCESS,
            "fresh_holdout_downloaded_only_after_policy_freeze": True,
        },
        "limits": [
            "The holdout is a deterministic mixed-domain mechanism benchmark, not a universal compression corpus.",
            "The admission feature is intentionally one-dimensional: cheap-gate probe codelength only.",
            "The 50% diagnostic oracle is non-causal and uses summed independently coded block payloads.",
            "The frozen neural checkpoint is assumed shared whenever the neural path is admitted.",
        ],
    }

    csvout(OUT / "development-blocks.csv", dev_block_rows)
    csvout(OUT / "development-candidates.csv", candidates)
    csvout(OUT / "development-validation.csv", validation_rows)
    csvout(OUT / "holdout.csv", holdout_rows)
    csvout(OUT / "holdout-blocks.csv", holdout_block_rows)
    (OUT / "holdout-manifest.json").write_text(
        json.dumps({"sources": source_manifest, "streams": composition_manifest}, indent=2) + "\n"
    )
    (OUT / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print("AGGREGATE", json.dumps(aggregate, sort_keys=True), flush=True)
    print("RESULTS", OUT / "results.json", flush=True)


if __name__ == "__main__":
    main()
