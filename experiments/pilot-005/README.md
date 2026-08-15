# PILOT-005 — Adaptive POLLICINO

PILOT-005 tests whether causal file-local adaptation can recover from the severe out-of-distribution failure observed in PILOT-004 **without transmitting updated model weights**.

## Protocol

The neural model is frozen to the exact pre-PILOT-005 repository state: training corpus `pollicino-self-v2-clean-git` is reconstructed from commit `9c833cfb119fdfc941977abafc3fcb75e9e9c7ec` with `git archive`. This prevents the experiment code itself from changing the training set.

Two deterministic adaptive predictors are evaluated:

- `adaptive-o2`: order 0/1/2 byte counts with integer weights `1/4/16`;
- `adaptive-o3`: order 0/1/2/3 byte counts with integer weights `1/4/16/64`.

Every byte keeps positive base mass. The provider updates only from the already decoded prefix. A fresh decoder therefore reaches the same adaptive state without receiving a delta, gradient, seed or model update.

A second family adds the frozen Transformer only as a fixed pseudo-count prior (`64`, `256` or `1024` total prior counts). This tests whether the pretrained model is useful as a weak prior once online evidence becomes available.

## Correctness

The adaptive implementation lives in `src/pollicino/compression/adaptive.py`. The one-shot independent run executed `tests/test_adaptive.py`, `tests/test_range.py` and `tests/test_codec.py`: **22 tests passed** before any benchmark result was accepted. Separate provider instances were used for encode and decode round-trips.

## Main result — adaptation fixes catastrophic OOD mismatch

Weighted Canterbury evaluation:

| method | bpb |
|---|---:|
| frozen `m80-l2` neural model | 8.7590 |
| adaptive order 2 | 3.4540 |
| **adaptive order 3** | **3.2069** |
| zlib | 2.4647 |
| zstd-19 | 2.2195 |

`adaptive-o3` beats the frozen neural predictor on **11/11** Canterbury files and stays below 8 bpb on **11/11**. It still beats zlib on **0/11** full evaluation prefixes, so online adaptation repairs robustness but does not yet establish universal superiority over classical compression.

### Broad domains

| domain | frozen neural | adaptive-o3 | zlib | zstd-19 |
|---|---:|---:|---:|---:|
| text | 5.160 | **3.841** | 3.125 | 2.956 |
| source / markup | 6.953 | **3.687** | 2.488 | 2.420 |
| binary / structured | 14.842 | **2.097** | 1.421 | 1.014 |

The largest recovery is on binary/structured inputs, where the frozen model was catastrophically overconfident.

## Artificial controls

| file | frozen neural | adaptive-o3 | zlib | zstd-19 |
|---|---:|---:|---:|---:|
| `aaa.txt` | 10.3717 | **0.0010** | 0.0104 | 0.0023 |
| `alphabet.txt` | 9.6509 | **0.3856** | 0.0251 | 0.0054 |
| `random.txt` | 11.6402 | **6.0297** | 6.0590 | 6.0112 |

The `aaa.txt` result validates the original motivation for causal adaptation: after observing the repetition, encoder and decoder learn the same pattern without any side information. On random 64-symbol data the adaptive model is essentially competitive with zlib/zstd instead of catastrophically exceeding 8 bpb.

## Real range-coded 2 KiB slices

Representative payload results:

| file | frozen POL1 | adaptive-o3 payload | zlib |
|---|---:|---:|---:|
| `alice29.txt` | 5.2266 | 4.2158 | 4.0703 |
| `fields.c` | 6.4258 | 4.1450 | 3.5117 |
| `kennedy.xls` | 15.4883 | 4.3711 | 3.4805 |
| `ptt5` fax | 16.3633 | **0.0269** | 0.0898 |
| `sum` executable | 14.9570 | **2.6563** | 2.8711 |
| `aaa.txt` | 10.7266 | **0.0264** | 0.0898 |
| `random.txt` | 11.7773 | 6.4253 | 6.1523 |

The adaptive **payload** beats zlib on fax, the SPARC executable and repetition. The current 92-byte `POL1` header erases these small-slice wins: on the 2 KiB checks no complete POL1 file beats zlib. This makes compact container work a concrete next target rather than a theoretical optimization.

## Does the neural prior help?

Sometimes. On English and C source, a neural prior can improve the early adaptive stream: e.g. `alice29.txt` falls from 4.2158 bpb (`adaptive-o3`) to 3.9023 bpb payload at prior strength 1024, while `fields.c` reaches 3.9180 bpb at strength 256.

But the prior is harmful on strongly mismatched domains. On `kennedy.xls`, fax, executable, repetition and random data, larger prior strengths progressively make compression worse. It also requires the ~603 KB shared checkpoint and raises 2 KiB encode/decode time from roughly 0.1 s for pure adaptation to roughly 2.4–2.6 s on this CPU runner.

Therefore a fixed neural prior is **not** the universal answer. The next architecture should gate or attenuate it using evidence from bytes already decoded.

## Interpretation

PILOT-004 showed that a frozen learned predictor is brittle. PILOT-005 shows that a tiny deterministic online model can remove most of that brittleness and can even beat zlib at the payload level on some external regimes. The learned model remains potentially useful as a prior for text/code, but it must not be trusted equally across domains.

A natural next experiment is a deterministic **expert gate**: neural prior, adaptive order-2/order-3 and possibly uniform/classical fallback compete using only cumulative past evidence, so encoder and decoder choose the same expert without transmitting a selector stream.

## Reproducibility

Successful GitHub Actions run: `31907566414`  
Artifact: `9252819476`  
Artifact digest: `sha256:71fd7a5d7192793e4fdca764934c8a1c2d99c7bf56222d4b1eebb7b7bf1e1aec`

The one-shot workflow was removed before merge. The checkpoint and external corpus archives are not committed. The training commit, model fingerprint, corpus hashes, aggregate results and representative coding results are recorded in `results.json`.
