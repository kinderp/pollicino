from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
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
from pollicino.compression.routing import (
    CostAwareSpecialistRouterCDFProvider,
    cost_aware_router_fingerprint,
)

PRECISION = 18
PRIMARY_PROBE = 256
PRIMARY_RATIO = (1, 1)
SILESIA_SLICE = 2048
LARGE_SLICE = 4096
PROBE_ABLATION = (64, 128, 256, 512)
TRAINING_COMMIT = "9c833cfb119fdfc941977abafc3fcb75e9e9c7ec"
LARGE_URL = "https://corpus.canterbury.ac.nz/resources/large.zip"
LARGE = {
    "E.coli": ("dna", 4_638_690),
    "bible.txt": ("english-bible", 4_047_392),
    "world192.txt": ("world-factbook", 2_473_400),
}
CHEAP_NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")
NEURAL_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)


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


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004_for_p8")
    p5 = load_module(ROOT / "experiments/pilot-005/run.py", "pilot005_for_p8")
    p6 = load_module(ROOT / "experiments/pilot-006/run.py", "pilot006_for_p8")
    p7 = load_module(ROOT / "experiments/pilot-007/run.py", "pilot007_for_p8")
    p7_results = json.loads((ROOT / "experiments/pilot-007/results.json").read_text())

    model, spec, training = p5.prepare_frozen_model()
    neural_fp = torch_model_fingerprint(model, spec)
    if neural_fp.hex() != p7_results["neural_gate"]["canonical_neural_fingerprint"]:
        raise RuntimeError("frozen neural fingerprint did not reproduce PILOT-007")
    checkpoint_bytes = int(p7_results["neural_gate"]["checkpoint_bytes"])
    observed_silesia_gain = (
        p7_results["silesia_new_holdout"]["aggregate"]["mean_cheap_payload_bpb"]
        - p7_results["silesia_new_holdout"]["aggregate"]["mean_neural_gate_payload_bpb"]
    )
    self_contained_min_bytes = math.ceil(checkpoint_bytes * 8 / observed_silesia_gain)

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
    cheap_fp = expert_gate_fingerprint(
        expert_fingerprints=cheap_fps,
        names=CHEAP_NAMES,
        window=cheap_window,
    )

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

    def router_factory(
        stream_bytes: int,
        *,
        probe_bytes: int = PRIMARY_PROBE,
        min_stream_bytes: int = 0,
        specialist_available: bool = True,
        ratio: tuple[int, int] = PRIMARY_RATIO,
    ):
        def factory():
            specialist = neural_factory() if specialist_available else None
            return CostAwareSpecialistRouterCDFProvider(
                cheap_factory(),
                specialist,
                stream_bytes=stream_bytes,
                probe_bytes=probe_bytes,
                min_stream_bytes=min_stream_bytes,
                required_ratio_num=ratio[0],
                required_ratio_den=ratio[1],
                cheap_name="cheap-gate",
                specialist_name="neural-gate",
            )
        return factory

    def router_fp(
        stream_bytes: int,
        *,
        probe_bytes: int = PRIMARY_PROBE,
        min_stream_bytes: int = 0,
        specialist_available: bool = True,
        ratio: tuple[int, int] = PRIMARY_RATIO,
    ) -> bytes:
        return cost_aware_router_fingerprint(
            cheap_fingerprint=cheap_fp,
            specialist_fingerprint=neural_gate_fp if specialist_available else None,
            stream_bytes=stream_bytes,
            probe_bytes=probe_bytes,
            min_stream_bytes=min_stream_bytes,
            required_ratio_num=ratio[0],
            required_ratio_den=ratio[1],
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
        if hasattr(encoder, "selected_route"):
            result["selected_route"] = encoder.selected_route
            result["route_choice_fractions"] = encoder.choice_fractions()
            result["probe_count"] = encoder.probe_count
        return result

    # Silesia is already-consumed development data. Primary policy stays fixed;
    # probe ablation is diagnostic only and does not choose PILOT-008 defaults.
    silesia_files, silesia_manifest = p7.download_silesia()
    silesia_rows = []
    probe_rows = []
    for name, raw in silesia_files.items():
        sample = raw[:SILESIA_SLICE]
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        primary = roundtrip(
            sample,
            router_factory(len(sample)),
            router_fp(len(sample)),
        )
        base = baselines(sample)
        silesia_rows.append({
            "file": name,
            "category": p7.SILESIA[name][0],
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "router_payload_bpb": primary["payload_bpb"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "neural_encode_seconds": neural["encode_seconds"],
            "router_encode_seconds": primary["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "neural_decode_seconds": neural["decode_seconds"],
            "router_decode_seconds": primary["decode_seconds"],
            "router_selected_route": primary["selected_route"],
            **base,
        })
        for probe in PROBE_ABLATION:
            result = roundtrip(
                sample,
                router_factory(len(sample), probe_bytes=probe),
                router_fp(len(sample), probe_bytes=probe),
            )
            probe_rows.append({
                "file": name,
                "probe_bytes": probe,
                "payload_bpb": result["payload_bpb"],
                "encode_seconds": result["encode_seconds"],
                "decode_seconds": result["decode_seconds"],
                "selected_route": result["selected_route"],
            })
        print("SILESIA", name, primary["selected_route"], primary["payload_bpb"], flush=True)

    # New untouched holdout: fixed three-file subset of the Canterbury Large Corpus.
    largezip = p4.download(LARGE_URL, OUT / "large.zip")
    large = p4.unpack(largezip, LARGE)
    large_rows = []
    large_manifest = []
    for name, raw in large.items():
        sample = raw[:LARGE_SLICE]
        cheap = roundtrip(sample, cheap_factory, cheap_fp)
        neural = roundtrip(sample, neural_factory, neural_gate_fp)
        shared_router = roundtrip(
            sample,
            router_factory(len(sample)),
            router_fp(len(sample)),
        )
        unavailable_router = roundtrip(
            sample,
            router_factory(len(sample), specialist_available=False),
            router_fp(len(sample), specialist_available=False),
        )
        self_contained_router = roundtrip(
            sample,
            router_factory(len(sample), min_stream_bytes=self_contained_min_bytes),
            router_fp(len(sample), min_stream_bytes=self_contained_min_bytes),
        )
        base = baselines(sample)
        row = {
            "file": name,
            "category": LARGE[name][0],
            "file_bytes": len(raw),
            "sha256": sha(raw),
            "sample_bytes": len(sample),
            "cheap_payload_bpb": cheap["payload_bpb"],
            "neural_payload_bpb": neural["payload_bpb"],
            "shared_router_payload_bpb": shared_router["payload_bpb"],
            "shared_router_pol1_bpb": shared_router["pol1_bpb"],
            "shared_router_route": shared_router["selected_route"],
            "shared_router_encode_seconds": shared_router["encode_seconds"],
            "shared_router_decode_seconds": shared_router["decode_seconds"],
            "unavailable_router_payload_bpb": unavailable_router["payload_bpb"],
            "unavailable_router_route": unavailable_router["selected_route"],
            "self_contained_router_payload_bpb": self_contained_router["payload_bpb"],
            "self_contained_router_route": self_contained_router["selected_route"],
            "cheap_encode_seconds": cheap["encode_seconds"],
            "cheap_decode_seconds": cheap["decode_seconds"],
            "neural_encode_seconds": neural["encode_seconds"],
            "neural_decode_seconds": neural["decode_seconds"],
            **base,
        }
        large_rows.append(row)
        large_manifest.append({
            "file": name,
            "category": LARGE[name][0],
            "bytes": len(raw),
            "sha256": sha(raw),
        })
        print("LARGE", name, shared_router["selected_route"], shared_router["payload_bpb"], flush=True)

    # Regression controls demonstrate availability and domain-specialist behavior.
    p6_test = p6.frozen_test_split()[:SILESIA_SLICE]
    p4_can = p4.download(p4.ART_URL, OUT / "artificl.zip")
    art = p4.unpack(p4_can, p4.ART)
    controls = []
    for name, category, sample in [
        ("self-v2-test", "training-domain-test", p6_test),
        ("aaa.txt", "repetition", art["aaa.txt"][:SILESIA_SLICE]),
        ("random.txt", "random-64-symbol-alphabet", art["random.txt"][:SILESIA_SLICE]),
    ]:
        shared = roundtrip(sample, router_factory(len(sample)), router_fp(len(sample)))
        no_model = roundtrip(
            sample,
            router_factory(len(sample), specialist_available=False),
            router_fp(len(sample), specialist_available=False),
        )
        controls.append({
            "file": name,
            "category": category,
            "shared_router_payload_bpb": shared["payload_bpb"],
            "shared_router_route": shared["selected_route"],
            "shared_router_encode_seconds": shared["encode_seconds"],
            "no_model_payload_bpb": no_model["payload_bpb"],
            "no_model_route": no_model["selected_route"],
        })

    silesia_agg = {
        "files": len(silesia_rows),
        "mean_cheap_bpb": mean(r["cheap_payload_bpb"] for r in silesia_rows),
        "mean_neural_bpb": mean(r["neural_payload_bpb"] for r in silesia_rows),
        "mean_router_bpb": mean(r["router_payload_bpb"] for r in silesia_rows),
        "mean_router_encode_seconds": mean(r["router_encode_seconds"] for r in silesia_rows),
        "mean_neural_encode_seconds": mean(r["neural_encode_seconds"] for r in silesia_rows),
        "specialist_routes": sum(r["router_selected_route"] == "neural-gate" for r in silesia_rows),
        "cheap_routes": sum(r["router_selected_route"] == "cheap-gate" for r in silesia_rows),
    }
    large_agg = {
        "files": len(large_rows),
        "subset_note": "fixed three-file Large Corpus subset; do not report as the evolving corpus overall average",
        "mean_cheap_bpb": mean(r["cheap_payload_bpb"] for r in large_rows),
        "mean_neural_bpb": mean(r["neural_payload_bpb"] for r in large_rows),
        "mean_shared_router_bpb": mean(r["shared_router_payload_bpb"] for r in large_rows),
        "mean_zlib_bpb": mean(r["zlib_bpb"] for r in large_rows),
        "mean_zstd19_bpb": mean(r["zstd19_bpb"] for r in large_rows),
        "shared_specialist_routes": sum(r["shared_router_route"] == "neural-gate" for r in large_rows),
        "shared_cheap_routes": sum(r["shared_router_route"] == "cheap-gate" for r in large_rows),
        "all_files_below_self_contained_break_even": all(len(large[name]) < self_contained_min_bytes for name in large),
    }

    results = {
        "experiment_id": "pilot-008-automatic-specialist-routing",
        "base_commit": os.environ.get("GITHUB_SHA", "local"),
        "training_commit": TRAINING_COMMIT,
        "question": "Can POLLICINO automatically preserve a cheap universal path while activating the neural specialist only when availability, size policy and causal evidence justify it?",
        "primary_policy": {
            "probe_bytes": PRIMARY_PROBE,
            "required_likelihood_ratio": list(PRIMARY_RATIO),
            "shared_model_min_stream_bytes": 0,
            "self_contained_min_stream_bytes": self_contained_min_bytes,
            "checkpoint_bytes": checkpoint_bytes,
            "break_even_source": "PILOT-007 observed Silesia mean cheap-neural payload advantage",
            "selector_side_bits": 0,
            "decision": "single post-probe lock; cheap during probe",
        },
        "model": {
            "canonical_neural_fingerprint": neural_fp.hex(),
            "cheap_gate_fingerprint": cheap_fp.hex(),
            "neural_gate_fingerprint": neural_gate_fp.hex(),
        },
        "silesia_development": {"aggregate": silesia_agg, "rows": silesia_rows, "probe_ablation": probe_rows},
        "large_new_holdout": {"aggregate": large_agg, "rows": large_rows, "manifest": large_manifest},
        "controls": controls,
        "source_archives": {
            "large_sha256": sha(largezip),
            "artificial_sha256": sha(p4_can),
        },
        "limits": [
            "The primary probe/ratio policy was fixed before the Large Corpus holdout was evaluated.",
            "Silesia is development/replication data because it was already used in PILOT-007.",
            "Large Corpus results encode only the first 4096 bytes of each fixed file; full file size is reported separately.",
            "The self-contained threshold accounts only for checkpoint bytes using the PILOT-007 observed gain, not CPU/energy cost.",
            "The current POL1 shared-model container does not yet materialize a high-level model registry; experiments pass providers explicitly.",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (OUT / "large-manifest.json").write_text(json.dumps(large_manifest, indent=2) + "\n")
    csvout(OUT / "silesia.csv", silesia_rows)
    csvout(OUT / "probe-ablation.csv", probe_rows)
    csvout(OUT / "large.csv", large_rows)
    csvout(OUT / "controls.csv", controls)
    print(json.dumps({"silesia": silesia_agg, "large": large_agg, "controls": controls}, indent=2))


if __name__ == "__main__":
    main()
