# PILOT-012 — Block-Local Regret Routing

PILOT-011 showed that direct regret minimization under a deterministic neural-compute budget produces a useful file-level Pareto frontier. Its remaining structural limitation is that the route is irreversible for the whole stream.

## Scientific question

Can a lossless codec make a fresh deterministic cheap/neural decision at fixed block boundaries and thereby exploit **within-stream domain changes** better than one file-level decision, without selector side bits?

## Codec change

`BlockLocalBitCreditRouterCDFProvider` creates a fresh PILOT-011 bit-credit router at every fixed block boundary.

The block reset is part of the codec definition:

- each block starts with fresh cheap and neural expert state;
- only the bytes already decoded inside that block are visible to its experts;
- routing evidence is therefore block-local;
- after a cheap rejection, neural compute stops for the rest of that block;
- the next block starts from deterministic fresh state and may choose a different route;
- encoder and decoder know block boundaries and reconstruct every route independently;
- selector side bits remain zero.

This design deliberately trades some cross-block context for real compute savings and route flexibility. Because model state resets, the correct oracle is a **block-reset oracle**, not the file-level min(cheap, neural).

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
- PILOT-012 block-local `max` / `balanced`;
- block-reset cheap and neural baselines;
- block-reset per-block oracle `min(cheap, neural)`;
- zlib;
- zstd level 19.

All selected P12 routes are verified with real encode/decode round-trips.

## Primary metrics

- payload bpb;
- block-oracle regret;
- block-local versus file-level payload delta;
- specialist-call fraction;
- number of route switches;
- block-level chosen route versus block oracle;
- encode/decode time as a reported metric only.

## Success criterion

PILOT-012 is successful if block-local routing produces a meaningful mixed-stream advantage over the corresponding PILOT-011 file-level mode on the fresh holdout, while preserving deterministic lossless decoding and an interpretable quality/compute frontier.

A negative result is equally useful: it would show that block reset/context tax exceeds the value of local specialization and would argue for state-preserving chunk routing in POL2 instead.
