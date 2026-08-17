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

This design deliberately trades some cross-block context for honest compute accounting and route flexibility. A state-preserving variant is scientifically different: with the current stateful expert gates it would have to replay skipped bytes when the specialist wakes up, so that catch-up compute must be counted explicitly. We leave that variant for a separate experiment rather than hiding its cost inside PILOT-012.

Because model state resets, the correct oracle for this pilot is a **block-reset oracle**, not the file-level min(cheap, neural).

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

### Development result

For `max` the candidate means were:

| block | mean payload bpb | mean specialist-call fraction |
|---:|---:|---:|
| 256 B | 3.9470 | 0.6753 |
| **512 B** | **3.8411** | 0.6433 |
| 1024 B | 3.8531 | 0.6329 |

`max` therefore freezes **512 B** before the fresh holdout.

For `balanced`, none of the three block sizes satisfies the inherited `<= 0.50` compute budget:

| block | mean payload bpb | mean specialist-call fraction |
|---:|---:|---:|
| 256 B | 3.9570 | 0.6411 |
| 512 B | 3.8453 | 0.6333 |
| 1024 B | 3.8550 | **0.6281** |

The `balanced` block-local mode is therefore recorded as **development-budget-infeasible** and is not relaxed after development.

## Fresh holdout

Only after block sizes are frozen, two external source files never used by earlier POLLICINO pilots are downloaded:

- CPython `Lib/json/decoder.py` at tag `v3.11.15`, Git blob `c5d9ae2d0d5d040708f097fbf6450b86eef334dd`;
- Linux `kernel/sched/core.c` at tag `v6.6`, Git blob `802551e0009bf1ef66191441a802633bb57543bc`.

The downloaded bytes match the frozen Git blob IDs. The run records their exact sizes and SHA-256 values.

Six 4096-byte holdout streams are composed from those fresh source bytes plus deterministic JSON/DNA/random/repetition/compressed controls. Segment lengths are deliberately non-multiples of 512 B, so domain transitions do not line up neatly with block boundaries.

This is a **mechanism benchmark for mixed-domain routing**, not a universal compression benchmark.

## Fresh holdout result

Mean payload bpb across the six mixed streams:

| method | mean bpb |
|---|---:|
| block-reset oracle | **4.2313** |
| block-reset neural | 4.2303 |
| **PILOT-012 max / 512 B** | **4.2569** |
| global neural | 4.5004 |
| PILOT-011 max file-level | 4.5546 |
| global cheap | 4.6655 |
| block-reset cheap | 4.6860 |
| zlib | **3.9964** |
| zstd-19 | **3.8783** |

PILOT-012 `max` beats the corresponding PILOT-011 file-level route on **6/6 streams**. The average improvement is **0.2977 bpb**, about **6.54%** relative to the file-level P11 payload.

The block router is close to its own block-reset oracle:

- mean block-oracle regret: **0.02555 bpb**;
- correct block route: **43/48 blocks (89.6%)**;
- mean route switches: **2.0 per 4096-byte stream**.

This establishes that local re-routing is useful on the deliberately mixed streams.

However it does **not** create a new universal-compression claim: zlib and zstd-19 remain better on average on this holdout.

## Compute interpretation

PILOT-012 `max` uses a mean specialist-call fraction of **0.8428** on the fresh holdout. The corresponding P11 file-level `max` averages **0.8346** there, so block-local routing buys its large compression improvement at roughly the same — slightly higher — neural-call budget, not by reducing compute versus P11.

Relative to always evaluating the neural path, P12 still avoids about 15.7% of specialist calls.

The more important negative result is `balanced`: repeated probing at every block boundary makes the inherited 50% budget infeasible even at 1024 B. A production block codec therefore cannot simply restart a full expensive probe in every small chunk and expect the P11 balanced budget to survive.

## Context-reset observation

On this constructed mixed-domain holdout, resetting neural state every 512 B is **beneficial**, not a net tax: block-reset neural averages 4.2303 bpb versus 4.5004 for global neural. The likely reason is that hard domain changes make stale cross-block context harmful.

The cheap path behaves differently: block reset slightly worsens it (4.6860 versus 4.6655 global cheap). This reinforces that reset policy should be treated as an architectural choice, not assumed to have one universal effect.

## Correctness and provenance

Scientific run:

- GitHub Actions run: `31987271468`;
- scientific head: `111e3ea7204bccad8bf41846d7e026cbbe3609af`;
- **67 tests passed** before the benchmark;
- artifact: `9274272450`;
- artifact digest: `sha256:62434b6164f88c021c15fce707293b06c423ba2ff5b90f61a8f960140b8ef11c`;
- exact PILOT-003 checkpoint fingerprint remains `354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`.

An earlier true-reset attempt stopped in the test suite because a test left over from an intermediate state-preserving implementation asserted the wrong state semantics. The fresh holdout was not opened by that failed run. The obsolete test was replaced with a true-reset invariant before the successful scientific run.

## Conclusion

**Positive for block-local specialization; negative for naively preserving the P11 balanced budget.**

PILOT-012 demonstrates that re-routing inside a mixed stream can recover a substantial amount of compression quality and track a block oracle closely. It also exposes the next architectural problem: repeated shadow evaluation/probing at every block boundary consumes too much neural compute for a balanced mode.

The next experiment should therefore not add another threshold. It should test **state-preserving or low-cost block admission with explicit catch-up accounting**, separating:

1. expert prediction state;
2. cheap routing features used every block;
3. expensive neural evaluation invoked only when a cheap admission signal says the block is worth probing.

That is the design direction most relevant to a future POL2 chunked codec.
