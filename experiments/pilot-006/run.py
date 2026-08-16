from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
import tempfile
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
from pollicino.compression.codec import decode_pol, encode_shared, inspect_pol
from pollicino.compression.gating import DeterministicExpertGateCDFProvider, expert_gate_fingerprint
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint

TRAINING_COMMIT = "9c833cfb119fdfc941977abafc3fcb75e9e9c7ec"
PRECISION = 18
SLICE = 2048
DEV_WINDOWS = (16, 64, 256)
EXPERT_NAMES = ("adaptive-o3", "frozen-neural", "neural-prior-256", "neural-prior-1024")
ADAPTIVE_CFG = dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1)
CAL_URL = "https://corpus.canterbury.ac.nz/resources/calgary.zip"
CAL = {
    "bib": ("bibliography", 111261),
    "book1": ("fiction", 768771),
    "book2": ("nonfiction-troff", 610856),
    "geo": ("geophysical", 102400),
    "news": ("usenet", 377109),
    "obj1": ("vax-object", 21504),
    "obj2": ("mac-object", 246814),
    "paper1": ("technical-paper", 53161),
    "paper2": ("technical-paper", 82199),
    "pic": ("fax", 513216),
    "progc": ("c-source", 39611),
    "progl": ("lisp-source", 71646),
    "progp": ("pascal-source", 49379),
    "trans": ("terminal-transcript", 93695),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def frozen_test_split() -> bytes:
    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        archive = td / "base.tar"
        frozen = td / "repo"
        frozen.mkdir()
        subprocess.run(["git", "archive", TRAINING_COMMIT, "-o", str(archive)], check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(frozen)
        prep = load_module(frozen / "experiments/pilot-001/prepare_data.py", "p6_frozen_prepare")
        data_dir = td / "data"
        prep.write_dataset(frozen, data_dir)
        return (data_dir / "test.bin").read_bytes()


def download_and_unpack(p4, url: str, path: Path, expected: dict[str, tuple[str, int]]):
    archive = p4.download(url, path)
    return archive, p4.unpack(archive, expected)


def baseline_bpb(data: bytes) -> dict[str, float]:
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

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004_for_p6_final")
    p5 = load_module(ROOT / "experiments/pilot-005/run.py", "pilot005_for_p6_final")
    p5_results = json.loads((ROOT / "experiments/pilot-005/results.json").read_text())
    p3_results = json.loads((ROOT / "experiments/pilot-003/results.json").read_text())

    model, spec, training = p5.prepare_frozen_model()
    neural_fp = torch_model_fingerprint(model, spec)
    if neural_fp.hex() != p5_results["neural_model"]["canonical_fingerprint"]:
        raise RuntimeError("PILOT-005 neural model fingerprint did not reproduce")

    canzip, can = download_and_unpack(p4, p4.CAN_URL, OUT / "cantrbry.zip", p4.CAN)
    artzip, art = download_and_unpack(p4, p4.ART_URL, OUT / "artificl.zip", p4.ART)
    calzip, cal = download_and_unpack(p4, CAL_URL, OUT / "calgary.zip", CAL)

    adaptive_fp = adaptive_fingerprint(**ADAPTIVE_CFG)
    prior256_fp = adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=256, neural_fingerprint=neural_fp)
    prior1024_fp = adaptive_fingerprint(**ADAPTIVE_CFG, prior_strength=1024, neural_fingerprint=neural_fp)
    expert_fps = (adaptive_fp, neural_fp, prior256_fp, prior1024_fp)

    def adaptive_factory():
        return AdaptiveNGramCDFProvider(**ADAPTIVE_CFG)

    def gate_factory(window: int):
        def factory():
            shared_prior = PyTorchCDFProvider(model, spec, precision_bits=PRECISION, device="cpu")
            experts = [
                AdaptiveNGramCDFProvider(**ADAPTIVE_CFG),
                shared_prior,
                NeuralPriorAdaptiveCDFProvider(shared_prior, prior_strength=256, **ADAPTIVE_CFG),
                NeuralPriorAdaptiveCDFProvider(shared_prior, prior_strength=1024, **ADAPTIVE_CFG),
            ]
            return DeterministicExpertGateCDFProvider(experts, names=EXPERT_NAMES, window=window)
        return factory

    def gate_fp(window: int) -> bytes:
        return expert_gate_fingerprint(
            expert_fingerprints=expert_fps,
            names=EXPERT_NAMES,
            window=window,
        )

    def encode_gate(data: bytes, window: int, *, verify: bool) -> dict:
        encoder = gate_factory(window)()
        started = time.perf_counter()
        blob = encode_shared(data, encoder, gate_fp(window), precision_bits=PRECISION)
        enc = time.perf_counter() - started
        dec = None
        if verify:
            decoder = gate_factory(window)()
            started = time.perf_counter()
            restored = decode_pol(blob, shared_provider=decoder, expected_model_fingerprint=gate_fp(window))
            dec = time.perf_counter() - started
            assert restored == data
            assert encoder.choice_counts == decoder.choice_counts
        info = inspect_pol(blob)
        return {
            "payload_bpb": info["payload_bpb"],
            "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc,
            "decode_seconds": dec,
            "choice_fractions": encoder.choice_fractions(),
        }

    def roundtrip_adaptive(data: bytes) -> dict:
        started = time.perf_counter()
        blob = encode_shared(data, adaptive_factory(), adaptive_fp, precision_bits=PRECISION)
        enc = time.perf_counter() - started
        started = time.perf_counter()
        restored = decode_pol(blob, shared_provider=adaptive_factory(), expected_model_fingerprint=adaptive_fp)
        dec = time.perf_counter() - started
        assert restored == data
        info = inspect_pol(blob)
        return {
            "payload_bpb": info["payload_bpb"],
            "pol1_bpb": info["realized_bpb"],
            "encode_seconds": enc,
            "decode_seconds": dec,
        }

    # Development only: choose the rolling window on already-consumed Canterbury/Artificial slices.
    dev_names = list(p5.REPRESENTATIVE) + list(p5.ARTIFICIAL_REP)
    dev_sources = {**can, **art}
    dev_rows = []
    for window in DEV_WINDOWS:
        values = []
        for name in dev_names:
            data = dev_sources[name][:SLICE]
            result = encode_gate(data, window, verify=False)
            values.append(result["payload_bpb"])
            dev_rows.append({
                "window": window,
                "file": name,
                "category": p4.CAN[name][0] if name in p4.CAN else p4.ART[name][0],
                "sample_bytes": len(data),
                **result,
            })
            print("DEV", window, name, result["payload_bpb"], flush=True)
        print("DEV-MEAN", window, mean(values), flush=True)
    window_means = {
        window: mean(row["payload_bpb"] for row in dev_rows if row["window"] == window)
        for window in DEV_WINDOWS
    }
    selected_window = min(DEV_WINDOWS, key=lambda w: window_means[w])

    # Calgary: untouched holdout after the window has been frozen.
    calgary_rows = []
    for name, data in cal.items():
        sample = data[:SLICE]
        gate = encode_gate(sample, selected_window, verify=True)
        adaptive = roundtrip_adaptive(sample)
        bases = baseline_bpb(sample)
        eval_n = min(65536, len(data))
        long_adaptive = p5.adaptive_bpb(data, eval_n, ADAPTIVE_CFG)
        long_bases = baseline_bpb(data[:eval_n])
        calgary_rows.append({
            "file": name,
            "category": CAL[name][0],
            "file_bytes": len(data),
            "sha256": sha(data),
            "sample_bytes": len(sample),
            "gate_payload_bpb": gate["payload_bpb"],
            "gate_pol1_bpb": gate["pol1_bpb"],
            "adaptive_payload_bpb": adaptive["payload_bpb"],
            "adaptive_pol1_bpb": adaptive["pol1_bpb"],
            "zlib_bpb": bases["zlib_bpb"],
            "zstd19_bpb": bases["zstd19_bpb"],
            "gate_encode_seconds": gate["encode_seconds"],
            "gate_decode_seconds": gate["decode_seconds"],
            "gate_choice_fractions": gate["choice_fractions"],
            "long_eval_bytes": eval_n,
            "long_adaptive_o3_bpb": long_adaptive,
            "long_zlib_bpb": long_bases["zlib_bpb"],
            "long_zstd19_bpb": long_bases["zstd19_bpb"],
        })
        print("CALGARY", name, gate["payload_bpb"], adaptive["payload_bpb"], bases["zlib_bpb"], flush=True)

    # In-domain and artificial regression controls.
    self_test = frozen_test_split()[:SLICE]
    controls = []
    for name, category, data in [
        ("self-v2-test", "training-domain-test", self_test),
        ("aaa.txt", "repetition", art["aaa.txt"][:SLICE]),
        ("random.txt", "random-64-symbol-alphabet", art["random.txt"][:SLICE]),
    ]:
        gate = encode_gate(data, selected_window, verify=True)
        adaptive = roundtrip_adaptive(data)
        bases = baseline_bpb(data)
        row = {
            "file": name,
            "category": category,
            "sample_bytes": len(data),
            "gate_payload_bpb": gate["payload_bpb"],
            "gate_pol1_bpb": gate["pol1_bpb"],
            "adaptive_payload_bpb": adaptive["payload_bpb"],
            "zlib_bpb": bases["zlib_bpb"],
            "zstd19_bpb": bases["zstd19_bpb"],
            "gate_choice_fractions": gate["choice_fractions"],
        }
        if name == "self-v2-test":
            row["frozen_neural_pilot003_payload_bpb"] = next(
                r["payload_bpb"] for r in p3_results["size_sweep"] if r["bytes"] == SLICE
            )
        controls.append(row)

    gate_beats_adaptive = sum(r["gate_payload_bpb"] < r["adaptive_payload_bpb"] for r in calgary_rows)
    gate_beats_zlib = sum(r["gate_payload_bpb"] < r["zlib_bpb"] for r in calgary_rows)
    pol1_beats_zlib = sum(r["gate_pol1_bpb"] < r["zlib_bpb"] for r in calgary_rows)
    mean_gate = mean(r["gate_payload_bpb"] for r in calgary_rows)
    mean_adaptive = mean(r["adaptive_payload_bpb"] for r in calgary_rows)
    mean_zlib = mean(r["zlib_bpb"] for r in calgary_rows)
    mean_direct_neural = mean(r["gate_choice_fractions"].get("frozen-neural", 0.0) for r in calgary_rows)
    mean_neural_family = mean(
        sum(r["gate_choice_fractions"].get(name, 0.0) for name in EXPERT_NAMES[1:])
        for r in calgary_rows
    )

    results = {
        "experiment_id": "pilot-006-deterministic-expert-gate",
        "base_commit": os.environ.get("GITHUB_SHA", "local"),
        "training_commit": TRAINING_COMMIT,
        "training_domain": "pollicino-self-v2-clean-git frozen at training_commit",
        "external_fine_tuning": False,
        "development_corpus": "Canterbury + Artificial representative 2 KiB slices",
        "holdout_corpus": "Calgary Corpus",
        "neural_model": {
            "spec": spec.__dict__,
            "canonical_fingerprint": neural_fp.hex(),
            "checkpoint_bytes": training["checkpoint_bytes"],
        },
        "gate": {
            "experts": list(EXPERT_NAMES),
            "candidate_windows": list(DEV_WINDOWS),
            "development_mean_payload_bpb": {str(k): v for k, v in window_means.items()},
            "selected_window": selected_window,
            "fingerprint": gate_fp(selected_window).hex(),
            "decision_arithmetic": "exact integer rolling likelihood; stable expert-order tie break",
            "selector_side_bits": 0,
        },
        "aggregate_holdout_2k": {
            "mean_gate_payload_bpb": mean_gate,
            "mean_adaptive_o3_payload_bpb": mean_adaptive,
            "mean_zlib_bpb": mean_zlib,
            "gate_beats_adaptive_files": gate_beats_adaptive,
            "gate_beats_zlib_files": gate_beats_zlib,
            "gate_pol1_beats_zlib_files": pol1_beats_zlib,
            "mean_frozen_neural_choice_fraction": mean_direct_neural,
            "mean_neural_family_choice_fraction": mean_neural_family,
        },
        "calgary": calgary_rows,
        "controls": controls,
        "development": dev_rows,
        "sources": {
            "canterbury_archive_sha256": sha(canzip),
            "artificial_archive_sha256": sha(artzip),
            "calgary_archive_sha256": sha(calzip),
        },
        "limits": [
            "The gate window was selected on Canterbury/Artificial development slices; Calgary is the untouched holdout.",
            "Holdout gate comparisons use the first 2048 bytes of each Calgary file; long-prefix reporting is provided only for pure adaptive-o3.",
            "The gate requires the shared neural checkpoint even when adaptive-o3 is selected.",
            "No gradient update or selector side stream is transmitted.",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    csvout(OUT / "development.csv", dev_rows)
    csvout(OUT / "calgary.csv", calgary_rows)
    csvout(OUT / "controls.csv", controls)
    manifest = [
        {"file": name, "category": CAL[name][0], "bytes": len(data), "sha256": sha(data)}
        for name, data in cal.items()
    ]
    (OUT / "calgary-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(results["aggregate_holdout_2k"], indent=2))


if __name__ == "__main__":
    main()
