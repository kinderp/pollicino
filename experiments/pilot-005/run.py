from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path
from statistics import mean

import torch

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

from pollicino.compression.adaptive import AdaptiveNGramCDFProvider, NeuralPriorAdaptiveCDFProvider, adaptive_fingerprint
from pollicino.compression.codec import decode_pol, encode_shared, inspect_pol
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint

ADAPTIVE_CONFIGS = {
    "adaptive-o2": dict(max_order=2, order_weights=(1, 4, 16), base_count=1),
    "adaptive-o3": dict(max_order=3, order_weights=(1, 4, 16, 64), base_count=1),
}
PRIOR_STRENGTHS = (64, 256, 1024)
REPRESENTATIVE = ["alice29.txt", "fields.c", "kennedy.xls", "ptt5", "sum"]
ARTIFICIAL_REP = ["aaa.txt", "random.txt"]
PRECISION = 18
SLICE = 2048


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def adaptive_bpb(data: bytes, eval_bytes: int, cfg: dict) -> float:
    sample = data[:eval_bytes]
    provider = AdaptiveNGramCDFProvider(**cfg)
    prefix: list[int] = []
    bits = 0.0
    for index, symbol in enumerate(sample):
        numerator, denominator = provider.symbol_mass(index, prefix, symbol)
        bits += math.log2(denominator) - math.log2(numerator)
        prefix.append(symbol)
    return bits / len(sample) if sample else 0.0


def roundtrip(data: bytes, factory, fingerprint: bytes) -> dict:
    enc_provider = factory()
    t0 = time.perf_counter()
    blob = encode_shared(data, enc_provider, fingerprint, precision_bits=PRECISION)
    encode_seconds = time.perf_counter() - t0
    dec_provider = factory()
    t0 = time.perf_counter()
    restored = decode_pol(blob, shared_provider=dec_provider, expected_model_fingerprint=fingerprint)
    decode_seconds = time.perf_counter() - t0
    assert restored == data
    info = inspect_pol(blob)
    return {
        "payload_bpb": info["payload_bpb"],
        "pol1_bpb": info["realized_bpb"],
        "file_bytes": info["file_bytes"],
        "encode_seconds": encode_seconds,
        "decode_seconds": decode_seconds,
    }


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    p4 = load_module(ROOT / "experiments/pilot-004/run.py", "pilot004")
    p4_results = json.loads((ROOT / "experiments/pilot-004/results.json").read_text())
    model, model_spec, training = p4.prepare_model()
    neural_fp = torch_model_fingerprint(model, model_spec)
    if neural_fp.hex() != p4_results["model_fingerprint"]:
        raise RuntimeError("PILOT-005 regenerated a different neural model")

    can_archive = p4.download(p4.CAN_URL, OUT / "cantrbry.zip")
    art_archive = p4.download(p4.ART_URL, OUT / "artificl.zip")
    canterbury = p4.unpack(can_archive, p4.CAN)
    artificial = p4.unpack(art_archive, p4.ART)

    frozen_can = {row["file"]: row for row in p4_results["canterbury"]}
    frozen_art = {row["file"]: row for row in p4_results["artificial_controls"]}
    frozen_coding = {row["file"]: row for row in p4_results["coding_checks"]}

    can_rows = []
    for name, data in canterbury.items():
        frozen = frozen_can[name]
        n = int(frozen["eval_bytes"])
        row = {
            "file": name,
            "category": p4.CAN[name][0],
            "eval_bytes": n,
            "frozen_neural_bpb": frozen["model_zero_shot_bpb"],
            "zlib_bpb": frozen["eval_zlib_bpb"],
            "zstd19_bpb": frozen["eval_zstd19_bpb"],
        }
        for method, cfg in ADAPTIVE_CONFIGS.items():
            row[f"{method}_bpb"] = adaptive_bpb(data, n, cfg)
        can_rows.append(row)
        print("CANTERBURY", name, row["frozen_neural_bpb"], row["adaptive-o3_bpb"], row["zlib_bpb"], flush=True)

    art_rows = []
    for name, data in artificial.items():
        frozen = frozen_art[name]
        n = int(frozen["eval_bytes"])
        row = {
            "file": name,
            "category": p4.ART[name][0],
            "eval_bytes": n,
            "frozen_neural_bpb": frozen["model_zero_shot_bpb"],
            "zlib_bpb": frozen["eval_zlib_bpb"],
            "zstd19_bpb": frozen["eval_zstd19_bpb"],
        }
        for method, cfg in ADAPTIVE_CONFIGS.items():
            row[f"{method}_bpb"] = adaptive_bpb(data, n, cfg)
        art_rows.append(row)
        print("ARTIFICIAL", name, row["frozen_neural_bpb"], row["adaptive-o3_bpb"], row["zlib_bpb"], flush=True)

    def adaptive_factory(cfg):
        return lambda: AdaptiveNGramCDFProvider(**cfg)

    def prior_factory(strength: int):
        return lambda: NeuralPriorAdaptiveCDFProvider(
            PyTorchCDFProvider(model, model_spec, precision_bits=PRECISION, device="cpu"),
            prior_strength=strength,
            max_order=3,
            order_weights=(1, 4, 16, 64),
            base_count=1,
        )

    coding_rows = []
    all_sources = {**canterbury, **artificial}
    for name in REPRESENTATIVE + ARTIFICIAL_REP:
        data = all_sources[name][:SLICE]
        source_category = p4.CAN[name][0] if name in p4.CAN else p4.ART[name][0]
        base = frozen_coding.get(name)
        common = {
            "file": name,
            "category": source_category,
            "sample_bytes": len(data),
            "sample_sha256": sha(data),
            "zlib_bpb": (base["zlib_bpb"] if base else len(__import__("zlib").compress(data, 9)) * 8 / len(data)),
            "frozen_neural_pol1_bpb": (base["pol1_bpb"] if base else None),
        }
        for method, cfg in ADAPTIVE_CONFIGS.items():
            fp = adaptive_fingerprint(max_order=cfg["max_order"], order_weights=cfg["order_weights"], base_count=cfg["base_count"])
            coded = roundtrip(data, adaptive_factory(cfg), fp)
            coding_rows.append({**common, "method": method, "requires_neural_checkpoint": False, **coded})
        for strength in PRIOR_STRENGTHS:
            fp = adaptive_fingerprint(
                max_order=3,
                order_weights=(1, 4, 16, 64),
                base_count=1,
                prior_strength=strength,
                neural_fingerprint=neural_fp,
            )
            coded = roundtrip(data, prior_factory(strength), fp)
            coding_rows.append({**common, "method": f"neural-prior-{strength}", "requires_neural_checkpoint": True, **coded})
        print("CODED", name, flush=True)

    def weighted(rows: list[dict], key: str) -> float:
        total = sum(row["eval_bytes"] for row in rows)
        return sum(row[key] * row["eval_bytes"] for row in rows) / total

    aggregate = {
        "weighted_frozen_neural_bpb": weighted(can_rows, "frozen_neural_bpb"),
        "weighted_adaptive_o2_bpb": weighted(can_rows, "adaptive-o2_bpb"),
        "weighted_adaptive_o3_bpb": weighted(can_rows, "adaptive-o3_bpb"),
        "weighted_zlib_bpb": weighted(can_rows, "zlib_bpb"),
        "weighted_zstd19_bpb": weighted(can_rows, "zstd19_bpb"),
        "adaptive_o3_beats_frozen_count": sum(r["adaptive-o3_bpb"] < r["frozen_neural_bpb"] for r in can_rows),
        "adaptive_o3_beats_zlib_count": sum(r["adaptive-o3_bpb"] < r["zlib_bpb"] for r in can_rows),
        "adaptive_o3_below_8_count": sum(r["adaptive-o3_bpb"] < 8.0 for r in can_rows),
    }

    results = {
        "experiment_id": "pilot-005-adaptive-pollicino",
        "base_commit": os.environ.get("GITHUB_SHA", "local"),
        "training_domain": "pollicino-self-v2-clean-git only",
        "external_fine_tuning": False,
        "neural_model": {
            "spec": model_spec.__dict__,
            "canonical_fingerprint": neural_fp.hex(),
            "checkpoint_bytes": training["checkpoint_bytes"],
            "best_validation_bpb": training["best_validation_bpb"],
        },
        "adaptive_configs": {name: {**cfg, "order_weights": list(cfg["order_weights"])} for name, cfg in ADAPTIVE_CONFIGS.items()},
        "prior_strengths": list(PRIOR_STRENGTHS),
        "aggregate": aggregate,
        "canterbury": can_rows,
        "artificial_controls": art_rows,
        "coding_checks": coding_rows,
        "protocol": {
            "adaptive_state_source": "decoded prefix only",
            "adaptive_state_transmitted": False,
            "gradient_updates": False,
            "coding_slice_bytes": SLICE,
            "neural_prior_precision_bits": PRECISION,
            "neural_prior_is_fixed_pseudocount_mass": True,
        },
        "sources": {
            "canterbury_archive_sha256": sha(can_archive),
            "artificial_archive_sha256": sha(art_archive),
        },
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    csvout(OUT / "canterbury.csv", can_rows)
    csvout(OUT / "artificial.csv", art_rows)
    csvout(OUT / "coding.csv", coding_rows)
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
