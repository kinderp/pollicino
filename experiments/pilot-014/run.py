from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
import zlib
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import mean
from typing import Callable

import numpy as np
import torch
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
sys.path.insert(0, str(ROOT / "src"))

from pollicino.compression.adaptive import (
    AdaptiveNGramCDFProvider,
    NeuralPriorAdaptiveCDFProvider,
    adaptive_fingerprint,
)
from pollicino.compression.admission_routing import (
    RICH_CHEAP_FEATURE_NAMES,
    RICH_CHEAP_FEATURE_VERSION,
    AdmissionBudgetState,
    CheapAdmissionDecisionTree,
    CheapAdmissionFeatures,
    CheapCodelengthAdmissionBlockCDFProvider,
    DecisionTreeNode,
    QuantizedLinearAdmissionRule,
    RichCheapAdmissionBlockCDFProvider,
    admission_rule_from_dict,
    cheap_codelength_admission_fingerprint,
    extract_cheap_admission_features,
    integer_admission_rule_feature_names,
    rich_cheap_admission_decision,
    rich_cheap_admission_fingerprint,
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


EXPERIMENT_ID = "pilot-014-rich-cheap-admission"
PREDECESSOR_COMMIT = "a07fc2166ca2806b514b2a0825a7f0fb07efca4e"
PREDECESSOR_RUN_HEAD = "ba6eb338d47ceaac170358c1f26ba6c5d5f4b4ff"
PRECISION = 18
STREAM_BYTES = 4096
BLOCK_BYTES = 512
PROBE_BYTES = 16
MAX_ADMITTED_BYTES = STREAM_BYTES // 2
RETAINED_GAIN_SUCCESS = 0.50
COMPLEXITY_TOLERANCE_BPB = 0.01
LINEAR_QUANTIZATION_SCALE = 256
VERY_SURPRISING_BITS = 9
CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)

FEATURE_SETS = {
    "compact6": (
        "probe_code_bits_ceil",
        "unique_count",
        "max_hist_count",
        "transition_count",
        "longest_run",
        "surprise_max_ceil",
    ),
    "all12": tuple(RICH_CHEAP_FEATURE_NAMES),
}
FEATURE_GROUPS = {
    "codelength": ("probe_code_bits_ceil",),
    "histogram": ("unique_count", "max_hist_count"),
    "repetition": ("longest_run",),
    "transition": ("transition_count", "distinct_transition_count"),
    "surprise_shape": (
        "surprise_sum_ceil",
        "surprise_max_ceil",
        "surprise_range_ceil",
        "surprise_variance_proxy",
        "surprise_early_minus_late",
        "very_surprising_count",
    ),
}
FIT_STREAMS = tuple(
    [f"p12-mix-{suffix}" for suffix in "abcd"]
    + [f"p13-mix-{suffix}" for suffix in "abcd"]
)
VALIDATION_STREAMS = tuple(
    [f"p12-mix-{suffix}" for suffix in "ef"]
    + [f"p13-mix-{suffix}" for suffix in "ef"]
)

CONSUMED_SOURCES = {
    "cpython-json-decoder": {
        "url": "https://raw.githubusercontent.com/python/cpython/v3.11.15/Lib/json/decoder.py",
        "git_blob_sha1": "c5d9ae2d0d5d040708f097fbf6450b86eef334dd",
    },
    "linux-sched-core": {
        "url": "https://raw.githubusercontent.com/torvalds/linux/v6.6/kernel/sched/core.c",
        "git_blob_sha1": "802551e0009bf1ef66191441a802633bb57543bc",
    },
    "go-http-server": {
        "url": "https://raw.githubusercontent.com/golang/go/go1.22.12/src/net/http/server.go",
        "git_blob_sha1": "23a603a83dd7135077fa1363ceb8255ff345ac06",
    },
    "node-cjs-loader": {
        "url": "https://raw.githubusercontent.com/nodejs/node/v20.19.1/lib/internal/modules/cjs/loader.js",
        "git_blob_sha1": "ebccdb28256314e7cd8ac8d7e3dec670286022d2",
    },
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def current_git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def payload_bits(info: dict, source_bytes: int) -> int:
    return round(float(info["payload_bpb"]) * source_bytes)


def reset_fingerprint(base_fp: bytes, stream_bytes: int, label: str) -> bytes:
    payload = (
        b"p14-block-reset-v1\0"
        + label.encode()
        + base_fp
        + stream_bytes.to_bytes(8, "big")
        + BLOCK_BYTES.to_bytes(4, "big")
    )
    return hashlib.sha256(payload).digest()


def download_verified_sources(
    specs: dict[str, dict], *, user_agent: str
) -> tuple[dict[str, bytes], list[dict]]:
    sources: dict[str, bytes] = {}
    manifest: list[dict] = []
    for name, metadata in specs.items():
        request = urllib.request.Request(
            metadata["url"], headers={"User-Agent": user_agent}
        )
        data = urllib.request.urlopen(request, timeout=120).read()
        observed_blob = git_blob_sha1(data)
        if observed_blob != metadata["git_blob_sha1"]:
            raise RuntimeError(
                f"{name}: HOLDOUT_PROVENANCE_ERROR git blob mismatch "
                f"{observed_blob} != {metadata['git_blob_sha1']}"
            )
        expected_size = metadata.get("expected_bytes")
        if expected_size is not None and len(data) != int(expected_size):
            raise RuntimeError(f"{name}: HOLDOUT_PROVENANCE_ERROR byte-size mismatch")
        expected_sha = metadata.get("expected_sha256")
        if expected_sha is not None and sha256(data) != expected_sha:
            raise RuntimeError(f"{name}: HOLDOUT_PROVENANCE_ERROR SHA-256 mismatch")
        sources[name] = data
        manifest.append(
            {
                "name": name,
                "repository": metadata.get("repository"),
                "revision": metadata.get("revision"),
                "path": metadata.get("path"),
                "url": metadata["url"],
                "git_blob_sha1": observed_blob,
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    return sources, manifest


@dataclass
class CodecContext:
    model: object
    spec: object
    checkpoint: dict
    cheap_factory: Callable[[], object]
    cheap_fp: bytes
    neural_gate_fp: bytes
    max_policy: dict
    p12: object


class TrackingNeuralFactory:
    def __init__(self, context: CodecContext):
        self.context = context
        self.priors: list[PyTorchCDFProvider] = []

    def __call__(self):
        context = self.context
        shared_prior = PyTorchCDFProvider(
            context.model, context.spec, precision_bits=PRECISION, device="cpu"
        )
        self.priors.append(shared_prior)
        p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
        neural_window = int(p7_results["neural_gate"]["window"])
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


def load_context() -> CodecContext:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    p9exact = load_module(ROOT / "experiments/pilot-009/exact_checkpoint.py", "pilot009_exact_for_p14")
    p12 = load_module(ROOT / "experiments/pilot-012/run.py", "pilot012_for_p14")
    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())
    p11_results = json.loads((ROOT / "experiments/pilot-011/results.json").read_text())
    p12_results = json.loads((ROOT / "experiments/pilot-012/results.json").read_text())

    model, spec, checkpoint = p9exact.load_exact_checkpoint()
    neural_fp = torch_model_fingerprint(model, spec)
    if neural_fp.hex() != p12_results["model"]["canonical_neural_fingerprint"]:
        raise RuntimeError("exact frozen checkpoint fingerprint mismatch")

    adaptive_cfgs = {
        "adaptive-o0": dict(max_order=0, order_weights=(1,), base_count=1),
        "adaptive-o1": dict(max_order=1, order_weights=(1, 4), base_count=1),
        "adaptive-o2": dict(max_order=2, order_weights=(1, 4, 16), base_count=1),
        "adaptive-o3": ADAPTIVE_CFG,
    }
    cheap_window = int(p7_results["cheap_gate"]["selected_window"])

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

    cheap_fps = [adaptive_fingerprint(**adaptive_cfgs[name]) for name in CHEAP_NAMES[:-1]] + [
        run_length_fingerprint(run_weight=64)
    ]
    cheap_fp = expert_gate_fingerprint(
        expert_fingerprints=cheap_fps, names=CHEAP_NAMES, window=cheap_window
    )
    adaptive_fp = adaptive_fingerprint(**ADAPTIVE_CFG)
    neural_fps = (
        adaptive_fp,
        neural_fp,
        adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=256, neural_fingerprint=neural_fp),
        adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=1024, neural_fingerprint=neural_fp),
    )
    neural_window = int(p7_results["neural_gate"]["window"])
    neural_gate_fp = expert_gate_fingerprint(
        expert_fingerprints=neural_fps, names=NEURAL_NAMES, window=neural_window
    )
    return CodecContext(
        model=model,
        spec=spec,
        checkpoint={
            **checkpoint,
            "canonical_model_fingerprint": neural_fp.hex(),
        },
        cheap_factory=cheap_factory,
        cheap_fp=cheap_fp,
        neural_gate_fp=neural_gate_fp,
        max_policy=p11_results["development"]["selected_modes"]["max"],
        p12=p12,
    )


def encode_only(data: bytes, provider, fingerprint: bytes) -> dict:
    started = time.perf_counter()
    blob = encode_shared(data, provider, fingerprint, precision_bits=PRECISION)
    elapsed = time.perf_counter() - started
    info = inspect_pol(blob)
    return {
        "blob": blob,
        "payload_bits": payload_bits(info, len(data)),
        "payload_bpb": float(info["payload_bpb"]),
        "pol1_bpb": float(info["realized_bpb"]),
        "encode_seconds": elapsed,
    }


def rich_fingerprint(context: CodecContext, rule, stream_bytes: int) -> bytes:
    return rich_cheap_admission_fingerprint(
        cheap_fingerprint=context.cheap_fp,
        specialist_fingerprint=context.neural_gate_fp,
        stream_bytes=stream_bytes,
        block_bytes=BLOCK_BYTES,
        probe_bytes=PROBE_BYTES,
        rule=rule,
        max_admitted_bytes=min(MAX_ADMITTED_BYTES, stream_bytes),
    )


def run_rich(context: CodecContext, data: bytes, rule, *, verify: bool) -> dict:
    enc_tracker = TrackingNeuralFactory(context)
    enc_provider = RichCheapAdmissionBlockCDFProvider(
        context.cheap_factory,
        enc_tracker,
        rule,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        probe_bytes=PROBE_BYTES,
        max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
        cheap_name="cheap-gate",
        specialist_name="neural-gate",
    )
    fingerprint = rich_fingerprint(context, rule, len(data))
    encoded = encode_only(data, enc_provider, fingerprint)
    result = {
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
        dec_tracker = TrackingNeuralFactory(context)
        dec_provider = RichCheapAdmissionBlockCDFProvider(
            context.cheap_factory,
            dec_tracker,
            rule,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            probe_bytes=PROBE_BYTES,
            max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
            cheap_name="cheap-gate",
            specialist_name="neural-gate",
        )
        restored = decode_pol(
            encoded["blob"],
            shared_provider=dec_provider,
            expected_model_fingerprint=fingerprint,
        )
        result["roundtrip"] = restored == data
        result["sha256_match"] = sha256(restored) == sha256(data)
        if not result["roundtrip"] or not result["sha256_match"]:
            raise RuntimeError("PILOT-014 exact roundtrip failed")
        if enc_provider.block_summary() != dec_provider.block_summary():
            raise RuntimeError("SEARCH_CODEC_DECISION_DIVERGENCE between encoder and decoder")
        if enc_tracker.model_evaluations != dec_tracker.model_evaluations:
            raise RuntimeError("encoder/decoder neural evaluation counts diverged")
    return result


def p13_fingerprint(context: CodecContext, stream_bytes: int) -> bytes:
    return cheap_codelength_admission_fingerprint(
        cheap_fingerprint=context.cheap_fp,
        specialist_fingerprint=context.neural_gate_fp,
        stream_bytes=stream_bytes,
        block_bytes=BLOCK_BYTES,
        probe_bytes=PROBE_BYTES,
        min_probe_code_bits=88,
        max_probe_code_bits=128,
        max_admitted_bytes=min(MAX_ADMITTED_BYTES, stream_bytes),
    )


def run_p13(context: CodecContext, data: bytes, *, verify: bool) -> dict:
    tracker = TrackingNeuralFactory(context)
    provider = CheapCodelengthAdmissionBlockCDFProvider(
        context.cheap_factory,
        tracker,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        probe_bytes=PROBE_BYTES,
        min_probe_code_bits=88,
        max_probe_code_bits=128,
        max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
        cheap_name="cheap-gate",
        specialist_name="neural-gate",
    )
    fingerprint = p13_fingerprint(context, len(data))
    encoded = encode_only(data, provider, fingerprint)
    result = {
        **{key: value for key, value in encoded.items() if key != "blob"},
        "model_evaluations": tracker.model_evaluations,
        "model_eval_fraction": tracker.model_evaluations / len(data),
        "admitted_blocks": provider.admitted_blocks,
        "admitted_bytes": provider.admitted_bytes,
        "block_summary": provider.block_summary(),
    }
    if verify:
        dec_tracker = TrackingNeuralFactory(context)
        decoder = CheapCodelengthAdmissionBlockCDFProvider(
            context.cheap_factory,
            dec_tracker,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            probe_bytes=PROBE_BYTES,
            min_probe_code_bits=88,
            max_probe_code_bits=128,
            max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
            cheap_name="cheap-gate",
            specialist_name="neural-gate",
        )
        restored = decode_pol(encoded["blob"], shared_provider=decoder, expected_model_fingerprint=fingerprint)
        if restored != data or provider.block_summary() != decoder.block_summary():
            raise RuntimeError("PILOT-013 comparison roundtrip failed")
    return result


def reset_roundtrip(context: CodecContext, data: bytes, *, neural: bool) -> dict:
    tracker = TrackingNeuralFactory(context) if neural else None
    base_factory = tracker if neural else context.cheap_factory
    base_fp = context.neural_gate_fp if neural else context.cheap_fp
    provider = BlockResetCDFProvider(base_factory, stream_bytes=len(data), block_bytes=BLOCK_BYTES)
    fingerprint = reset_fingerprint(base_fp, len(data), "neural" if neural else "cheap")
    encoded = encode_only(data, provider, fingerprint)
    dec_tracker = TrackingNeuralFactory(context) if neural else None
    decoder = BlockResetCDFProvider(
        dec_tracker if neural else context.cheap_factory,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
    )
    restored = decode_pol(encoded["blob"], shared_provider=decoder, expected_model_fingerprint=fingerprint)
    if restored != data or sha256(restored) != sha256(data):
        raise RuntimeError("block-reset baseline roundtrip failed")
    return {
        "payload_bits": encoded["payload_bits"],
        "payload_bpb": encoded["payload_bpb"],
        "model_evaluations": tracker.model_evaluations if tracker else 0,
        "model_eval_fraction": tracker.model_evaluations / len(data) if tracker else 0.0,
    }


def p12_max_roundtrip(context: CodecContext, data: bytes) -> dict:
    policy = context.max_policy
    tracker = TrackingNeuralFactory(context)
    provider = BlockLocalBitCreditRouterCDFProvider(
        context.cheap_factory,
        tracker,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        min_observations=int(policy["min_observations"]),
        max_probe_bytes=int(policy["max_probe_bytes"]),
        activation_credit_bits=int(policy["activation_credit_bits"]),
        rejection_credit_bits=int(policy["rejection_credit_bits"]),
        cheap_name="cheap-gate",
        specialist_name="neural-gate",
    )
    fingerprint = block_local_router_fingerprint(
        cheap_fingerprint=context.cheap_fp,
        specialist_fingerprint=context.neural_gate_fp,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        min_observations=int(policy["min_observations"]),
        max_probe_bytes=int(policy["max_probe_bytes"]),
        activation_credit_bits=int(policy["activation_credit_bits"]),
        rejection_credit_bits=int(policy["rejection_credit_bits"]),
    )
    encoded = encode_only(data, provider, fingerprint)
    dec_tracker = TrackingNeuralFactory(context)
    decoder = BlockLocalBitCreditRouterCDFProvider(
        context.cheap_factory,
        dec_tracker,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        min_observations=int(policy["min_observations"]),
        max_probe_bytes=int(policy["max_probe_bytes"]),
        activation_credit_bits=int(policy["activation_credit_bits"]),
        rejection_credit_bits=int(policy["rejection_credit_bits"]),
        cheap_name="cheap-gate",
        specialist_name="neural-gate",
    )
    restored = decode_pol(encoded["blob"], shared_provider=decoder, expected_model_fingerprint=fingerprint)
    if restored != data or provider.block_summary() != decoder.block_summary():
        raise RuntimeError("PILOT-012 comparison roundtrip failed")
    return {
        "payload_bpb": encoded["payload_bpb"],
        "model_evaluations": tracker.model_evaluations,
        "model_eval_fraction": tracker.model_evaluations / len(data),
        "specialist_call_fraction": provider.compute_fraction,
    }


def classical_baselines(data: bytes) -> dict[str, float]:
    return {
        "zlib_bpb": len(zlib.compress(data, 9)) * 8 / len(data),
        "zstd19_bpb": len(zstd.ZstdCompressor(level=19).compress(data)) * 8 / len(data),
    }


def make_development_streams(context: CodecContext) -> tuple[dict[str, bytes], list[dict]]:
    consumed, manifest = download_verified_sources(
        CONSUMED_SOURCES, user_agent="POLLICINO-PILOT-014-DEVELOPMENT/1.0"
    )
    p12 = context.p12
    components = {
        "cpython": consumed["cpython-json-decoder"],
        "linux": consumed["linux-sched-core"],
        "go": consumed["go-http-server"],
        "node": consumed["node-cjs-loader"],
        "json12": p12.json_bytes(STREAM_BYTES, 2201),
        "dna12": p12.dna_bytes(STREAM_BYTES, 2202),
        "random64_12": p12.random_bytes(STREAM_BYTES, 2203, 64),
        "random256_12": p12.random_bytes(STREAM_BYTES, 2204, 256),
        "repeat12": p12.cycle(b"POLLICINO-POLLICINO-", STREAM_BYTES),
        "compressed12": p12.compressed_bytes(STREAM_BYTES, 2205),
        "english12": p12.english_bytes(STREAM_BYTES),
        "json13": p12.json_bytes(STREAM_BYTES, 3301),
        "dna13": p12.dna_bytes(STREAM_BYTES, 3302),
        "random64_13": p12.random_bytes(STREAM_BYTES, 3303, 64),
        "random256_13": p12.random_bytes(STREAM_BYTES, 3304, 256),
        "repeat13": p12.cycle(b"admit-cheap-or-neural-", STREAM_BYTES),
        "compressed13": p12.compressed_bytes(STREAM_BYTES, 3305),
        "english13": p12.english_bytes(STREAM_BYTES),
    }
    recipes = {
        "p12-mix-a": [("cpython", 851), ("random256_12", 457), ("linux", 1099), ("repeat12", 389), ("json12", -1)],
        "p12-mix-b": [("linux", 727), ("dna12", 901), ("cpython", 1027), ("compressed12", -1)],
        "p12-mix-c": [("english12", 667), ("cpython", 947), ("random64_12", 557), ("linux", -1)],
        "p12-mix-d": [("json12", 877), ("linux", 823), ("repeat12", 353), ("compressed12", 701), ("cpython", -1)],
        "p12-mix-e": [("random256_12", 499), ("cpython", 1157), ("dna12", 751), ("linux", -1)],
        "p12-mix-f": [("cpython", 461), ("repeat12", 607), ("linux", 443), ("random256_12", 719), ("json12", -1)],
        "p13-mix-a": [("go", 811), ("random256_13", 503), ("node", 1109), ("repeat13", 421), ("json13", -1)],
        "p13-mix-b": [("node", 727), ("dna13", 933), ("go", 1001), ("compressed13", -1)],
        "p13-mix-c": [("english13", 689), ("go", 971), ("random64_13", 541), ("node", -1)],
        "p13-mix-d": [("json13", 893), ("node", 809), ("repeat13", 371), ("compressed13", 683), ("go", -1)],
        "p13-mix-e": [("random256_13", 487), ("node", 1169), ("dna13", 769), ("go", -1)],
        "p13-mix-f": [("go", 479), ("repeat13", 593), ("node", 457), ("random256_13", 733), ("json13", -1)],
    }
    return {
        name: p12.compose(components, recipe)[0] for name, recipe in recipes.items()
    }, manifest


ALWAYS_ADMIT_RULE = QuantizedLinearAdmissionRule(
    ("unique_count",), (0,), bias=1, threshold=0
)
ALWAYS_CHEAP_RULE = QuantizedLinearAdmissionRule(
    ("unique_count",), (0,), bias=0, threshold=1
)


def precompute_blocks(
    context: CodecContext, streams: dict[str, bytes], *, progress_label: str
) -> list[dict]:
    rows: list[dict] = []
    for stream_name, data in streams.items():
        for block_index, start in enumerate(range(0, len(data), BLOCK_BYTES)):
            block = data[start : start + BLOCK_BYTES]
            features = extract_cheap_admission_features(
                context.cheap_factory, block[:PROBE_BYTES]
            )
            cheap = encode_only(block, context.cheap_factory(), context.cheap_fp)
            neural_tracker = TrackingNeuralFactory(context)
            neural = encode_only(block, neural_tracker(), context.neural_gate_fp)
            forced = run_rich(context, block, ALWAYS_ADMIT_RULE, verify=False)
            if forced["admitted_blocks"] != 1:
                raise RuntimeError("forced rich development route did not admit")
            rows.append(
                {
                    "stream": stream_name,
                    "block_index": block_index,
                    "start": start,
                    "bytes": len(block),
                    **features.as_dict(),
                    "cheap_payload_bits": cheap["payload_bits"],
                    "neural_payload_bits": neural["payload_bits"],
                    "neural_model_evaluations": neural_tracker.model_evaluations,
                    "hybrid_payload_bits": forced["payload_bits"],
                    "hybrid_model_evaluations": forced["model_evaluations"],
                    "hybrid_saving_bits": cheap["payload_bits"] - forced["payload_bits"],
                }
            )
        print(progress_label, stream_name, flush=True)
    return rows


def features_from_row(row: dict) -> CheapAdmissionFeatures:
    return CheapAdmissionFeatures(
        probe_code_bits_floor=int(row["probe_code_bits_floor"]),
        **{name: int(row[name]) for name in RICH_CHEAP_FEATURE_NAMES},
    )


def with_threshold(rule, threshold: int):
    return replace(rule, threshold=int(threshold))


def prune_tree_to_binary_decision(
    rule: CheapAdmissionDecisionTree,
) -> CheapAdmissionDecisionTree:
    def nested(index: int):
        node = rule.nodes[index]
        if node.value is not None:
            return {"value": int(node.value >= rule.threshold)}
        assert node.less_equal is not None and node.greater is not None
        less_equal = nested(node.less_equal)
        greater = nested(node.greater)
        if less_equal == greater:
            return less_equal
        return {
            "feature": node.feature,
            "threshold": node.threshold,
            "less_equal": less_equal,
            "greater": greater,
        }

    compact = nested(0)
    nodes: list[DecisionTreeNode | None] = []

    def emit(node: dict) -> int:
        index = len(nodes)
        nodes.append(None)
        if "value" in node:
            nodes[index] = DecisionTreeNode(value=int(node["value"]))
        else:
            less_equal = emit(node["less_equal"])
            greater = emit(node["greater"])
            nodes[index] = DecisionTreeNode(
                feature=str(node["feature"]),
                threshold=int(node["threshold"]),
                less_equal=less_equal,
                greater=greater,
            )
        return index

    emit(compact)
    return CheapAdmissionDecisionTree(
        tuple(node for node in nodes if node is not None), threshold=1
    )


def simulate_rule(block_rows: list[dict], stream_names: tuple[str, ...], rule) -> dict:
    total_bits = 0
    total_evals = 0
    total_bytes = 0
    admitted_bytes = 0
    admitted_blocks = 0
    route_rows: list[dict] = []
    for stream_name in stream_names:
        spent = 0
        rows = sorted(
            (row for row in block_rows if row["stream"] == stream_name),
            key=lambda row: int(row["block_index"]),
        )
        for row in rows:
            decision = rich_cheap_admission_decision(
                features_from_row(row),
                rule,
                AdmissionBudgetState(spent, MAX_ADMITTED_BYTES),
                int(row["bytes"]),
            )
            if decision.admitted:
                spent += int(row["bytes"])
                admitted_bytes += int(row["bytes"])
                admitted_blocks += 1
                total_bits += int(row["hybrid_payload_bits"])
                total_evals += int(row["hybrid_model_evaluations"])
            else:
                total_bits += int(row["cheap_payload_bits"])
            total_bytes += int(row["bytes"])
            route_rows.append(
                {
                    "stream": stream_name,
                    "block_index": int(row["block_index"]),
                    "score": decision.score,
                    "admitted": decision.admitted,
                }
            )
    return {
        "payload_bpb": total_bits / total_bytes,
        "model_eval_fraction": total_evals / total_bytes,
        "admitted_byte_fraction": admitted_bytes / total_bytes,
        "admitted_blocks": admitted_blocks,
        "routes": route_rows,
    }


def optimize_threshold(block_rows: list[dict], stream_names: tuple[str, ...], rule):
    scores = sorted(
        {int(rule.score(features_from_row(row))) for row in block_rows if row["stream"] in stream_names}
    )
    candidates = [scores[0] - 1, *scores, scores[-1] + 1]
    evaluated = []
    for threshold in candidates:
        candidate_rule = with_threshold(rule, threshold)
        metrics = simulate_rule(block_rows, stream_names, candidate_rule)
        evaluated.append((metrics["payload_bpb"], metrics["model_eval_fraction"], -threshold, candidate_rule, metrics))
    _, _, _, selected, metrics = min(evaluated, key=lambda item: item[:3])
    if isinstance(selected, CheapAdmissionDecisionTree):
        selected = prune_tree_to_binary_decision(selected)
    return selected, metrics


def fit_linear_rule(
    rows: list[dict], feature_names: tuple[str, ...], ridge: float
) -> tuple[QuantizedLinearAdmissionRule, dict]:
    matrix = np.asarray([[float(row[name]) for name in feature_names] for row in rows])
    target = np.asarray([float(row["hybrid_saving_bits"]) for row in rows])
    centers = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales == 0] = 1.0
    standardized = (matrix - centers) / scales
    design = np.column_stack((np.ones(len(rows)), standardized))
    penalty = np.eye(design.shape[1]) * float(ridge)
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ target)
    raw_weights = coefficients[1:] / scales
    raw_bias = coefficients[0] - float(np.dot(coefficients[1:], centers / scales))
    weights = tuple(int(round(value * LINEAR_QUANTIZATION_SCALE)) for value in raw_weights)
    bias = int(round(raw_bias * LINEAR_QUANTIZATION_SCALE))
    return (
        QuantizedLinearAdmissionRule(feature_names, weights, bias=bias, threshold=0),
        {
            "ridge": ridge,
            "quantization_scale": LINEAR_QUANTIZATION_SCALE,
            "float_raw_weights": [float(value) for value in raw_weights],
            "float_raw_bias": raw_bias,
        },
    )


def fit_tree_rule(
    rows: list[dict], feature_names: tuple[str, ...], max_depth: int, min_leaf: int
) -> CheapAdmissionDecisionTree:
    def squared_error(indices: list[int]) -> float:
        values = [float(rows[index]["hybrid_saving_bits"]) for index in indices]
        average = mean(values)
        return sum((value - average) ** 2 for value in values)

    def build(indices: list[int], depth: int):
        leaf_value = int(round(mean(float(rows[index]["hybrid_saving_bits"]) for index in indices)))
        if depth >= max_depth or len(indices) < 2 * min_leaf:
            return {"value": leaf_value}
        best = None
        for feature_position, feature in enumerate(feature_names):
            values = sorted({int(rows[index][feature]) for index in indices})
            for threshold in values[:-1]:
                less_equal = [index for index in indices if int(rows[index][feature]) <= threshold]
                greater = [index for index in indices if int(rows[index][feature]) > threshold]
                if len(less_equal) < min_leaf or len(greater) < min_leaf:
                    continue
                error = squared_error(less_equal) + squared_error(greater)
                key = (error, feature_position, threshold)
                if best is None or key < best[0]:
                    best = (key, feature, threshold, less_equal, greater)
        if best is None:
            return {"value": leaf_value}
        _, feature, threshold, less_equal, greater = best
        return {
            "feature": feature,
            "threshold": threshold,
            "less_equal": build(less_equal, depth + 1),
            "greater": build(greater, depth + 1),
        }

    nested = build(list(range(len(rows))), 0)
    nodes: list[DecisionTreeNode | None] = []

    def emit(node: dict) -> int:
        index = len(nodes)
        nodes.append(None)
        if "value" in node:
            nodes[index] = DecisionTreeNode(value=int(node["value"]))
        else:
            less_equal = emit(node["less_equal"])
            greater = emit(node["greater"])
            nodes[index] = DecisionTreeNode(
                feature=str(node["feature"]),
                threshold=int(node["threshold"]),
                less_equal=less_equal,
                greater=greater,
            )
        return index

    emit(nested)
    return CheapAdmissionDecisionTree(tuple(node for node in nodes if node is not None), threshold=0)


def deployed_feature_count(rule) -> int:
    if isinstance(rule, QuantizedLinearAdmissionRule):
        return len(rule.feature_names)
    return len(
        {
            node.feature
            for node in rule.nodes
            if node.feature is not None
        }
    )


def deployed_complexity(rule) -> int:
    if isinstance(rule, QuantizedLinearAdmissionRule):
        return len(rule.weights)
    return len(rule.nodes)


def search_codec_mismatches(
    context: CodecContext,
    streams: dict[str, bytes],
    block_rows: list[dict],
    stream_names: tuple[str, ...],
    rule,
) -> tuple[int, dict[str, dict]]:
    simulation = simulate_rule(block_rows, stream_names, rule)
    expected = {
        (row["stream"], int(row["block_index"])): bool(row["admitted"])
        for row in simulation["routes"]
    }
    mismatches = 0
    actual_results: dict[str, dict] = {}
    for stream_name in stream_names:
        actual = run_rich(context, streams[stream_name], rule, verify=True)
        actual_results[stream_name] = actual
        for summary in actual["block_summary"]:
            if bool(summary["admitted"]) != expected[(stream_name, int(summary["block_index"]))]:
                mismatches += 1
    return mismatches, actual_results


def feature_diagnostics(block_rows: list[dict]) -> dict:
    target = np.asarray([float(row["hybrid_saving_bits"]) for row in block_rows])
    output = {}
    for name in RICH_CHEAP_FEATURE_NAMES:
        values = np.asarray([float(row[name]) for row in block_rows])
        if float(values.std()) == 0.0 or float(target.std()) == 0.0:
            correlation = 0.0
        else:
            correlation = float(np.corrcoef(values, target)[0, 1])
        output[name] = {
            "min": int(values.min()),
            "max": int(values.max()),
            "mean": float(values.mean()),
            "pearson_correlation_with_hybrid_saving_bits": correlation,
        }
    return output


def candidate_rules(block_rows: list[dict]) -> list[dict]:
    fit_rows = [row for row in block_rows if row["stream"] in FIT_STREAMS]
    candidates: list[dict] = []
    for feature_set_name, feature_names in FEATURE_SETS.items():
        for max_depth in (2, 3):
            for min_leaf in (4, 8):
                raw_rule = fit_tree_rule(fit_rows, feature_names, max_depth, min_leaf)
                rule, fit_metrics = optimize_threshold(block_rows, FIT_STREAMS, raw_rule)
                validation_metrics = simulate_rule(block_rows, VALIDATION_STREAMS, rule)
                candidates.append(
                    {
                        "candidate_id": f"tree-{feature_set_name}-d{max_depth}-l{min_leaf}",
                        "family": "decision-tree",
                        "feature_set": feature_set_name,
                        "feature_names": list(feature_names),
                        "max_depth": max_depth,
                        "min_leaf": min_leaf,
                        "rule": rule,
                        "fit_simulated_payload_bpb": fit_metrics["payload_bpb"],
                        "fit_simulated_model_eval_fraction": fit_metrics["model_eval_fraction"],
                        "validation_simulated_payload_bpb": validation_metrics["payload_bpb"],
                        "validation_simulated_model_eval_fraction": validation_metrics["model_eval_fraction"],
                    }
                )
        for ridge in (1.0, 10.0):
            raw_rule, offline = fit_linear_rule(fit_rows, feature_names, ridge)
            rule, fit_metrics = optimize_threshold(block_rows, FIT_STREAMS, raw_rule)
            validation_metrics = simulate_rule(block_rows, VALIDATION_STREAMS, rule)
            float_scores = {
                (row["stream"], int(row["block_index"])): (
                    offline["float_raw_bias"]
                    + sum(
                        weight * float(row[name])
                        for name, weight in zip(
                            feature_names, offline["float_raw_weights"], strict=True
                        )
                    )
                )
                for row in block_rows
                if row["stream"] in FIT_STREAMS + VALIDATION_STREAMS
            }
            quant_routes = simulate_rule(block_rows, FIT_STREAMS + VALIDATION_STREAMS, rule)[
                "routes"
            ]
            float_threshold = rule.threshold / LINEAR_QUANTIZATION_SCALE
            float_mismatches = 0
            for stream_name in FIT_STREAMS + VALIDATION_STREAMS:
                float_spent = 0
                for route in (
                    row for row in quant_routes if row["stream"] == stream_name
                ):
                    float_match = (
                        float_scores[(stream_name, route["block_index"])] >= float_threshold
                    )
                    float_admitted = float_match and float_spent + BLOCK_BYTES <= MAX_ADMITTED_BYTES
                    if float_admitted:
                        float_spent += BLOCK_BYTES
                    float_mismatches += float_admitted != bool(route["admitted"])
            candidates.append(
                {
                    "candidate_id": f"linear-{feature_set_name}-r{int(ridge)}",
                    "family": "quantized-linear",
                    "feature_set": feature_set_name,
                    "feature_names": list(feature_names),
                    "ridge": ridge,
                    "quantization_scale": LINEAR_QUANTIZATION_SCALE,
                    "float_vs_deployed_route_mismatches": float_mismatches,
                    "rule": rule,
                    "fit_simulated_payload_bpb": fit_metrics["payload_bpb"],
                    "fit_simulated_model_eval_fraction": fit_metrics["model_eval_fraction"],
                    "validation_simulated_payload_bpb": validation_metrics["payload_bpb"],
                    "validation_simulated_model_eval_fraction": validation_metrics["model_eval_fraction"],
                }
            )
    return candidates


def p13_development_baseline(block_rows: list[dict]) -> dict:
    total_bits = 0
    total_bytes = 0
    total_evals = 0
    admitted_blocks = 0
    for stream_name in VALIDATION_STREAMS:
        spent = 0
        rows = sorted(
            (row for row in block_rows if row["stream"] == stream_name),
            key=lambda row: int(row["block_index"]),
        )
        for row in rows:
            match = int(row["probe_code_bits_floor"]) >= 88 and int(row["probe_code_bits_ceil"]) <= 128
            admit = match and spent + int(row["bytes"]) <= MAX_ADMITTED_BYTES
            if admit:
                spent += int(row["bytes"])
                admitted_blocks += 1
                total_bits += int(row["hybrid_payload_bits"])
                total_evals += int(row["hybrid_model_evaluations"])
            else:
                total_bits += int(row["cheap_payload_bits"])
            total_bytes += int(row["bytes"])
    return {
        "simulated_payload_bpb": total_bits / total_bytes,
        "simulated_model_eval_fraction": total_evals / total_bytes,
        "admitted_blocks": admitted_blocks,
    }


def run_ablation(block_rows: list[dict], selected: dict) -> list[dict]:
    base_names = integer_admission_rule_feature_names(selected["rule"])
    fit_rows = [row for row in block_rows if row["stream"] in FIT_STREAMS]
    rows = []
    configurations = [("all_features", base_names)]
    for group_name, group_features in FEATURE_GROUPS.items():
        kept = tuple(name for name in base_names if name not in group_features)
        if kept != base_names:
            configurations.append((f"minus_{group_name}", kept))
    for label, names in configurations:
        if not names:
            rule = ALWAYS_CHEAP_RULE
            fit_metrics = simulate_rule(block_rows, FIT_STREAMS, rule)
            validation = simulate_rule(block_rows, VALIDATION_STREAMS, rule)
            rows.append(
                {
                    "ablation": label,
                    "feature_count": 0,
                    "features": "",
                    "fit_payload_bpb": fit_metrics["payload_bpb"],
                    "validation_payload_bpb": validation["payload_bpb"],
                    "validation_model_eval_fraction": validation["model_eval_fraction"],
                }
            )
            continue
        if selected["family"] == "decision-tree":
            raw_rule = fit_tree_rule(
                fit_rows, names, int(selected["max_depth"]), int(selected["min_leaf"])
            )
        else:
            raw_rule, _ = fit_linear_rule(fit_rows, names, float(selected["ridge"]))
        rule, fit_metrics = optimize_threshold(block_rows, FIT_STREAMS, raw_rule)
        validation = simulate_rule(block_rows, VALIDATION_STREAMS, rule)
        rows.append(
            {
                "ablation": label,
                "feature_count": len(names),
                "features": ",".join(names),
                "fit_payload_bpb": fit_metrics["payload_bpb"],
                "validation_payload_bpb": validation["payload_bpb"],
                "validation_model_eval_fraction": validation["model_eval_fraction"],
            }
        )
    return rows


def development_reproduction_record(summary: dict) -> dict:
    return {
        "selected_candidate_id": summary["selected_candidate_id"],
        "selected_rule": summary["selected_rule"],
        "validation_actual_mean_payload_bpb": summary["validation_actual_mean_payload_bpb"],
        "validation_actual_mean_model_eval_fraction": summary[
            "validation_actual_mean_model_eval_fraction"
        ],
        "search_codec_decision_mismatches": summary["search_codec_decision_mismatches"],
        "development_block_count": summary["development_block_count"],
        "development_rows_digest": summary["development_rows_digest"],
    }


def run_development(context: CodecContext, *, write_outputs: bool = True) -> dict:
    streams, source_manifest = make_development_streams(context)
    block_rows = precompute_blocks(context, streams, progress_label="DEVELOPMENT_PRECOMPUTED")
    candidates = candidate_rules(block_rows)

    # Actual codec validation for every small candidate. This is the selection
    # quantity; independently summed block payload is screening/diagnostic only.
    for candidate in candidates:
        mismatches, actual = search_codec_mismatches(
            context,
            streams,
            block_rows,
            VALIDATION_STREAMS,
            candidate["rule"],
        )
        candidate["search_codec_decision_mismatches"] = mismatches
        candidate["validation_actual_mean_payload_bpb"] = mean(
            result["payload_bpb"] for result in actual.values()
        )
        candidate["validation_actual_mean_model_eval_fraction"] = mean(
            result["model_eval_fraction"] for result in actual.values()
        )
        candidate["validation_actual_max_model_eval_fraction"] = max(
            result["model_eval_fraction"] for result in actual.values()
        )
        candidate["deployed_feature_count"] = deployed_feature_count(candidate["rule"])
        candidate["deployed_complexity"] = deployed_complexity(candidate["rule"])
        print(
            "DEVELOPMENT_CANDIDATE",
            candidate["candidate_id"],
            candidate["validation_actual_mean_payload_bpb"],
            flush=True,
        )

    best_bpb = min(candidate["validation_actual_mean_payload_bpb"] for candidate in candidates)
    eligible = [
        candidate
        for candidate in candidates
        if candidate["search_codec_decision_mismatches"] == 0
        and candidate["validation_actual_mean_payload_bpb"] <= best_bpb + COMPLEXITY_TOLERANCE_BPB
    ]
    selected = min(
        eligible,
        key=lambda candidate: (
            candidate["deployed_feature_count"],
            candidate["deployed_complexity"],
            candidate["validation_actual_mean_payload_bpb"],
            candidate["candidate_id"],
        ),
    )
    selected_rule = selected["rule"]
    deployed_features = integer_admission_rule_feature_names(selected_rule)
    ablation = run_ablation(block_rows, selected)
    p13_simulated = p13_development_baseline(block_rows)
    p13_actual = {
        name: run_p13(context, streams[name], verify=True) for name in VALIDATION_STREAMS
    }
    rows_digest = sha256(canonical_json(block_rows))
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "new_holdout_sources_opened": False,
        "source": "already-consumed PILOT-012 and PILOT-013 mixed streams",
        "source_manifest": source_manifest,
        "fit_streams": list(FIT_STREAMS),
        "validation_streams": list(VALIDATION_STREAMS),
        "development_block_count": len(block_rows),
        "development_rows_digest": rows_digest,
        "feature_version": RICH_CHEAP_FEATURE_VERSION,
        "candidate_feature_sets": {key: list(value) for key, value in FEATURE_SETS.items()},
        "candidate_selector_families": ["decision-tree-depth-2-or-3", "quantized-linear-scale-256"],
        "selection_complexity_tolerance_bpb": COMPLEXITY_TOLERANCE_BPB,
        "selected_candidate_id": selected["candidate_id"],
        "selected_rule": selected_rule.to_dict(),
        "selected_candidate_feature_set": list(selected["feature_names"]),
        "selected_features": list(deployed_features),
        "validation_actual_mean_payload_bpb": selected["validation_actual_mean_payload_bpb"],
        "validation_actual_mean_model_eval_fraction": selected[
            "validation_actual_mean_model_eval_fraction"
        ],
        "validation_actual_max_model_eval_fraction": selected[
            "validation_actual_max_model_eval_fraction"
        ],
        "search_codec_decision_mismatches": selected["search_codec_decision_mismatches"],
        "float_vs_deployed_route_mismatches": selected.get(
            "float_vs_deployed_route_mismatches", 0
        ),
        "p13_validation_simulated": p13_simulated,
        "p13_validation_actual_mean_payload_bpb": mean(
            result["payload_bpb"] for result in p13_actual.values()
        ),
        "p13_validation_actual_mean_model_eval_fraction": mean(
            result["model_eval_fraction"] for result in p13_actual.values()
        ),
        "feature_diagnostics": feature_diagnostics(block_rows),
        "ablation": ablation,
    }
    reproduction = development_reproduction_record(summary)
    summary["development_reproduction_digest"] = sha256(canonical_json(reproduction))
    recommended_policy = {
        "pilot_version": "PILOT-014",
        "predecessor_commit": PREDECESSOR_COMMIT,
        "predecessor_scientific_run_head": PREDECESSOR_RUN_HEAD,
        "block_bytes": BLOCK_BYTES,
        "probe_bytes": PROBE_BYTES,
        "max_admitted_bytes": MAX_ADMITTED_BYTES,
        "max_admitted_fraction": MAX_ADMITTED_BYTES / STREAM_BYTES,
        "feature_version": RICH_CHEAP_FEATURE_VERSION,
        "feature_names": list(deployed_features),
        "very_surprising_bits": VERY_SURPRISING_BITS,
        "selector": selected_rule.to_dict(),
        "checkpoint": context.checkpoint,
        "cheap_provider_fingerprint": context.cheap_fp.hex(),
        "neural_gate_fingerprint": context.neural_gate_fp.hex(),
        "codec": "POL1 shared-provider range coder, unchanged",
        "selector_side_bits": 0,
        "development_reproduction": reproduction,
        "development_reproduction_digest": summary["development_reproduction_digest"],
    }
    if write_outputs:
        OUT.mkdir(parents=True, exist_ok=True)
        csvout(OUT / "development-blocks.csv", block_rows)
        serializable_candidates = []
        for candidate in candidates:
            serializable_candidates.append(
                {
                    key: (value.to_dict() if key == "rule" else value)
                    for key, value in candidate.items()
                }
            )
        csv_rows = [
            {
                key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                for key, value in candidate.items()
            }
            for candidate in serializable_candidates
        ]
        csvout(OUT / "development-candidates.csv", csv_rows)
        csvout(OUT / "development-ablation.csv", ablation)
        (OUT / "development-summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        (OUT / "recommended-policy.json").write_text(
            json.dumps(recommended_policy, indent=2, sort_keys=True) + "\n"
        )
    return {"summary": summary, "recommended_policy": recommended_policy, "block_rows": block_rows}


def policy_digest(document: dict) -> str:
    payload = {key: value for key, value in document.items() if key != "policy_digest"}
    return sha256(canonical_json(payload))


def load_frozen_policy(path: Path) -> tuple[dict, object]:
    document = json.loads(path.read_text())
    observed_digest = policy_digest(document)
    if document.get("policy_digest") != observed_digest:
        raise RuntimeError(
            f"frozen policy digest mismatch: {observed_digest} != {document.get('policy_digest')}"
        )
    if document.get("pilot_version") != "PILOT-014":
        raise RuntimeError("wrong frozen policy version")
    if document.get("predecessor_commit") != PREDECESSOR_COMMIT:
        raise RuntimeError("frozen policy predecessor mismatch")
    if int(document["policy"]["block_bytes"]) != BLOCK_BYTES:
        raise RuntimeError("frozen block size changed")
    if int(document["policy"]["probe_bytes"]) != PROBE_BYTES:
        raise RuntimeError("frozen probe size changed")
    if int(document["policy"]["max_admitted_bytes"]) != MAX_ADMITTED_BYTES:
        raise RuntimeError("frozen budget changed")
    rule = admission_rule_from_dict(document["policy"]["selector"])
    return document, rule


def make_holdout_streams(
    context: CodecContext, preregistration: dict
) -> tuple[dict[str, bytes], list[dict], list[dict]]:
    specs = {item["name"]: item for item in preregistration["sources"]}
    sources, source_manifest = download_verified_sources(
        specs, user_agent="POLLICINO-PILOT-014-HOLDOUT/1.0"
    )
    aliases = preregistration["source_aliases"]
    p12 = context.p12
    generated = preregistration["generated_components"]
    components = {
        alias: sources[source_name] for alias, source_name in aliases.items()
    }
    components.update(
        {
            "json": p12.json_bytes(STREAM_BYTES, int(generated["json_seed"])),
            "dna": p12.dna_bytes(STREAM_BYTES, int(generated["dna_seed"])),
            "random64": p12.random_bytes(
                STREAM_BYTES, int(generated["random64_seed"]), 64
            ),
            "random256": p12.random_bytes(
                STREAM_BYTES, int(generated["random256_seed"]), 256
            ),
            "repeat": p12.cycle(
                str(generated["repeat_ascii"]).encode(), STREAM_BYTES
            ),
            "compressed": p12.compressed_bytes(
                STREAM_BYTES, int(generated["compressed_seed"])
            ),
            "english": p12.english_bytes(STREAM_BYTES),
        }
    )
    streams: dict[str, bytes] = {}
    composition_manifest = []
    for name, raw_recipe in preregistration["recipes"].items():
        recipe = [(str(component), int(length)) for component, length in raw_recipe]
        data, segments = p12.compose(components, recipe)
        if len(data) != STREAM_BYTES:
            raise RuntimeError(f"holdout stream {name} has unexpected length")
        streams[name] = data
        composition_manifest.append(
            {
                "stream": name,
                "bytes": len(data),
                "sha256": sha256(data),
                "segments": segments,
            }
        )
    return streams, source_manifest, composition_manifest


def selector_confusion(block_rows: list[dict], summaries: list[dict]) -> dict:
    selected = {int(row["block_index"]): bool(row["admitted"]) for row in summaries}
    counts = {
        "true_neural": 0,
        "false_neural": 0,
        "true_cheap": 0,
        "false_cheap": 0,
        "false_neural_lost_bits": 0,
        "false_cheap_lost_bits": 0,
    }
    for row in block_rows:
        saving = int(row["hybrid_saving_bits"])
        admitted = selected[int(row["block_index"])]
        beneficial = saving > 0
        if admitted and beneficial:
            counts["true_neural"] += 1
        elif admitted:
            counts["false_neural"] += 1
            counts["false_neural_lost_bits"] += max(0, -saving)
        elif beneficial:
            counts["false_cheap"] += 1
            counts["false_cheap_lost_bits"] += saving
        else:
            counts["true_cheap"] += 1
    return counts


def holdout_stream_metrics(
    context: CodecContext,
    stream_name: str,
    data: bytes,
    block_rows: list[dict],
    rule,
) -> tuple[dict, list[dict]]:
    cheap = reset_roundtrip(context, data, neural=False)
    neural = reset_roundtrip(context, data, neural=True)
    p12 = p12_max_roundtrip(context, data)
    p13 = run_p13(context, data, verify=True)
    p14 = run_rich(context, data, rule, verify=True)
    classical = classical_baselines(data)

    oracle_candidates = sorted(
        block_rows,
        key=lambda row: (int(row["hybrid_saving_bits"]), -int(row["block_index"])),
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
        for row in block_rows
    )
    oracle_evaluations = sum(
        int(row["hybrid_model_evaluations"])
        for row in block_rows
        if int(row["block_index"]) in oracle_selected
    )

    p14_summaries = {
        int(row["block_index"]): row for row in p14["block_summary"]
    }
    p13_summaries = {
        int(row["block_index"]): row for row in p13["block_summary"]
    }
    simulated = simulate_rule(block_rows, (stream_name,), rule)
    simulated_routes = {
        int(row["block_index"]): bool(row["admitted"])
        for row in simulated["routes"]
    }
    divergence_count = sum(
        simulated_routes[index] != bool(p14_summaries[index]["admitted"])
        for index in simulated_routes
    )
    p14_blocksum_bits = sum(
        int(row["hybrid_payload_bits"])
        if bool(p14_summaries[int(row["block_index"])]["admitted"])
        else int(row["cheap_payload_bits"])
        for row in block_rows
    )
    route_correct = sum(
        bool(p14_summaries[int(row["block_index"])]["admitted"])
        == (int(row["block_index"]) in oracle_selected)
        for row in block_rows
    )
    confusion = selector_confusion(block_rows, p14["block_summary"])
    available_gain = cheap["payload_bpb"] - neural["payload_bpb"]
    retained_gain = (
        (cheap["payload_bpb"] - p14["payload_bpb"]) / available_gain
        if available_gain > 0
        else 0.0
    )
    p13_retained_gain = (
        (cheap["payload_bpb"] - p13["payload_bpb"]) / available_gain
        if available_gain > 0
        else 0.0
    )
    diagnostics = []
    for block in block_rows:
        index = int(block["block_index"])
        diagnostics.append(
            {
                **block,
                "p13_admitted": bool(p13_summaries[index]["admitted"]),
                "p14_admitted": bool(p14_summaries[index]["admitted"]),
                "p14_selector_score": int(p14_summaries[index]["selector_score"]),
                "p14_rule_match": bool(p14_summaries[index]["rule_match"]),
                "p14_budget_limited": bool(p14_summaries[index]["budget_limited"]),
                "oracle_beneficial": int(block["hybrid_saving_bits"]) > 0,
                "oracle50_admitted": index in oracle_selected,
            }
        )
    row = {
        "stream": stream_name,
        "sample_bytes": len(data),
        "source_sha256": sha256(data),
        "cheap_reset_bpb": cheap["payload_bpb"],
        "neural_reset_bpb": neural["payload_bpb"],
        "neural_reset_model_eval_fraction": neural["model_eval_fraction"],
        "p12_max_bpb": p12["payload_bpb"],
        "p12_max_model_eval_fraction": p12["model_eval_fraction"],
        "p12_max_specialist_call_fraction": p12["specialist_call_fraction"],
        "p13_bpb": p13["payload_bpb"],
        "p13_model_eval_fraction": p13["model_eval_fraction"],
        "p13_admitted_blocks": p13["admitted_blocks"],
        "p13_retained_gain_fraction": p13_retained_gain,
        "p14_bpb": p14["payload_bpb"],
        "p14_model_eval_fraction": p14["model_eval_fraction"],
        "p14_admitted_blocks": p14["admitted_blocks"],
        "p14_rejected_blocks": len(block_rows) - p14["admitted_blocks"],
        "p14_admitted_byte_fraction": p14["admitted_byte_fraction"],
        "p14_retained_gain_fraction": retained_gain,
        "p14_minus_p13_bpb": p14["payload_bpb"] - p13["payload_bpb"],
        "oracle50_blocksum_bpb": oracle_bits / len(data),
        "oracle50_model_eval_fraction": oracle_evaluations / len(data),
        "oracle50_admitted_blocks": len(oracle_selected),
        "p14_blocksum_bpb": p14_blocksum_bits / len(data),
        "p14_oracle_regret_bits": p14_blocksum_bits - oracle_bits,
        "route_correct_blocks": route_correct,
        "route_accuracy": route_correct / len(block_rows),
        "search_codec_decision_mismatches": divergence_count,
        "roundtrip": p14["roundtrip"],
        "sha256_match": p14["sha256_match"],
        **confusion,
        **classical,
    }
    return row, diagnostics


def aggregate_holdout(rows: list[dict]) -> dict:
    aggregate = {
        "mean_cheap_reset_bpb": mean(row["cheap_reset_bpb"] for row in rows),
        "mean_neural_reset_bpb": mean(row["neural_reset_bpb"] for row in rows),
        "mean_p12_max_bpb": mean(row["p12_max_bpb"] for row in rows),
        "mean_p13_bpb": mean(row["p13_bpb"] for row in rows),
        "mean_p13_retained_gain_fraction": mean(
            row["p13_retained_gain_fraction"] for row in rows
        ),
        "mean_p14_bpb": mean(row["p14_bpb"] for row in rows),
        "mean_zlib_bpb": mean(row["zlib_bpb"] for row in rows),
        "mean_zstd19_bpb": mean(row["zstd19_bpb"] for row in rows),
        "mean_oracle50_blocksum_bpb": mean(row["oracle50_blocksum_bpb"] for row in rows),
        "mean_p14_model_eval_fraction": mean(row["p14_model_eval_fraction"] for row in rows),
        "max_p14_model_eval_fraction": max(row["p14_model_eval_fraction"] for row in rows),
        "min_p14_model_eval_fraction": min(row["p14_model_eval_fraction"] for row in rows),
        "mean_p14_admitted_byte_fraction": mean(row["p14_admitted_byte_fraction"] for row in rows),
        "mean_p14_retained_gain_fraction": mean(row["p14_retained_gain_fraction"] for row in rows),
        "mean_p14_retained_gain_improvement_over_p13": mean(
            row["p14_retained_gain_fraction"] - row["p13_retained_gain_fraction"]
            for row in rows
        ),
        "mean_p14_minus_p13_bpb": mean(row["p14_minus_p13_bpb"] for row in rows),
        "p14_beats_p13_streams": sum(row["p14_bpb"] < row["p13_bpb"] for row in rows),
        "p14_loses_to_p13_streams": sum(row["p14_bpb"] > row["p13_bpb"] for row in rows),
        "p14_ties_p13_streams": sum(row["p14_bpb"] == row["p13_bpb"] for row in rows),
        "p14_beats_cheap_streams": sum(row["p14_bpb"] < row["cheap_reset_bpb"] for row in rows),
        "mean_route_accuracy": mean(row["route_accuracy"] for row in rows),
        "mean_oracle_regret_bits": mean(row["p14_oracle_regret_bits"] for row in rows),
        "mean_p14_to_oracle_blocksum_gap_bpb": mean(
            row["p14_blocksum_bpb"] - row["oracle50_blocksum_bpb"] for row in rows
        ),
        "total_p14_admitted_blocks": sum(row["p14_admitted_blocks"] for row in rows),
        "total_p14_rejected_blocks": sum(row["p14_rejected_blocks"] for row in rows),
        "total_oracle50_admitted_blocks": sum(row["oracle50_admitted_blocks"] for row in rows),
        "total_route_correct_blocks": sum(row["route_correct_blocks"] for row in rows),
        "total_false_neural_admissions": sum(row["false_neural"] for row in rows),
        "total_missed_neural_opportunities": sum(row["false_cheap"] for row in rows),
        "total_false_neural_lost_bits": sum(row["false_neural_lost_bits"] for row in rows),
        "total_missed_neural_lost_bits": sum(row["false_cheap_lost_bits"] for row in rows),
        "search_codec_decision_mismatches": sum(row["search_codec_decision_mismatches"] for row in rows),
        "budget_violations": sum(row["p14_model_eval_fraction"] > 0.5 + 1e-12 for row in rows),
        "exact_roundtrip_failures": sum(not row["roundtrip"] for row in rows),
        "sha256_mismatches": sum(not row["sha256_match"] for row in rows),
    }
    aggregate["retained_gain_threshold_passed"] = bool(
        aggregate["mean_p14_retained_gain_fraction"] >= RETAINED_GAIN_SUCCESS
    )
    aggregate["mean_payload_beats_p13"] = bool(
        aggregate["mean_p14_bpb"] < aggregate["mean_p13_bpb"]
    )
    aggregate["stronger_four_of_six_passed"] = aggregate["p14_beats_p13_streams"] >= 4
    aggregate["primary_success"] = bool(
        aggregate["exact_roundtrip_failures"] == 0
        and aggregate["sha256_mismatches"] == 0
        and aggregate["budget_violations"] == 0
        and aggregate["search_codec_decision_mismatches"] == 0
        and aggregate["retained_gain_threshold_passed"]
        and aggregate["mean_payload_beats_p13"]
    )
    if aggregate["primary_success"]:
        classification = "PILOT014_RICH_CHEAP_ADMISSION_SUCCESS"
    elif aggregate["mean_payload_beats_p13"]:
        classification = "PILOT014_SELECTOR_IMPROVED_BUT_THRESHOLD_NOT_MET"
    else:
        classification = "PILOT014_CHEAP_FEATURES_INSUFFICIENT"
    aggregate["scientific_classification"] = classification
    return aggregate


def bundle_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def feature_cost_record(rule) -> dict:
    features = integer_admission_rule_feature_names(rule)
    histogram_needed = bool(set(features) & {"unique_count", "max_hist_count"})
    adjacency_needed = bool(
        set(features) & {"transition_count", "distinct_transition_count", "longest_run"}
    )
    surprise_needed = any(name.startswith("surprise_") for name in features) or (
        "very_surprising_count" in features
    )
    if isinstance(rule, QuantizedLinearAdmissionRule):
        scorer = {
            "integer_multiplications": len(rule.weights),
            "integer_additions": len(rule.weights),
            "comparisons": 1,
        }
    else:
        scorer = {
            "integer_multiplications": 0,
            "integer_additions": 0,
            "comparisons": 4,
            "note": "at most three feature splits plus admission threshold",
        }
    return {
        "probe_bytes": PROBE_BYTES,
        "deployed_features": list(features),
        "incremental_feature_work": {
            "histogram_updates": PROBE_BYTES if histogram_needed else 0,
            "adjacent_pair_updates": PROBE_BYTES - 1 if adjacency_needed else 0,
            "per_symbol_integer_codelength_bounds": PROBE_BYTES if surprise_needed else 0,
            "exact_total_codelength_bigint_products": (
                PROBE_BYTES if "probe_code_bits_ceil" in features else 0
            ),
            "bounded_summary_pass_bytes": PROBE_BYTES if surprise_needed else 0,
        },
        "selector_work": scorer,
        "logical_bounded_state": {
            "probe_symbols": PROBE_BYTES,
            "per_symbol_surprises": PROBE_BYTES,
            "histogram_entries_max": PROBE_BYTES if histogram_needed else 0,
            "distinct_transition_entries_max": PROBE_BYTES - 1 if adjacency_needed else 0,
            "scalar_counters": 9,
            "python_container_overhead": "implementation-dependent; bounded by the 16-byte probe",
        },
        "additional_bytes_transmitted": 0,
        "neural_calls_during_feature_extraction": 0,
        "relative_cost_statement": "bounded O(16) integer/container operations versus hundreds of neural forward evaluations per admitted block",
    }


def run_holdout(
    context: CodecContext,
    policy_document: dict,
    rule,
    preregistration: dict,
    preregistration_digest: str,
) -> dict:
    streams, source_manifest, composition_manifest = make_holdout_streams(
        context, preregistration
    )
    block_rows = precompute_blocks(context, streams, progress_label="HOLDOUT_DIAGNOSTIC_PRECOMPUTED")
    holdout_rows: list[dict] = []
    holdout_block_rows: list[dict] = []
    for stream_name, data in streams.items():
        stream_blocks = [row for row in block_rows if row["stream"] == stream_name]
        row, diagnostics = holdout_stream_metrics(
            context, stream_name, data, stream_blocks, rule
        )
        holdout_rows.append(row)
        holdout_block_rows.extend(diagnostics)
        print("HOLDOUT", stream_name, json.dumps(row, sort_keys=True), flush=True)
    aggregate = aggregate_holdout(holdout_rows)
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "preregistration_digest": preregistration_digest,
        "selection_basis": preregistration["selection_basis"],
        "sources": source_manifest,
        "streams": composition_manifest,
    }
    results = {
        "experiment_id": EXPERIMENT_ID,
        "question": "Can richer causal cheap-only evidence allocate the same hard neural budget better than PILOT-013?",
        "predecessor": {
            "commit": PREDECESSOR_COMMIT,
            "scientific_run_head": PREDECESSOR_RUN_HEAD,
            "remains_valid_unchanged": True,
        },
        "run_source_commit": current_git_sha(),
        "frozen_policy_digest": policy_document["policy_digest"],
        "holdout_preregistration_digest": preregistration_digest,
        "policy": policy_document["policy"],
        "development": policy_document["development"],
        "holdout": {
            "name": preregistration["name"],
            "streams": list(streams),
            "sources": source_manifest,
            "composition_manifest": "holdout-manifest.json",
            "per_stream_table": "holdout.csv",
            "per_block_table": "holdout-blocks.csv",
            "aggregate": aggregate,
        },
        "feature_cost": feature_cost_record(rule),
        "protocol": {
            "precision_bits": PRECISION,
            "block_bytes": BLOCK_BYTES,
            "probe_bytes": PROBE_BYTES,
            "hard_max_admitted_bytes": MAX_ADMITTED_BYTES,
            "hard_max_admitted_fraction": MAX_ADMITTED_BYTES / STREAM_BYTES,
            "selector_side_bits": 0,
            "neural_evaluations_before_admission_decision": 0,
            "primary_compute_metric": "actual uncached PyTorch model forward evaluations / source bytes",
            "search_and_codec_helper": "rich_cheap_admission_decision",
            "holdout_policy_retuning": 0,
            "policy_modifications_after_holdout_access": 0,
            "codec_core_changed": False,
            "checkpoint_assumption": "shared, but not free; checkpoint/model cost is separate from payload bpb",
            "primary_retained_gain_threshold": RETAINED_GAIN_SUCCESS,
            "stronger_stream_win_target": "at least 4 of 6",
        },
        "failure_taxonomy": {
            "repaired_before_freeze": [
                {
                    "class": "TEST_HARNESS_ERROR",
                    "detail": "local Python initially lacked pytest and NumPy; declared dependencies were installed before development selection",
                }
            ],
            "reporting_only_rerun_after_first_frozen_measurement": {
                "class": "TEST_HARNESS_ERROR",
                "first_artifact_digest": "sha256:da8838b724b96eefd4618ee1b7984a779bb2035a34ed78cc8e0d52dfc3ac4ab4",
                "repair": "add omitted PILOT-013 retained-gain and explicit oracle/admission aggregate fields",
                "policy_changed": False,
                "required_full_development_reproduction": True,
            },
            "scientific_run_failures": [],
        },
        "limits": [
            "The six deterministic mixed streams are a mechanism holdout, not a population sample.",
            "The diagnostic oracle is non-causal and uses independently coded block payloads.",
            "Model/checkpoint description length is reported separately and not included in payload bpb.",
            "Feature extraction uses Python containers; logical state is bounded but interpreter overhead is implementation-dependent.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    results_path = OUT / "results.json"
    holdout_path = OUT / "holdout.csv"
    blocks_path = OUT / "holdout-blocks.csv"
    manifest_path = OUT / "holdout-manifest.json"
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    csvout(holdout_path, holdout_rows)
    csvout(blocks_path, holdout_block_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    artifact_sha = bundle_digest([results_path, holdout_path, blocks_path, manifest_path])
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "execution_kind": "local-scientific-run",
        "workflow_run_id": None,
        "git_sha": current_git_sha(),
        "artifact": {
            "id": f"local-{current_git_sha()[:12]}-{policy_document['policy_digest'][:12]}",
            "name": "pilot-014-results",
            "digest": f"sha256:{artifact_sha}",
            "digest_definition": "SHA-256 over sorted filename, NUL, and each file SHA-256 for results/holdout/blocks/manifest",
        },
        "frozen_policy_digest": policy_document["policy_digest"],
        "holdout_manifest_digest": sha256(manifest_path.read_bytes()),
        "holdout_preregistration_digest": preregistration_digest,
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "zstandard": zstd.__version__,
        "device": "cpu",
        "torch_num_threads": torch.get_num_threads(),
        "torch_deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "random_seeds": preregistration["generated_components"],
        "checkpoint": context.checkpoint,
        "exact_command": "GITHUB_TOKEN=\"$(gh auth token)\" .venv/bin/python experiments/pilot-014/run_frozen.py",
        "tests": "recorded after final validation",
    }
    (OUT / "run-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    print("AGGREGATE", json.dumps(aggregate, sort_keys=True), flush=True)
    print("ARTIFACT_SHA256", artifact_sha, flush=True)
    return {"results": results, "metadata": metadata, "manifest": manifest}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase", choices=("development", "holdout"), help="experiment phase"
    )
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--preregistration", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = load_context()
    if args.phase == "development":
        development = run_development(context)
        print(
            "DEVELOPMENT_FROZEN_CANDIDATE",
            json.dumps(development["recommended_policy"], sort_keys=True),
            flush=True,
        )
        return
    if os.environ.get("PILOT014_FROZEN_FIREWALL") != "verified":
        raise RuntimeError("fresh holdout may only be run through run_frozen.py")
    if args.policy is None or args.preregistration is None:
        raise RuntimeError("holdout requires --policy and --preregistration")
    policy_document, rule = load_frozen_policy(args.policy)
    preregistration_bytes = args.preregistration.read_bytes()
    preregistration = json.loads(preregistration_bytes)
    run_holdout(
        context,
        policy_document,
        rule,
        preregistration,
        sha256(preregistration_bytes),
    )


if __name__ == "__main__":
    main()
