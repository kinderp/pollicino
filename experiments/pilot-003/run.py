from __future__ import annotations

import bz2
import copy
import csv
import gzip
import hashlib
import importlib.util
import json
import lzma
import math
import os
import random
import resource
import struct
import sys
import time
import zlib
from pathlib import Path
from statistics import mean, stdev

import torch
import torch.nn.functional as F
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

from pollicino.model_spec import ModelSpec, expected_parameter_count
from pollicino.backends.pytorch.model import ByteTransformer, parameter_count
from pollicino.compression.codec import encode_shared, decode_pol, inspect_pol
from pollicino.compression.format import header_size
from pollicino.compression.neural import PyTorchCDFProvider, torch_model_fingerprint
from pollicino.compression.quantization import probabilities_to_frequencies
from pollicino.compression.range_coder import decode_symbols

EXPECTED_SPLITS = {
    "train": {"bytes": 120539, "sha256": "eeeb4d5b4ed4b61bae10dfb07ba9425a9e984bb2055dee7d0fdab4e9952c52e8"},
    "validation": {"bytes": 14256, "sha256": "0b4304b27ce5c90055785b6ef6cb97c27a6cf7de030a63f5b6412e5f987f69b8"},
    "test": {"bytes": 12711, "sha256": "3ac9c682bacb359197c5070388509281ac49e775723805304dba341338b88a33"},
}
SEEDS = [1337, 2026, 4242]
LR = 0.003
BATCH = 32
CONTEXT = 32
QUICK_STEPS = 150
CONFIRM_STEPS = 300
FINAL_STEPS = 500
PRECISIONS = [12, 13, 14, 15, 16, 17, 18]
SIZE_SWEEP = [512, 1024, 2048, 4096, 8192]
CANDIDATES = {
    "m56-l2": dict(d_model=56, n_heads=4, n_layers=2, d_ff=112),
    "m64-l2": dict(d_model=64, n_heads=4, n_layers=2, d_ff=128),
    "m72-l2": dict(d_model=72, n_heads=4, n_layers=2, d_ff=144),
    "m80-l2": dict(d_model=80, n_heads=4, n_layers=2, d_ff=160),
    "m64-l3": dict(d_model=64, n_heads=4, n_layers=3, d_ff=128),
}
COMPACT_SAFE = struct.Struct(">4sBQ32s16s")
COMPACT_128 = struct.Struct(">4sBQ16s16s")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare_dataset() -> dict:
    source = ROOT / "experiments/pilot-001/prepare_data.py"
    spec = importlib.util.spec_from_file_location("pilot001_prepare", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    data_dir = HERE / "data"
    manifest = module.write_dataset(ROOT, data_dir)
    for split, expected in EXPECTED_SPLITS.items():
        blob = (data_dir / f"{split}.bin").read_bytes()
        actual = {"bytes": len(blob), "sha256": sha256(blob)}
        if actual != expected:
            raise RuntimeError(f"dataset drift for {split}: expected {expected}, got {actual}")
    return manifest


def model_spec(cfg: dict) -> ModelSpec:
    return ModelSpec(context_length=CONTEXT, **cfg)


def random_batch(data: bytes, spec: ModelSpec, batch_size: int, rng: random.Random):
    max_start = len(data) - spec.context_length - 1
    starts = [rng.randint(0, max_start) for _ in range(batch_size)]
    x = torch.tensor([list(data[s:s+spec.context_length]) for s in starts], dtype=torch.long)
    y = torch.tensor([list(data[s+1:s+spec.context_length+1]) for s in starts], dtype=torch.long)
    return x, y


def eval_bpb(model, data: bytes, spec: ModelSpec, max_windows: int = 128) -> float:
    starts = list(range(0, max(0, len(data)-spec.context_length-1), spec.context_length))[:max_windows]
    if not starts:
        raise ValueError("not enough evaluation data")
    losses = []
    model.eval()
    with torch.no_grad():
        for s in starts:
            x = torch.tensor([list(data[s:s+spec.context_length])], dtype=torch.long)
            y = torch.tensor([list(data[s+1:s+spec.context_length+1])], dtype=torch.long)
            logits = model(x)
            losses.append(float(F.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))))
    return mean(losses) / math.log(2.0)


def train_once(name: str, cfg: dict, seed: int, steps: int, train: bytes, val: bytes,
               *, keep_state: bool = False) -> dict:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    torch.manual_seed(seed)
    rng = random.Random(seed)
    spec = model_spec(cfg)
    model = ByteTransformer(spec)
    params = parameter_count(model)
    assert params == expected_parameter_count(spec)
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    best_val = float("inf")
    best_step = 0
    best_state = None
    history = []
    t0 = time.perf_counter()
    for step in range(1, steps + 1):
        model.train()
        x, y = random_batch(train, spec, BATCH, rng)
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
        loss.backward()
        opt.step()
        if step == 1 or step % 50 == 0 or step == steps:
            vb = eval_bpb(model, val, spec, 128)
            history.append({"step": step, "train_bpb": float(loss.detach())/math.log(2), "validation_bpb": vb})
            if vb < best_val:
                best_val = vb
                best_step = step
                if keep_state:
                    best_state = copy.deepcopy(model.state_dict())
    elapsed = time.perf_counter() - t0
    row = {
        "name": name, "seed": seed, "steps": steps, "spec": spec.__dict__,
        "parameter_count": params, "best_validation_bpb": best_val, "best_step": best_step,
        "train_seconds": elapsed, "steps_per_second": steps/elapsed,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0,
        "history": history,
    }
    if keep_state:
        row["_state"] = best_state
    return row


def float_and_precision_bpds(model, spec: ModelSpec, data: bytes, precisions: list[int]):
    float_bits = 0.0
    quant_bits = {p: 0.0 for p in precisions}
    prefix: list[int] = []
    model.eval()
    with torch.no_grad():
        for symbol in data:
            if not prefix:
                probs = [1.0 / 256.0] * 256
            else:
                ctx = prefix[-spec.context_length:]
                logits = model(torch.tensor([ctx], dtype=torch.long))[0, -1]
                probs = torch.softmax(logits, dim=-1).detach().cpu().double().tolist()
            float_bits += -math.log2(probs[symbol])
            for p in precisions:
                freqs = probabilities_to_frequencies(probs, p)
                quant_bits[p] += -math.log2(freqs[symbol] / (1 << p))
            prefix.append(symbol)
    n = len(data)
    return float_bits/n, {p: quant_bits[p]/n for p in precisions}


def baseline_sizes(data: bytes) -> dict[str, int]:
    cctx = zstd.ZstdCompressor(level=19)
    return {
        "raw": len(data),
        "zlib": len(zlib.compress(data, 9)),
        "gzip": len(gzip.compress(data, 9)),
        "bz2": len(bz2.compress(data, 9)),
        "xz_lzma": len(lzma.compress(data, preset=9)),
        "zstd19": len(cctx.compress(data)),
    }


def compact_safe_blob(data: bytes, payload: bytes, precision: int, fingerprint: bytes) -> bytes:
    return COMPACT_SAFE.pack(b"P2S1", precision, len(data), hashlib.sha256(data).digest(), fingerprint[:16]) + payload


def compact_128_blob(data: bytes, payload: bytes, precision: int, fingerprint: bytes) -> bytes:
    return COMPACT_128.pack(b"P2T1", precision, len(data), hashlib.sha256(data).digest()[:16], fingerprint[:16]) + payload


def decode_compact_safe(blob: bytes, model, spec: ModelSpec, fingerprint: bytes) -> bytes:
    magic, precision, original_size, data_sha, model_id = COMPACT_SAFE.unpack_from(blob)
    if magic != b"P2S1" or model_id != fingerprint[:16]:
        raise ValueError("compact header mismatch")
    provider = PyTorchCDFProvider(model, spec, precision_bits=precision, device="cpu")
    payload = blob[COMPACT_SAFE.size:]
    restored = bytes(decode_symbols(payload, original_size, provider))
    if hashlib.sha256(restored).digest() != data_sha:
        raise ValueError("compact decode integrity failure")
    return restored


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in fields})


def main():
    manifest = prepare_dataset()
    train = (HERE/"data/train.bin").read_bytes()
    val = (HERE/"data/validation.bin").read_bytes()
    test = (HERE/"data/test.bin").read_bytes()

    quick = []
    for name, cfg in CANDIDATES.items():
        row = train_once(name, cfg, 1337, QUICK_STEPS, train, val)
        quick.append(row)
        print("QUICK", name, row["parameter_count"], row["best_validation_bpb"], flush=True)
    quick.sort(key=lambda r: r["best_validation_bpb"])
    finalists = [r["name"] for r in quick[:2]]

    confirmation = []
    for name in finalists:
        cfg = CANDIDATES[name]
        runs = [train_once(name, cfg, seed, CONFIRM_STEPS, train, val) for seed in SEEDS]
        row = {
            "name": name,
            "spec": model_spec(cfg).__dict__,
            "parameter_count": runs[0]["parameter_count"],
            "seeds": SEEDS,
            "mean_validation_bpb": mean(r["best_validation_bpb"] for r in runs),
            "stdev_validation_bpb": stdev(r["best_validation_bpb"] for r in runs),
            "mean_train_seconds": mean(r["train_seconds"] for r in runs),
            "runs": runs,
        }
        confirmation.append(row)
        print("CONFIRM", name, row["mean_validation_bpb"], row["stdev_validation_bpb"], flush=True)
    confirmation.sort(key=lambda r: r["mean_validation_bpb"])
    winner_name = confirmation[0]["name"]
    winner_cfg = CANDIDATES[winner_name]

    final = train_once(winner_name, winner_cfg, 1337, FINAL_STEPS, train, val, keep_state=True)
    state = final.pop("_state")
    winner_spec = model_spec(winner_cfg)
    model = ByteTransformer(winner_spec)
    model.load_state_dict(state)
    model.eval()
    checkpoint = OUT/"winner.pt"
    torch.save(state, checkpoint)

    final_test_bpb = eval_bpb(model, test, winner_spec, 256)
    sample2048 = test[:2048]
    float_bpb, precision_bpds = float_and_precision_bpds(model, winner_spec, sample2048, PRECISIONS)
    precision_rows = [
        {"precision_bits": p, "float_model_bpb": float_bpb, "quantized_ideal_bpb": precision_bpds[p]}
        for p in PRECISIONS
    ]
    best_precision = min(PRECISIONS, key=lambda p: precision_bpds[p])

    fingerprint = torch_model_fingerprint(model, winner_spec)
    size_rows = []
    for n in SIZE_SWEEP:
        sample = test[:n]
        provider = PyTorchCDFProvider(model, winner_spec, precision_bits=best_precision, device="cpu")
        t0 = time.perf_counter()
        pol1 = encode_shared(sample, provider, fingerprint, precision_bits=best_precision)
        encode_seconds = time.perf_counter() - t0
        info = inspect_pol(pol1)
        payload = pol1[header_size():]
        p2s = compact_safe_blob(sample, payload, best_precision, fingerprint)
        p2t = compact_128_blob(sample, payload, best_precision, fingerprint)
        if n == 2048:
            restored = decode_pol(
                pol1,
                shared_provider=PyTorchCDFProvider(model, winner_spec, precision_bits=best_precision, device="cpu"),
                expected_model_fingerprint=fingerprint,
            )
            assert restored == sample
            assert decode_compact_safe(p2s, model, winner_spec, fingerprint) == sample
        bases = baseline_sizes(sample)
        row = {
            "bytes": n,
            "payload_bits": info["payload_bits"],
            "payload_bpb": info["payload_bpb"],
            "pol1_bytes": len(pol1),
            "pol1_bpb": len(pol1)*8/n,
            "compact_safe_header_bytes": COMPACT_SAFE.size,
            "compact_safe_bytes": len(p2s),
            "compact_safe_bpb": len(p2s)*8/n,
            "compact128_header_bytes": COMPACT_128.size,
            "compact128_bytes": len(p2t),
            "compact128_bpb": len(p2t)*8/n,
            "encode_seconds": encode_seconds,
        }
        for key, value in bases.items():
            row[f"{key}_bytes"] = value
            row[f"{key}_bpb"] = value*8/n
        size_rows.append(row)
        print("SIZE", n, row["payload_bpb"], row["compact_safe_bpb"], row["zlib_bpb"], flush=True)

    first_payload_below_zlib = next((r["bytes"] for r in size_rows if r["payload_bpb"] < r["zlib_bpb"]), None)
    first_compact_safe_below_zlib = next((r["bytes"] for r in size_rows if r["compact_safe_bpb"] < r["zlib_bpb"]), None)
    first_pol1_below_zlib = next((r["bytes"] for r in size_rows if r["pol1_bpb"] < r["zlib_bpb"]), None)

    results = {
        "experiment_id": "pilot-003-crossing-line",
        "base_commit": os.environ.get("GITHUB_SHA", "local"),
        "dataset": {k: {"bytes": EXPECTED_SPLITS[k]["bytes"], "sha256": EXPECTED_SPLITS[k]["sha256"]} for k in EXPECTED_SPLITS},
        "quick": [{k:v for k,v in r.items() if k != "history"} for r in quick],
        "finalists": finalists,
        "confirmation": confirmation,
        "winner": {
            "name": winner_name,
            "spec": winner_spec.__dict__,
            "parameter_count": parameter_count(model),
            "seed": 1337,
            "steps": FINAL_STEPS,
            "best_validation_bpb": final["best_validation_bpb"],
            "best_step": final["best_step"],
            "test_bpb_256_windows": final_test_bpb,
            "checkpoint_sha256": sha256(checkpoint.read_bytes()),
            "checkpoint_bytes": checkpoint.stat().st_size,
        },
        "precision_sweep_2048": precision_rows,
        "selected_precision_bits": best_precision,
        "size_sweep": size_rows,
        "crossing": {
            "first_tested_payload_below_zlib_bytes": first_payload_below_zlib,
            "first_tested_compact_safe_below_zlib_bytes": first_compact_safe_below_zlib,
            "first_tested_pol1_below_zlib_bytes": first_pol1_below_zlib,
        },
        "header_variants": {
            "POL1_bytes": header_size(),
            "P2S1_compact_safe_bytes": COMPACT_SAFE.size,
            "P2T1_compact128_bytes": COMPACT_128.size,
            "P2S1_integrity": "full SHA-256 data + 128-bit model fingerprint",
            "P2T1_integrity": "128-bit truncated data and model fingerprints; research only",
        },
        "notes": [
            "selection uses validation, not test",
            "all results are domain-specific to pollicino-self-v1",
            "compact headers are experimental shared-model-only formats, not production POL1 replacements",
        ],
    }
    (OUT/"results.json").write_text(json.dumps(results, indent=2) + "\n")

    write_csv(OUT/"quick.csv", quick,
              ["name","parameter_count","best_validation_bpb","best_step","train_seconds","steps_per_second","peak_rss_mib"])
    conf_rows = [{
        "name": r["name"], "parameter_count": r["parameter_count"],
        "mean_validation_bpb": r["mean_validation_bpb"], "stdev_validation_bpb": r["stdev_validation_bpb"],
        "mean_train_seconds": r["mean_train_seconds"]
    } for r in confirmation]
    write_csv(OUT/"confirmation.csv", conf_rows,
              ["name","parameter_count","mean_validation_bpb","stdev_validation_bpb","mean_train_seconds"])
    write_csv(OUT/"precision.csv", precision_rows,
              ["precision_bits","float_model_bpb","quantized_ideal_bpb"])
    write_csv(OUT/"size-sweep.csv", size_rows, list(size_rows[0].keys()))
    (OUT/"dataset-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(results["winner"], indent=2), flush=True)


if __name__ == "__main__":
    main()
