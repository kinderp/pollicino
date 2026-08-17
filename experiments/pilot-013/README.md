# PILOT-013 — Cheap Admission Before Neural Compute

PILOT-012 established that 512-byte block resets are valuable on mixed-domain streams, but its regret router still starts a neural probe in every block. That made the frozen `balanced` target (`<= 0.50` specialist coverage) infeasible even before a fresh holdout was opened.

PILOT-013 asks a narrower question:

> Can cheap-only causal evidence decide which blocks are worth waking the neural path for, while enforcing a hard 50% neural-coverage budget and retaining most of the block-reset compression gain?

## Why this pilot exists

PILOT-012 selected 512-byte blocks and improved its fresh mixed holdout from 4.5546 bpb (file-level max router) to 4.2569 bpb, but the always-reset neural gate reached 4.2303 bpb. The useful interpretation is therefore a quality/compute problem: block reset repairs domain-contaminated context, while routing must decide where neural compute is worth paying for.

A retrospective 50%-block oracle on the already-consumed PILOT-012 blocks retains roughly 80% of the cheap-reset -> neural-reset payload gain. The budget is therefore worth attempting rather than structurally impossible.

## Codec mechanism

`CheapCodelengthAdmissionBlockCDFProvider` uses no neural model during admission:

1. reset the cheap gate at a deterministic 512-byte block boundary;
2. encode the first `K` bytes with the cheap gate only;
3. accumulate the exact quantized likelihood of those observed bytes;
4. compare the resulting cheap codelength with a frozen integer-bit band;
5. lazily construct the neural gate only when the block lies inside that band and the remaining stream-level admission budget can pay for the whole block;
6. otherwise keep the block cheap-only.

The likelihood-band comparisons use integer products and powers of two; no floating-point decision and no selector side stream are required.

## Hard compute budget

For every 4096-byte stream:

- block size: 512 bytes (frozen from PILOT-012);
- admitted-byte cap: 2048 bytes;
- therefore at most four full blocks can instantiate the neural path.

The frozen PyTorch prior now reports actual cache-miss model forwards as `model_evaluations`. Multiple neural-gate experts share one prior, so repeated requests for the same context are cache hits rather than extra model forwards. The primary compute metric is:

`actual neural model evaluations / source bytes`

The admitted-byte cap also gives a structural upper bound of 0.50 for this model family, even when a newly admitted stateful specialist has to replay the cheap probe prefix.

## Development data and policy search

No PILOT-013 holdout source is opened during selection. Development reconstructs the six now-consumed PILOT-012 mixed streams (CPython + Linux + deterministic controls).

Frozen candidates:

- probe lengths: 16, 32, 64 bytes;
- lower/upper cheap-codelength bands on a coarse 0.5 bpb grid;
- hard admitted-byte cap: 2048 bytes.

For efficiency, each development block precomputes cheap-only, neural-only and probe-then-neural outcomes for each probe length. All codelength bands are screened from those reusable outcomes. The best few policies are then validated with real whole-stream range coding, and the real lowest-payload policy is frozen before the new holdout is downloaded.

### Policy frozen before holdout

GitHub Actions run `31988642119` completed all development selection and emitted the frozen policy **before** attempting fresh-source verification:

- probe: 16 bytes;
- cheap probe codelength band: 88–128 bits, i.e. 5.5–8.0 bpb;
- maximum admitted bytes: 2048 (50%).

That run then aborted on the first fresh-source Git-blob check because the preregistered source identifiers were incorrect. No fresh holdout stream was composed or coded and no holdout metric was produced. `frozen-policy.json` records the freeze event. The provenance-correction rerun uses `run_frozen.py`, which reruns the original development procedure, asserts that it reproduces this exact policy, and refuses to download the fresh sources if the policy drifts. The policy is **not retuned** after the failed provenance check.

## Fresh holdout

Only after the frozen policy has been re-verified, download and verify two sources never used by earlier POLLICINO pilots:

- Go `src/net/http/server.go`, tag `go1.22.12`, Git blob `23a603a83dd7135077fa1363ceb8255ff345ac06`;
- Node.js `lib/internal/modules/cjs/loader.js`, tag `v20.19.1`, Git blob `ebccdb28256314e7cd8ac8d7e3dec670286022d2`.

These identifiers were independently re-read from GitHub's tagged file metadata after the first run's provenance guard rejected the original annotations.

Six deterministic 4096-byte mixed streams combine those bytes with JSON, DNA, random, repetition, compressed and English-like controls. Segment boundaries are deliberately not aligned to 512 bytes.

## Fresh-holdout comparisons

- block-reset cheap gate;
- block-reset neural gate;
- PILOT-012 512-byte `max` regret router, now with actual neural-forward accounting;
- PILOT-013 frozen cheap-admission router;
- a diagnostic 50%-budget block oracle using the same probe-then-neural mechanism;
- zlib;
- zstd level 19.

All primary POLLICINO rows use real range-coded payloads. The diagnostic block oracle is explicitly identified as a block-sum/non-causal reference and is not treated as a deployable codec.

## Primary metrics

- real payload bpb;
- actual neural model evaluations per source byte;
- admitted byte fraction;
- retained fraction of the cheap-reset -> neural-reset compression gain;
- regret to the 50%-budget diagnostic oracle;
- round-trip correctness and deterministic encoder/decoder block summaries.

## Success criterion

PILOT-013 succeeds if the frozen policy:

1. preserves deterministic lossless round-trip coding with zero selector side bits;
2. stays at or below 0.50 actual neural evaluations per source byte on every fresh stream;
3. improves the mean fresh-holdout payload over the block-reset cheap baseline;
4. retains at least **50% of the mean cheap-reset -> neural-reset compression gain** on the fresh holdout.

The 50% retained-gain threshold was frozen before the Go/Node holdout was accepted. A negative result is useful: if cheap codelength cannot identify valuable neural blocks, the next experiment should add richer cheap-only causal features or a tiny learned admission model rather than silently increasing neural compute.
