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

Closed. The primary hypothesis failed. Classification:
`PILOT015_ADMISSION_DELAY_NEGATES_SIGNAL_GAIN`.

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

## Fresh-holdout preregistration

After the policy freeze and before file-content access, the following two
sources were selected by project maturity and parser/structured-data domain,
not by measured compressibility:

- LLVM 18.1.8 (`3b5b5c1ec4a3095ab096dd780e84d7ab81f3d7ff`),
  `clang/lib/Parse/ParseStmt.cpp`, expected 99,531 bytes and Git blob
  `d0ff33bd1379ab727bdf712ad2ebee58f64f9149`;
- PostgreSQL 16.4 (`2caa85f4aae689e6f6721d7363b4c66a2a6417d6`),
  `src/backend/utils/adt/jsonfuncs.c`, expected 150,652 bytes and Git blob
  `70cb922e6b7aa45629483bb64d3380d07a1e81a0`.

GitHub commit and tree metadata supplied these identities without reading the
blob contents. `holdout-preregistration.json` freezes the identities, new
deterministic generation seeds, and six 4096-byte recipes whose segment
boundaries are deliberately not all divisible by 512. Content download and
SHA-256 measurement may occur only through the frozen firewall.

The first firewall invocation was stopped before per-stream holdout metrics
because its regenerated policy document incorrectly used the later run HEAD as
`source_commit`, producing a different full document digest even though the
frozen selector and development reproduction matched. This was classified
`A. TEST_HARNESS_ERROR`. The repair pins the already-frozen implementation SHA
in regenerated policy documents and adds an explicit full policy-digest
equality assertion. `frozen-policy.json`, its selector, threshold, budget,
horizon, model and development metrics remain byte-for-byte unchanged. Fresh
source blobs had been verified and block diagnostics had begun, but no holdout
stream metrics or labels were produced; the repaired firewall must reproduce
all frozen development evidence before restarting the scientific run.

The corrected firewall reproduced the complete development record and both
policy digests exactly before restarting. Both fresh sources then matched the
registered identities:

- LLVM: 99,531 bytes, blob
  `d0ff33bd1379ab727bdf712ad2ebee58f64f9149`, SHA-256
  `ff2a485068513bf5ade332860f8b5362b2ed4777dd4edf9b2c6a3cb64b32f1a8`;
- PostgreSQL: 150,652 bytes, blob
  `70cb922e6b7aa45629483bb64d3380d07a1e81a0`, SHA-256
  `d36a4e15730cd6afd2eac6e636ecdeb72755dfdd1d3b864b02c8f6a2dc480eda`.

## Final result

All numbers below are rerun on the same PILOT-015 fresh holdout. Payload bpb
excludes the separately accounted shared model/checkpoint description cost.

| Method | Mean payload bpb | Mean actual neural eval fraction |
|---|---:|---:|
| cheap reset / always cheap | 4.674764 | 0 |
| neural reset | 4.356120 | 0.928019 |
| PILOT-012 max | 4.410522 | 0.724976 |
| PILOT-013 band | 4.544393 | 0.447388 |
| PILOT-014 `unique_count_16 <= 12` | 4.537882 | 0.437378 |
| **PILOT-015 `unique_count_32 <= 20`** | **4.538249** | **0.443034** |
| diagnostic 16-byte 50% oracle (block sum) | 4.479207 | horizon-matched |
| diagnostic 32-byte 50% oracle (block sum) | 4.501546 | horizon-matched |
| zlib-9 | 3.895508 | n/a |
| zstd-19 | 3.781576 | n/a |

PILOT-015 retained 46.222462% of the mean per-stream cheap-to-neural gain,
below the frozen 50% threshold. P14 retained 46.077496% on the same holdout.
Despite that small retained-gain improvement, P15 was 0.000366 bpb worse than
P14 in real whole-stream payload: one stream won, five lost and none tied. The
secondary four-of-six criterion also failed.

| Stream | P14 bpb | P15 bpb | P14−P15 bpb | P15 eval fraction | P15 retained | P15 route accuracy | P15 oracle regret bits | selected-route delay bits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fresh-a | 4.291748 | 4.295410 | -0.003662 | 0.435791 | 42.30% | 50% | 142 | 16 |
| fresh-b | 5.100586 | 5.103027 | -0.002441 | 0.477783 | 79.98% | 75% | 10 | 10 |
| fresh-c | 4.741211 | 4.766846 | -0.025635 | 0.444824 | 29.04% | 50% | 418 | 206 |
| fresh-d | 4.604980 | 4.559814 | +0.045166 | 0.426758 | 43.25% | 50% | 83 | 60 |
| fresh-e | 4.313477 | 4.318359 | -0.004883 | 0.496338 | 45.52% | 50% | 117 | 20 |
| fresh-f | 4.175293 | 4.186035 | -0.010742 | 0.376709 | 37.26% | 50% | 179 | 43 |

Every P15 stream admitted exactly four of eight blocks, so the admitted-byte
fraction was exactly 0.50. Actual uncached PyTorch forward evaluations averaged
0.443034 per source byte and reached at most 0.496338; there were zero budget
violations. P15 performed 10,888 actual forwards across the six streams versus
10,749 for P14. This small content-dependent increase is reported explicitly;
the same hard ceiling and admitted-byte cap were preserved.

## Selection quality, oracle gap and delay

Against each horizon's same-budget hindsight oracle, P15 matched 26/48 routes
(54.17%) versus P14's 24/48 (50%). P15's mean fixed-budget oracle regret fell
to 158.17 bits from P14's 248.17 bits. Its horizon-matched block-sum oracle gap
was 0.038615 bpb, versus P14's 0.060588 bpb. Thus the longer horizon did improve
the route signal on this registered holdout.

That signal improvement did not improve real payload. P15 made 21 true-neural,
three false-neural, three true-cheap and 21 missed-beneficial decisions under
the individual-benefit confusion definition. False admissions lost 101 bits
and missed opportunities represented 2,285 bits. P14 made 21 true-neural,
three false-neural, two true-cheap and 22 misses, losing 85 and 3,119 bits in
those categories. Classification counts alone therefore understate the P15
signal gain.

The decisive cost was later activation. Each 4096-byte stream performs 128
additional cheap observations (16 extra bytes across eight blocks). An admitted
full block exposes 480 rather than 496 bytes to neural coding. The frozen
selected P15 routes cost 355 bits in the forced same-route 32-versus-16 horizon
diagnostic. Better route allocation recovered 346 of those bits, leaving real
payload nine bits worse across all six streams (1.5 bits per stream). This is a
measured counterfactual block diagnostic, not a claim that all delay effects
can be perfectly decomposed in the stateful whole-stream codec.

The 32-byte oracle itself is 0.022339 bpb worse than the 16-byte oracle, further
showing that the later coding point weakens even hindsight-limited potential.
PILOT-015 also remains clearly worse than zlib-9 and zstd-19.

## Correctness, cost and reproducibility

The selector performs 32 bounded histogram updates, stores at most 32 observed
byte keys, extracts one count, makes one integer split comparison and one
budget comparison. This is bounded O(32) integer/container work versus up to
511 actual neural forwards for a full admitted block. It adds zero bytes, calls
no neural model during feature extraction and uses the same
`rich_cheap_admission_decision` helper in search, encode and decode.

There were zero search/codec route mismatches, future-byte reads, neural
evaluations before admission, side bits, budget violations, roundtrip failures
and SHA-256 mismatches. The first specialist output triggers 31 honestly
counted catch-up evaluations for P15 versus 15 for P14; no catch-up work is
hidden. The neural model, checkpoint, cheap predictor, range coder, block size
and selector complexity were unchanged. No `src/` production file, PollicinoNet
file or course file changed. PILOT-013 and PILOT-014 remain valid unchanged.

The scientific execution used commit
`1fbb02192324d59f2ca278411ae78828b37b1b5e`, Python 3.14.2, PyTorch 2.14.0,
NumPy 2.5.3, zstandard 0.25.0, deterministic CPU execution and one Torch
thread. The model fingerprint is
`354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`;
checkpoint SHA-256 is
`713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7`.
The frozen policy digest is `ee0aa7a13a0b24f7b3c978ee40e25a05376e734206e3cdf9df1d30c3ac39b28e`,
the holdout preregistration digest is
`2e5238431c71de82d9cdc276d58ee987f2ef9b5862af6aaa0b8ccf3ee06b0dbb`,
the holdout manifest digest is
`f27acf12c2ecb439059afe66628306a31060cb8eb28a74553885b648cebb36db`,
and the final result bundle digest is
`b1d7256bf491fe0d77f0acafb61ebbd5e396bdebbcc08aac9a759c313ff43877`.
No CI workflow was used; the artifact ID is
`local-1fbb02192324-ee0aa7a13a0b`.

Repository-appropriate validation passed 104 tests before the run and again
at closure; `python -m compileall src tests experiments/pilot-015` passed.
Reproduce with:

```bash
GITHUB_TOKEN="$(gh auth token)" \
  /Users/antoniocaristia/dev/pollicino-pilot014/.venv/bin/python \
  experiments/pilot-015/run_frozen.py
```

Two failures occurred and both were classified `A. TEST_HARNESS_ERROR`: the
synthetic focused-test fixture errors repaired before development, and the
dynamic source-commit policy-digest error stopped after source verification
but before holdout metrics. Neither changed the scientific policy. The latter
forced a complete frozen-development reproduction before the successful run.
No B–L failure was observed during the successful scientific execution; the
negative outcome itself is the preregistered admission-delay finding.

## Interpretation, limitations and next question

On this small deterministic mixed-domain mechanism holdout, 32 bytes carried a
somewhat better cheap-only admission signal, but observing them delayed neural
coding enough to erase that value. This is not evidence about all source code,
universal compression, or general superiority to classical codecs. The
horizon-matched oracles use independently coded block payloads and are
diagnostic; model description length remains separate from payload.

Confidence is high in the deterministic mechanism result and low in any broad
generalization beyond the registered streams. Increasing the threshold grid,
adding features, enlarging the model or raising the neural budget would not
answer this experiment and was not done.

The smallest justified PILOT-016 question is whether the same one-split
selector can gain a 32-byte causal evidence window without delaying activation:
at byte 16, compute one `unique_count` over the 16 immediately preceding bytes
plus the first 16 current-block bytes, while keeping the model, block, selector
complexity and 50% budget fixed. This tests cross-block cheap evidence rather
than rescuing PILOT-015 with a longer current-block probe.

`COURSE_UPDATE_RECOMMENDED: YES`, after closure: add the distinction between
better route classification and better coded payload, including admission
latency and honestly counted state catch-up. No course file was modified.
