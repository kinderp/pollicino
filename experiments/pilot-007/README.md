# PILOT-007 — Value of the Neural Expert

PILOT-007 asks a cost-aware question: **does the neural expert in POLLICINO justify its model and compute cost compared with a deterministic non-neural gate?**

The experiment keeps the same zero-side-bit deterministic gating idea from PILOT-006 and changes the expert portfolio. No scalar score such as `bpb + seconds` is invented; results are treated as a **Pareto frontier** over compression, container size, model bytes and runtime.

## Compared systems

### Cheap gate — no learned model

Five causal deterministic experts:

1. adaptive order 0;
2. adaptive order 1;
3. adaptive order 2;
4. adaptive order 3;
5. run-length/repetition expert.

The cheap gate uses the same exact-integer rolling likelihood selection as PILOT-006 and transmits **0 selector bits**. It needs no checkpoint and no neural inference. The only tuned parameter is the rolling window; Canterbury + Artificial development slices select **window 64** from 16/64/256.

### Neural gate — PILOT-006 reference

Four experts:

1. adaptive-o3;
2. frozen `m80-l2` neural model;
3. neural-prior-256;
4. neural-prior-1024.

It uses window 256 and requires the shared **603,105-byte** neural checkpoint.

## Correctness

Before benchmarking, the one-shot GitHub Actions run executed the cheap/classical, gating, adaptive, range-coder and codec tests: **34 tests passed**. Every benchmarked gated file is encoded and decoded with separate provider instances and must round-trip byte-for-byte.

## Calgary replication — 14 files, 2 KiB each

| metric | cheap gate | neural gate | zlib |
|---|---:|---:|---:|
| mean payload bpb | **4.0747** | **3.8531** | **3.7623** |

The neural gate beats the cheap gate on **11/14** files; the cheap gate wins on **3/14**. Neural saves about **0.2217 bpb** on average. Because historical PILOT-006 did not persist per-file timing values, Calgary is used only for compression replication; same-run timing is measured on Silesia below.

At the Calgary mean bpb delta, a 603,105-byte checkpoint needs roughly **20.8 MiB** of data under the same shared model just to amortize its transmitted byte cost.

## New holdout — Silesia

Six heterogeneous Silesia files are downloaded independently and verified by exact size/SHA-256: English text, Windows DLL, MySQL database, Polish PDF, XML and medical X-ray. Neither gate is tuned on Silesia. Only the first 2 KiB of each verified source file is coded in this pilot.

| metric | cheap gate | neural gate | zlib | zstd-19 |
|---|---:|---:|---:|---:|
| mean payload bpb | **4.2118** | **4.1398** | 3.7591 | 3.7409 |
| mean encode seconds | **0.701** | 2.912 | — | — |
| mean decode seconds | **0.705** | 2.938 | — | — |
| checkpoint bytes | **0** | **603,105** | — | — |

The neural gate improves mean Silesia payload by only **0.0719 bpb**, while taking about **4.16×** the encode time and **4.17×** the decode time.

At that observed bpb advantage, the checkpoint break-even is about **67.1 MB (64.0 MiB)**. This is only the byte-amortization threshold; it does not compensate for extra compute or memory.

### Per-file Silesia result

| file | cheap bpb | neural bpb | zlib bpb | winner cheap/neural |
|---|---:|---:|---:|---|
| `dickens` | 4.3579 | 4.0498 | 4.0586 | **neural** |
| `ooffice` | 1.3848 | 1.4077 | 1.6016 | **cheap** |
| `osdb` | 6.2798 | 6.2661 | 6.0469 | **neural** |
| `reymont` | 3.7275 | 3.6948 | 2.6836 | **neural** |
| `xml` | 3.5425 | 3.4424 | 2.3477 | **neural** |
| `x-ray` | 5.9780 | 5.9780 | 5.8164 | **tie** |

## Regression controls

The trade-off is not uniform across domains. On the frozen `self-v2` control the neural gate remains a true specialist: **1.7095 bpb** versus **3.7002 bpb** for the cheap gate. On a long repeated byte stream the cheap gate is slightly better (0.0239 vs 0.0264 bpb), and on random-64-symbol data the two are effectively tied (~6.426 bpb).

## Model amortization

The neural checkpoint alone contributes approximately:

- **2355.88 bpb** if sent for a single 2 KiB file;
- **4.60 bpb** over 1 MiB;
- **0.046 bpb** over 100 MiB;
- **0.0045 bpb** over 1 GiB.

Therefore a shared/preinstalled model assumption is essential. On generic data, using the neural path for small independent files is economically unjustified even when its payload is slightly smaller.

## Interpretation

PILOT-007 does **not** show that neural compression is useless. It shows that the neural model has a different role:

```text
universal / unknown file
        -> cheap adaptive/classical gate

known or likely matching domain
        -> optional shared neural specialist

large stream with pre-shared model
        -> neural gate can amortize its cost
```

This is a Pareto result: the cheap gate dominates on model size and runtime; the neural gate often wins modestly on bpb and wins dramatically on its own training domain. A universal POLLICINO codec should therefore **not require the neural checkpoint**. The learned model should be an optional specialist activated when it is already shared or when enough data will be compressed to amortize it.

## Reproducibility

Successful GitHub Actions run: `31940184528`  
Artifact: `9261834437`  
Artifact digest: `sha256:84f2d055d0727c1a654faca7e11a240f634bc88da6aa9c9fedcf9f79b648434c`  
Tests: **34 passed**.

The one-shot workflow is removed before merge. Downloaded corpora and model checkpoints are not committed; source file sizes/hashes are frozen in `silesia-manifest.json`.

## Limits

- 2 KiB slices are intentionally small and magnify header/model economics;
- the cheap gate window was selected on already-consumed Canterbury/Artificial development data;
- Calgary is a replication corpus from PILOT-006, while Silesia is the new holdout for this pilot;
- Silesia timings are CPU-runner timings, not hardware-independent performance numbers;
- full-file Silesia neural coding is not yet attempted because the current autoregressive implementation lacks efficient incremental caching.
