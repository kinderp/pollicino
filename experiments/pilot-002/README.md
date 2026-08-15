# PILOT-002 — Scaling & Context Sweep

PILOT-002 asks a narrower question than PILOT-001:

> On the frozen `pollicino-self-v1` dataset, is it more useful to spend compute on a larger byte Transformer or on a longer context window?

## Phase A — quick surface map

Three model sizes were tested with contexts 32, 64 and 128. Each run uses seed 1337, 80 optimizer steps and approximately 1024 training tokens per step. Context 256 is kept as a separate 20-step compute-frontier probe because its quadratic attention cost makes it non-comparable under the same small CPU pilot budget.

Best quick-sweep test bpb:

| model | context | params | test bpb |
|---|---:|---:|---:|
| medium | 32 | 64,384 | **3.7948** |
| medium | 64 | 65,920 | 3.8624 |
| medium | 128 | 68,992 | 3.9182 |
| base | 64 | 35,840 | 4.1396 |
| base | 32 | 34,816 | 4.1601 |

The early result is domain-specific but clear: on this corpus, **capacity helps more than extending context beyond 32**.

## Phase B — multi-seed confirmation

The three most informative configurations were retrained for 200 steps with seeds 1337, 2026 and 4242.

| configuration | params | mean test bpb | std | mean train s |
|---|---:|---:|---:|---:|
| medium-c32 | 64,384 | **3.3792** | 0.0240 | 5.24 |
| medium-c64 | 65,920 | 3.4769 | 0.0202 | 5.38 |
| base-c64 | 35,840 | 3.6583 | 0.0177 | 4.67 |

The medium/context-32 result is stable across seeds.

## Winner codec check

`medium-c32`, seed 1337, was trained for 300 steps and then connected to the same integer-CDF/range-coder pipeline used by PILOT-001 on the same frozen 2048-byte coding slice.

| layer | bpb |
|---|---:|
| float model | **2.9271** |
| quantized CDF ideal | 2.9368 |
| actual range payload | 2.9375 |
| full `.pol` file | 3.2969 |
| zlib | 2.9336 |
| gzip | 2.9805 |
| zstd -19 | 3.0234 |

This is the first POLLICINO run in which the **float predictive model slightly beats zlib** on the frozen slice. The advantage is not yet preserved by the final file: integer probability quantization costs about 0.0097 bpb and the current `POL1` container adds about 0.3594 bpb.

## Interpretation

The range coder itself is not the bottleneck. The next experiments should focus on:

1. improving predictive bpb by a small but robust margin;
2. shrinking/amortizing `POL1` metadata;
3. evaluating larger files/slices so fixed overhead matters less;
4. adding cached incremental decoding before scaling context further;
5. testing the winner on external corpora before making general claims.

All results remain domain-specific and exploratory. PILOT-002 is not evidence that the selected architecture is universally better than classical compression.
