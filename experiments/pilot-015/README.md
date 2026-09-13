# PILOT-015 — Longer Cheap-Only Observation Horizon

## Preregistration

PILOT-014 found that richer cheap-only features at a 16-byte causal horizon
did not solve neural admission: its final `unique_count(first 16 bytes) <= 12`
rule retained 45.852954% of the mean cheap-reset to neural-reset gain and did
not beat PILOT-013 on its fresh mixed-domain holdout. PILOT-015 isolates the
next smallest architectural question: does observing exactly 32 cheap-only
bytes provide enough additional causal evidence to allocate the same limited
neural compute better?

The single primary change is:

```text
PILOT-014 observation horizon = 16 bytes
PILOT-015 observation horizon = 32 bytes
```

The feature family and selector form are frozen to the PILOT-014 winner. The
only deployed feature is:

```text
unique_count_32 = number of distinct byte values among the first
                  32 already-consumed bytes of the current 512-byte block
```

The selector is one deterministic integer split: admit neural exactly when
`unique_count_32 <= T` and the causal per-stream budget permits the complete
block. It uses zero transmitted bytes and must be reproduced independently by
encoder and decoder. It may inspect no byte at offset 32 or later (the 33rd
block byte onward), invoke no neural provider before admission, or use any
floating-point runtime route decision.

### Frozen candidate grid and development selection

The only development-calibrated parameter is one integer threshold:

```text
T in {20, 22, 24, 26, 28, 30}
```

This narrow even grid brackets the proportional translation of PILOT-014's
`12/16 = 0.75` concentration boundary to `24/32`, while testing modestly more
selective and permissive counts. The grid will not be expanded after candidate
performance is observed. No codelength, entropy, repetition, transition,
surprise, deeper tree, linear scorer, model, probe length, or budget fallback
is permitted in this pilot.

Threshold selection uses only the already-consumed PILOT-012/013 development
stream lineage. Every candidate is evaluated through the real range-coded
codec and must satisfy the actual uncached PyTorch forward-evaluation ceiling
on every development stream. Deterministic selection order is:

1. lower mean real payload bpb;
2. lower mean actual neural evaluation fraction;
3. lower threshold (the more conservative admission rule).

Before candidate scoring, the harness must reproduce PILOT-013 and the frozen
PILOT-014 rule `unique_count_16 <= 12`, including PILOT-014 policy digest
`02cb5a4fd9fb2d3695af55a874aff6ad2a4b49599af9d396878ef7cde116aa85`.
Failure is classified as `K. INHERITED_PILOT014_CORRECTNESS_BUG` and stops the
experiment.

### Frozen architecture and accounting

- predecessor/base SHA: `91276bcdf9211a70605e11ee61fb713b16924f2b`;
- block size: 512 bytes;
- cheap observation horizon: 32 bytes;
- hard admitted-byte budget: 2048 of each 4096-byte stream;
- hard actual neural-evaluation fraction: at most 0.50 on every stream;
- cheap predictor, neural model/checkpoint, range coder and codec semantics:
  unchanged;
- neural model fingerprint:
  `354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`;
- checkpoint SHA-256:
  `713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7`;
- selector side bits: zero;
- feature work: 32 bounded histogram updates, at most 32 histogram entries,
  one unique-count extraction, one integer split comparison and one causal
  budget comparison.

Every uncached neural forward used to synchronize specialist state after an
admission decision is counted. The harness will measure model evaluations
immediately before the decision and after the first specialist output, report
explicit catch-up evaluations, the first neural-coded byte, 32 cheap-coded
probe bytes per block, and the remaining 480 bytes in a full admitted block.
The extra 16 cheap-coded bytes relative to PILOT-014 are part of the measured
whole-codec result and are not treated as free.

### Frozen hypotheses and success contract

Primary hypothesis: with model, codec, selector family, 512-byte block and
hard compute budget held fixed, the 32-byte horizon retains at least 50% of the
mean cheap-reset to neural-reset coding gain on a fresh registered six-stream
holdout and has lower mean payload bpb than frozen PILOT-014 rerun on that same
holdout.

The secondary win criterion is that PILOT-015 beats PILOT-014 on at least four
of six streams. Secondary mechanism hypotheses are that the added evidence can
outweigh delayed activation, remains useful within the unchanged budget, costs
far less than neural inference, and helps without greater selector complexity.

The full correctness contract is zero roundtrip failures, zero SHA-256
mismatches, zero side bits, zero future-byte reads, zero neural evaluations
before admission, zero search/deployed decision divergences, zero holdout
retuning, and no per-stream compute-budget violation.

### Fresh-data firewall

Fresh source identities and six deterministic 4096-byte mixed-stream recipes
will be preregistered only after the threshold, implementation and development
reproduction are frozen and committed. Source selection will use predefined
project/domain criteria, not observed compressibility, and will exclude every
source consumed by PILOT-001 through PILOT-014, including Rust 1.80.0
`library/std/src/io/mod.rs` and SQLite 3.46.0 `src/json.c`. Before metrics, each
source must match its preregistered byte size, SHA-256 and Git blob identity.
Any provenance mismatch stops before measurement and permits provenance-only
correction followed by complete frozen-development reproduction.

On the fresh holdout the fixed runtime evaluates cheap reset, neural reset,
PILOT-012 max, PILOT-013, PILOT-014, PILOT-015, fixed-budget diagnostic oracles,
zlib-9 and zstd-19. The report will separate selection quality from 16-byte
additional activation delay by comparing horizon-matched forced neural block
outcomes and oracle gaps. Holdout labels cannot change the threshold or policy.

## Status

Development selection complete and policy frozen for fresh-holdout
preregistration. Fresh holdout content has not been accessed.

## Development selection

The frozen P13 and P14 development baselines reproduced exactly before any
P15 candidate was scored. P13 reproduced at 4.43658447265625 bpb and
0.4376220703125 actual neural evaluations per byte on the four inherited
validation streams. P14 reproduced at 4.404296875 bpb and
0.44097900390625, with its required policy digest and exact
`unique_count_16 <= 12` rule.

All six preregistered P15 thresholds were then evaluated on all twelve
already-consumed P12/P13 development streams (96 blocks) through the real
encoder and decoder. Every candidate had zero search/codec route mismatches,
zero budget violations, and a maximum per-stream actual neural-evaluation
fraction of 0.4990234375. The preregistered objective selected:

```text
if unique_count_32 <= 20 and complete-block budget permits:
    neural
else:
    cheap
```

It achieved 4.613993326822917 mean development bpb and 0.4591878255208333
mean actual neural evaluations per byte. The next payloads were 4.6161499023
for thresholds 22 and 24, 4.6197306315 for 26, 4.6200154622 for 28, and
4.6299641927 for 30. All thresholds spent the complete 50% admitted-byte cap.

The development evidence is already cautionary: frozen P14 achieved
4.567362467447917 bpb over the same twelve streams. P15 also had lower
horizon-matched fixed-budget route accuracy (54.17% versus 58.33%) and higher
mean oracle regret (326.42 versus 280.08 independently coded block bits). This
does not alter the preregistered fresh-holdout protocol or the selected rule.

Activation instrumentation found zero neural evaluations before either
decision. The inherited specialist performs counted state synchronization on
first use: P14 had 15 catch-up evaluations before its first current-byte output
and P15 had 31. Thus the extra context is not hidden or free. The first
neural-coded byte moves from ordinal 17 to 33, leaving 480 rather than 496
neural-coded bytes in a full admitted block. Holding a block route fixed, the
32-byte horizon cost 26.3229166667 more payload bits per independently coded
development block on average.

The frozen policy digest is
`ee0aa7a13a0b24f7b3c978ee40e25a05376e734206e3cdf9df1d30c3ac39b28e`.

