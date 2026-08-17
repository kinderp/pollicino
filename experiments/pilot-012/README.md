# PILOT-012 — Block-Local Regret Routing

PILOT-011 showed that direct regret minimization under a deterministic neural-compute budget produces a useful file-level Pareto frontier. Its remaining structural limitation is that the route is irreversible for the whole stream.

## Scientific question

Can a lossless codec make a fresh deterministic cheap/neural decision at fixed block boundaries and thereby exploit **within-stream domain changes** better than one file-level decision, without selector side bits and without throwing away context already learned from the file?

## Codec change

`BlockLocalBitCreditRouterCDFProvider` creates a fresh PILOT-011 bit-credit **routing decision** at every fixed block boundary.

The important experimental control is that expert state is file-global:

- cheap and neural provider instances are created once per stream;
- both experts continue to see the complete decoded prefix of the file;
- only routing evidence and the route decision are reset at a block boundary;
- after a cheap rejection, neural compute stops for the rest of that block;
- when the next block begins, the neural expert can deterministically catch up from the complete prefix;
- encoder and decoder know block boundaries and reconstruct every route independently;
- selector side bits remain zero.

This isolates the value of **local re-routing** from the unrelated cost of resetting adaptive/neural context. `BlockResetCDFProvider` remains available only as an explicit ablation to measure what a full state reset would cost.

## Frozen inner policies

PILOT-012 does not retune activation/rejection thresholds. It imports the two feasible PILOT-011 policies exactly:

- `max`: min observations 4, max probe 32, activation credit 0 bits, rejection credit 12 bits;
- `balanced`: min observations 4, max probe 16, activation credit 8 bits, rejection credit 6 bits.

Their deterministic compute budgets remain:

- max `<= 1.00` mean specialist-call fraction;
- balanced `<= 0.50`.

The infeasible PILOT-011 fast budget is not silently relaxed.

## Development-only block-size choice

Candidate block sizes: `256`, `512`, `1024` bytes.

Four deterministic 4096-byte mixed development streams are built without fresh external data, using:

- the already-consumed self-v2 test bytes;
- generated JSON;
- generated DNA;
- random-64 / random-256 controls;
- repetition;
- zlib-compressed deterministic data;
- deterministic English-like prose.

For each frozen mode, select the block size with the lowest **real range-coded payload bpb** among candidates satisfying that mode's same deterministic mean specialist-call budget. Wall-clock time is not used for selection.

## Fresh holdout

Only after block sizes are frozen, two external source files never used by earlier POLLICINO pilots are downloaded:

- CPython `Lib/json/decoder.py` at tag `v3.11.15`, expected Git blob `c5d9ae2d0d5d040708f097fbf6450b86eef334dd`;
- Linux `kernel/sched/core.c` at tag `v6.6`, expected Git blob `802551e0009bf1ef66191441a802633bb57543bc`.

The downloaded bytes are verified against those Git blob IDs and their SHA-256 values are recorded.

Six 4096-byte holdout streams are then composed from those fresh source bytes plus deterministic JSON/DNA/random/repetition/compressed controls. Segment lengths are deliberately non-multiples of the candidate block sizes, so domain transitions do not line up neatly with block boundaries.

This is a **mechanism benchmark for mixed-domain routing**, not a universal compression benchmark.

## Comparisons

For every holdout stream:

- global cheap gate;
- global neural gate;
- PILOT-011 file-level `max` / `balanced`;
- PILOT-012 state-preserving block-local `max` / `balanced`;
- full-reset cheap and neural baselines as an ablation;
- a diagnostic full-reset per-block oracle, clearly separated from the primary state-preserving comparison;
- zlib;
- zstd level 19.

All selected PILOT-012 routes are verified with real encode/decode round-trips.

## Primary metrics

- real range-coded payload bpb;
- block-local versus file-level payload delta;
- specialist-call fraction;
- number of route switches;
- encode/decode time as a reported metric only.

The reset oracle is diagnostic only because it belongs to a different context model. It must not be used as the primary regret target for the state-preserving router.

## Success criterion

PILOT-012 is successful if state-preserving block-local routing produces a meaningful mixed-stream advantage over the corresponding PILOT-011 file-level mode on the fresh holdout, while preserving deterministic lossless decoding and an interpretable quality/compute frontier.

A negative result is equally useful: it would show that the additional probes caused by local re-routing cost more than the value of switching experts, and would motivate learned/dynamic block boundaries or a richer causal scheduler rather than silently changing model state.
