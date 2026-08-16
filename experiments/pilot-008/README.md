# PILOT-008 — Automatic Specialist Routing & Cost-Aware Codec

PILOT-008 turns the architectural conclusion of PILOT-007 into an executable routing policy. POLLICINO now has a causal two-stage router that keeps a model-free universal path and activates a shared neural specialist only after observing evidence from a cheap-coded prefix.

## Router

`CostAwareSpecialistRouterCDFProvider` lives in `src/pollicino/compression/routing.py`.

For a stream of known length:

1. if the specialist is unavailable, use the cheap gate for the whole stream;
2. if the stream is below the configured cost threshold, use the cheap gate for the whole stream;
3. otherwise encode a fixed probe with the cheap gate while evaluating both cheap and specialist likelihoods;
4. compare the exact quantized likelihood products with integer arithmetic;
5. lock once to `cheap-gate` or `neural-gate`;
6. after a cheap lock, stop evaluating the neural specialist entirely.

Encoder and decoder reconstruct the same decision from the same already-decoded bytes. No selector side stream is transmitted.

The policy fingerprint commits to the two provider fingerprints, stream length, probe length, minimum stream size, and required evidence ratio.

## Primary policy

The primary policy was fixed before evaluating the new Large Corpus holdout:

- probe: **256 bytes**;
- activation threshold: specialist likelihood strictly greater than cheap likelihood (`1:1`);
- shared-model mode: no minimum stream length beyond the probe;
- self-contained mode: **67,067,460 bytes** minimum;
- selector side bits: **0**.

The self-contained threshold comes from the checkpoint-only break-even measured in PILOT-007. It does **not** include CPU, memory, or energy cost.

## Correctness

The benchmark run executed the routing tests together with the classical/adaptive/gating/range/codec suites:

- **40 tests passed** before benchmark results were accepted;
- separate encode/decode providers were used;
- model-unavailable and self-contained fallbacks were round-tripped;
- the router can stop calling a rejected specialist after the probe.

After the benchmark, an edge case was tightened: streams whose entire length fits inside the probe now lock to cheap immediately and do not initialize the specialist. A test-only independent run then passed **41 tests**. This change does not alter any recorded PILOT-008 benchmark sample because every evaluated sample is longer than the 256-byte primary probe.

## Silesia development / replication

Silesia was already consumed by PILOT-007, so it is **development data**, not a fresh holdout.

For the fixed primary policy over six 2 KiB prefixes:

| method | mean payload bpb |
|---|---:|
| cheap gate | 4.2118 |
| neural gate | **4.1398** |
| automatic router | 4.1715 |

The router selected the neural path on **6/6** files. This is the key negative result of the pilot: the `1:1` evidence threshold is too permissive.

Examples:

- `dickens`: neural really helps; router selects neural;
- `ooffice`: cheap is better (`1.3848` vs neural `1.4077`), yet the router selects neural;
- `x-ray`: cheap and neural are effectively tied, yet the router still pays neural compute.

A diagnostic probe ablation on the same already-consumed development corpus shows:

| probe | mean bpb | specialist routes |
|---:|---:|---:|
| 64 | 4.1684 | 5/6 |
| 128 | **4.1640** | 6/6 |
| 256 | 4.1715 | 6/6 |
| 512 | 4.1790 | 6/6 |

These numbers are diagnostic only. The primary policy is **not** changed after seeing the new holdout.

## New holdout — fixed Large Corpus subset

The new holdout is the fixed three-file subset `E.coli`, `bible.txt`, `world192.txt`. Only the first **4096 bytes** of each file are coded; full file sizes and SHA-256 values are retained in `large-manifest.json`.

| file | cheap | neural | router | route | zlib | zstd-19 |
|---|---:|---:|---:|---|---:|---:|
| `E.coli` | 2.0920 | 2.0911 | **2.0920** | cheap | 2.5605 | 2.1074 |
| `bible.txt` | 3.0425 | **2.9819** | 3.0271 | neural | 2.2207 | 2.1738 |
| `world192.txt` | 4.4448 | **4.2510** | 4.2954 | neural | 3.9453 | 3.9316 |

Mean across this explicitly fixed subset:

- cheap: **3.1931 bpb**;
- neural: **3.1080 bpb**;
- router: **3.1382 bpb**;
- zlib: 2.9089;
- zstd-19: 2.7376.

The qualitative routing is sensible: the nearly useless neural improvement on `E.coli` is rejected, while the larger text-domain gains on `bible.txt` and `world192.txt` activate the specialist.

On `E.coli`, routing cuts encode time to about **2.71 s** versus **6.62 s** for always-neural while preserving the cheap payload exactly. On the two neural-routed files, the probe makes the router slightly slower than simply choosing neural from the start.

## Availability and model-cost policies

The same files were evaluated under two additional policies:

- **model unavailable**: all files deterministically use the cheap gate;
- **self-contained checkpoint**: specialist activation is forbidden below the 67.1 MB checkpoint-only break-even.

All three Large Corpus files are below that self-contained threshold, so all three stay cheap in that mode.

This makes model availability and amortization first-class routing inputs rather than assumptions hidden outside the codec.

## Regression controls

### In-domain `self-v2`

The shared router correctly selects neural, but the fixed cheap probe is costly:

- router: **2.1738 bpb**;
- no-model cheap: 3.7002 bpb;
- previous always-neural gate reference: about **1.7095 bpb**.

So routing preserves the specialist decision but pays a substantial **probe tax** on strongly known domains.

### Strong repetition

`aaa.txt` routes cheap and remains at **0.0239 bpb**.

### Random 64-symbol data

The current policy routes neural even though its advantage is only about **0.001 bpb**. This is another direct signal that likelihood superiority alone is insufficient; activation needs a meaningful confidence/cost margin.

## Interpretation

PILOT-008 establishes the architecture, but not yet the optimal routing policy.

What works:

```text
model unavailable -> cheap only
small/self-contained stream -> cheap only
weak neural value (E.coli) -> cheap
clear text-domain value -> neural
strong repetition -> cheap
```

What does not yet work:

```text
tiny/negligible gain -> can still activate neural
strong in-domain case -> fixed cheap probe wastes bits
neural activation -> probe may cost more compute than always-neural
```

The next research step should therefore be **PILOT-009 — confidence-aware sequential routing**: stronger activation margins, early exit, and possibly a trusted-domain neural fast path. Large Corpus must now be considered consumed; the final policy should be tested on a new holdout.

## Reproducibility

Benchmark run:

- GitHub Actions run: `31941837032`
- artifact: `9262305581`
- artifact digest: `sha256:863d42926ffb0a34fff6273a89a06dd2d12eb3edeb6e4021007b56c3025a0b6f`
- benchmark core: **40 passed in 3.79s**

Post-run routing edge-case verification:

- GitHub Actions run: `31942331368`
- deterministic compression core: **41 passed in 3.87s**

The one-shot workflows and trigger files are removed before merge. Downloaded corpus archives and model checkpoints are not committed.
