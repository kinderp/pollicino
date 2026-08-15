# PILOT-003 — Crossing the line

PILOT-003 asks whether POLLICINO can move from the near-tie observed in PILOT-002 to a **real range-coded payload and complete `.pol` file below zlib**, while separately measuring model capacity, integer-CDF precision and fixed container overhead.

## Methodological correction discovered by the pilot

The first clean GitHub Actions checkout could not regenerate the split hashes recorded by PILOT-001/002. The old experiments remain historical run records, but their original dataset bytes are not reconstructible from Git alone. See `../DATASET-PROVENANCE-ERRATA.md`.

PILOT-003 therefore establishes a new clean baseline, **`pollicino-self-v2-clean-git`**, generated from the clean checkout:

| split | bytes | SHA-256 |
|---|---:|---|
| train | 104189 | `6965b8665eaa4cfcf20703438adce522d6480401f0f608974a9f29ee9409a57c` |
| validation | 11742 | `575a1cbfd3544229a633408a23a86f5a72b006461cc443a8a7d82b7b11cfc5ec` |
| test | 15424 | `07c5a0a5c13a35a413a9eb0e94ee9926c8506754aafc5598e7e7e424a00d5d99` |

The `m48-l2` architecture that won PILOT-002 is rerun as an **internal control** on v2. Absolute PILOT-003 bpb values must not be interpreted as a continuation of the old v1 curve.

## Capacity sweep

All candidates use `context_length=32`. Quick selection uses validation only.

| model | params | validation bpb @150 |
|---|---:|---:|
| m64-l3 | 135616 | **3.8097** |
| m80-l2 | 148096 | 3.8166 |
| m72-l2 | 124096 | 3.8369 |
| m64-l2 | 102144 | 3.9633 |
| m56-l2 | 82240 | 4.0282 |
| m48-l2 control | 64384 | 4.0447 |

The top two were confirmed for 300 steps with seeds 1337, 2026 and 4242:

| model | mean validation bpb | std | mean train s |
|---|---:|---:|---:|
| **m80-l2** | **2.9767** | 0.0244 | 6.60 |
| m64-l3 | 3.1300 | 0.0453 | 7.50 |

Winner: **m80-l2**, 148096 parameters. A final seed-1337 run to 500 steps reaches **2.42545 validation bpb** and **2.00309 test bpb** on the 256-window reporting metric.

## Precision sweep — 2048 bytes

Float predictive cost is **1.70563 bpb**. Integer-CDF precision progressively closes the gap:

| precision | ideal quantized bpb |
|---:|---:|
| 12 | 1.79195 |
| 13 | 1.74779 |
| 14 | 1.72666 |
| 15 | 1.71605 |
| 16 | 1.71088 |
| 17 | 1.70825 |
| **18** | **1.70694** |

At 18 bits, quantization costs only about **0.00131 bpb** relative to the float model.

## Crossing zlib

The actual range coder is evaluated with precision 18. `POL1` uses its existing 92-byte header. Two research-only shared-model header measurements are also reported:

- `P2S1`: 61 bytes, full SHA-256 for decoded data + 128-bit model fingerprint;
- `P2T1`: 45 bytes, 128-bit truncated data/model fingerprints; sizing experiment only, weaker integrity.

| bytes | payload bpb | POL1 bpb | P2S1 bpb | zlib bpb | zstd19 bpb |
|---:|---:|---:|---:|---:|---:|
| 512 | 1.9824 | **3.4219** | 2.9375 | 4.5156 | 4.6719 |
| 1024 | 2.0713 | **2.7969** | 2.5547 | 3.9609 | 4.0938 |
| 2048 | 1.7075 | **2.0703** | 1.9492 | 2.9336 | 3.0000 |
| 4096 | 1.7888 | **1.9688** | 1.9082 | 2.9336 | 2.9395 |
| 8192 | 1.8568 | **1.9473** | 1.9170 | 2.6016 | 2.5684 |

On this **domain-specific clean self-corpus**, the actual payload, the compact safe container, and even the full 92-byte `POL1` beat zlib at every tested size from **512 to 8192 bytes**.

At 2048 bytes:

```text
float model             1.70563 bpb
+ integer quantization  0.00131
ideal integer CDF       1.70694
+ range coder           0.00058
actual payload          1.70752
+ POL1 fixed header     0.36279
POL1 complete           2.07031 bpb
zlib                    2.93359 bpb
```

The range coder remains effectively ideal. Capacity and reproducible data provenance, not entropy coding, are the dominant scientific variables.

## Reproducibility record

Successful one-shot GitHub Actions run: `31870566707`, head `6cafec9ee902cf9cf99e1616d367964d61a9b66e`. The complete original result artifact had digest `sha256:72a2f5c06088401f64d06f2aaead014a55015715b5dc1abb1b787567750d11b5`.

The temporary workflow used to execute the clean runner experiment is removed before merge. The checkpoint is not committed; `results.json` records SHA-256 and size.

## What this does *not* prove

- It does not show universal superiority over zlib or zstd.
- The corpus is self-referential and highly domain-specific.
- Absolute values are not directly comparable to PILOT-001/002 because their original dataset provenance is unresolved.
- Cross-backend PyTorch↔MLX integer-CDF identity remains unproven.
- Encode/decode still recompute Transformer context without a KV cache.

The next scientifically useful step is **external-domain validation**, not another victory lap on the self-corpus.
