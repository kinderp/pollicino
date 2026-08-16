# PILOT-006 — Deterministic Expert Gate

PILOT-006 asks whether POLLICINO can keep the strong in-domain neural predictor from PILOT-003 while automatically falling back to causal adaptive models when the file is out of distribution — **without transmitting a selector stream**.

## Architecture

The final gate has four deterministic experts:

1. `adaptive-o3`: causal order-0/1/2/3 byte counts, weights `1/4/16/64`;
2. `frozen-neural`: the exact `m80-l2/context32` model from PILOT-003/005;
3. `neural-prior-256`: adaptive-o3 plus 256 neural pseudo-counts;
4. `neural-prior-1024`: adaptive-o3 plus 1024 neural pseudo-counts.

For each already-decoded byte, the gate records the exact likelihood term `(symbol_mass, total_mass)` from every expert. It compares rolling likelihood products with integer cross-multiplication. There are no floating-point decisions and ties are resolved by expert order. The expert for byte `i` is chosen only from evidence in bytes `< i`, so encoder and decoder reconstruct the same selector state without side bits.

Implementation: `src/pollicino/compression/gating.py`.

## Correctness

The independent GitHub Actions run executed:

```text
PYTHONPATH=src pytest -q \
  tests/test_gating.py tests/test_adaptive.py \
  tests/test_range.py tests/test_codec.py
```

Result: **26 passed**. The benchmark then performed separate encoder/decoder round-trips on all 14 Calgary holdout slices plus the regression controls.

## Development versus holdout

The rolling window was the only gate hyperparameter selected in this pilot. Windows `16`, `64`, and `256` were evaluated on representative Canterbury + Artificial slices already used in PILOT-005.

| window | mean development payload bpb |
|---:|---:|
| 16 | 3.0620 |
| 64 | 3.0534 |
| **256** | **3.0494** |

After choosing `256`, the gate was frozen. The **Calgary Corpus was then used as the untouched holdout**; it was not used to tune the gate.

## Calgary holdout — 2 KiB real lossless payloads

Mean across the 14 files:

| method | mean bpb |
|---|---:|
| pure adaptive-o3 | 4.0771 |
| **expert gate** | **3.8531** |
| zlib | **3.7623** |

The gate improves pure adaptive-o3 on **11/14** files and beats zlib at the payload level on **6/14** files. The current 92-byte `POL1` container beats zlib on only **1/14** of the 2 KiB slices (`geo`), so fixed file overhead remains material at this scale.

Selected examples:

| file | gate payload | adaptive-o3 | zlib |
|---|---:|---:|---:|
| `book1` | **4.1421** | 4.4727 | 4.4844 |
| `book2` | **3.9077** | 4.2646 | 4.1406 |
| `geo` | **5.2183** | 5.2183 | 5.5820 |
| `paper1` | **4.0483** | 4.4492 | 4.0938 |
| `paper2` | **4.2173** | 4.5430 | 4.4180 |
| `pic` | **0.0269** | 0.0269 | 0.0898 |
| `progl` | 3.2773 | 3.5381 | **2.6055** |

This is a genuine improvement over PILOT-005's universal adaptive fallback, but not yet an average win over zlib on the independent holdout.

## The key regression test: preserve the in-domain specialist

On the same 2048-byte `self-v2` test control used in PILOT-003:

| predictor | payload bpb |
|---|---:|
| PILOT-003 frozen neural reference | **1.7075** |
| **PILOT-006 gate** | **1.7095** |
| pure adaptive-o3 | 3.6958 |
| zlib | 2.9336 |

The gate chooses `frozen-neural` for **99.90%** of the bytes. Therefore robustness no longer destroys the domain-specific neural advantage.

On strong mismatch controls it does the opposite:

- `aaa.txt`: 100% adaptive-o3, 0.0264 bpb payload;
- `random.txt`: 100% adaptive-o3, 6.4253 bpb payload.

## What does the gate actually use on Calgary?

Across the holdout, the **direct frozen-neural expert is selected only about 0.34%** of bytes. However, the broader neural family — direct neural plus the two neural-prior adaptive experts — is selected about **75.02%** on average. This is important: the learned model still provides useful weak evidence for many text/code-like streams even when it is almost never trusted directly.

The flip side is economic and computational. The gate still requires the shared ~603 KB checkpoint, and on the GitHub Actions CPU runner a 2 KiB Calgary slice costs roughly 3 seconds to encode and 3 seconds to decode. Pure adaptive-o3 is dramatically cheaper.

## Interpretation

PILOT-004 showed that the frozen model is brittle out of distribution. PILOT-005 showed that causal adaptation repairs that brittleness. PILOT-006 now shows that a deterministic likelihood gate can combine the two behaviors:

```text
in-domain evidence
      -> frozen neural specialist

moderate mismatch
      -> neural-informed adaptive prior

strong mismatch
      -> pure adaptive-o3
```

The remaining question is no longer whether gating is possible. It is whether the small compression gain over pure adaptation justifies evaluating and distributing the neural checkpoint.

A strong next experiment is therefore **PILOT-007 — value of the neural expert**: compare the current gate against much cheaper expert sets (adaptive orders, byte-frequency, RLE/run expert, possibly a classical fallback) on the same frozen Calgary-style protocol, with an explicit objective such as `bpb + model-cost + compute-cost`. If a non-neural gate reaches almost the same compression, the neural model should not be in the universal codec path; it can remain a domain-specialist plugin.

## Reproducibility

Successful GitHub Actions run: `31933797186`  
Artifact: `9260112994`  
Artifact digest: `sha256:6a17937188865962b72ffd34e9a30060c8b73f1ae078472cb996622db773c538`

The run used PyTorch CPU with deterministic algorithms. The one-shot workflow is removed before merge. The external Calgary file sizes and SHA-256 values are frozen in `calgary-manifest.json`; aggregate and per-file results are in `results.json`.

## Limits

- gate window selected on Canterbury/Artificial development slices;
- Calgary comparisons use 2 KiB real round-trip slices for the gated codec;
- pure adaptive-o3 also has longer-prefix diagnostics, but the neural gate is not yet benchmarked over entire Calgary files because of decode cost;
- the neural checkpoint is assumed shared for `POL1`; it is not included in payload bpb;
- no claim of universal superiority over zlib/zstd is supported.
