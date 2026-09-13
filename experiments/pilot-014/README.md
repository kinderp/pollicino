# PILOT-014 — Rich Cheap-Only Neural Admission

## Preregistration

PILOT-013 proved that a causal cheap-only gate can avoid all neural work before a
16-byte decision and enforce a per-stream 50% admitted-byte ceiling, but its
one-dimensional 88–128 bit cheap-codelength band retained only 36.86% of the
mean cheap-reset to neural-reset gain. PILOT-014 asks whether a small richer
integer selector allocates the same neural budget to better 512-byte blocks.

The primary hypothesis, registered before feature/scorer search, is that the
frozen selector will retain at least 50% of the mean cheap-reset to neural-reset
payload gain on a fresh six-stream mixed-domain holdout while every stream stays
at or below 0.50 actual uncached PyTorch forward evaluations per source byte.
It must also beat PILOT-013 in mean payload bpb; beating it on at least four of
six streams is the stronger target. The secondary hypothesis is that selection
can improve with bounded integer work, zero side bits, and no floating-point
runtime route decision.

The inherited checkpoint, cheap and neural gates, range coder, 512-byte block,
16-byte probe, and 2048/4096 admitted-byte cap are frozen. No neural output,
future byte, oracle label, transmitted route bit, or nondeterministic input may
enter the deployed decision. `rich_cheap_admission_decision` is the one deployed
helper used by search simulation and both codec directions.

Exact version-1 features are computed over the first 16 already-consumed bytes:

- `probe_code_bits_ceil`: ceiling of exact total cheap likelihood codelength;
- `unique_count`: number of distinct probe bytes;
- `max_hist_count`: largest byte-histogram bucket;
- `transition_count`: count of adjacent unequal byte pairs;
- `distinct_transition_count`: number of distinct adjacent ordered byte pairs;
- `longest_run`: maximum equal-byte run length;
- `surprise_sum_ceil`: sum of per-byte ceiling integer surprises;
- `surprise_max_ceil`: maximum per-byte ceiling surprise;
- `surprise_range_ceil`: maximum minus minimum per-byte ceiling surprise;
- `surprise_variance_proxy`: `N*sum(s_i^2) - sum(s_i)^2`;
- `surprise_early_minus_late`: first-half surprise sum minus second-half sum;
- `very_surprising_count`: count of per-byte ceiling surprises at least 9 bits.

Candidate A is a deterministic regression decision tree of depth 2 or 3.
Candidate B is ridge regression exported as an integer linear score with scale
256. Both are tested on a preregistered compact six-feature set and the full
twelve-feature set. Tree minimum-leaf sizes are 4 and 8; linear ridge values are
1 and 10. PILOT-013's band is the baseline. Candidate fitting uses only the
already-consumed PILOT-012 and PILOT-013 source sets: eight mixed streams form
the fit split and four form the validation split. Thresholds are chosen on the
fit split; final family/configuration selection uses actual whole-stream codec
payload on validation. Within 0.01 bpb of the best validation result, the rule
with fewer deployed features and then fewer nodes/coefficients wins. No fresh
holdout source is opened during this procedure.

After selection, deterministic development-only ablations remove codelength,
histogram, repetition, transition, and surprise groups where present. Ablations
are diagnostic and cannot change the frozen rule after fresh-holdout access.

The success contract is: zero roundtrip or SHA-256 failures; zero selector side
bits; zero search/deployed route divergences; zero neural evaluations before
admission; no policy retuning after holdout access; per-stream actual neural
evaluation fraction at most 0.50; mean retained gain at least 0.50; mean payload
below PILOT-013; and cheap bounded feature work relative to a neural forward.

## Status

Closed. The primary hypothesis **failed**. Classification:
`PILOT014_CHEAP_FEATURES_INSUFFICIENT`.

## Development selection and frozen policy

Development used 96 blocks from the already-consumed PILOT-012 and PILOT-013
mixed streams. Eight streams were the fit split and four were the validation
split. All 12 preregistered tree/linear configurations were evaluated through
the actual range codec. Search and deployed codec routes differed zero times.

The best raw validation payload was 4.395996 bpb from a six-coefficient integer
linear scorer. Under the preregistered 0.01 bpb complexity tolerance, the
selected tree achieved 4.404297 bpb, compared with PILOT-013 at 4.436584 bpb,
and used 0.440979 actual neural evaluations per byte. Threshold-equivalent tree
branches were pruned before freeze. The deployed rule is exactly:

```text
unique_count = number of distinct byte values in the first 16 consumed bytes

if unique_count <= 12 and admitted_bytes + block_bytes <= 2048:
    NEURAL
else:
    CHEAP
```

It is a one-split, three-node integer tree with threshold 1 and leaf values 1
(admit) and 0 (reject). Although the candidate search used rich features, the
complexity rule reduced the deployed signal to one histogram feature. Runtime
feature cost is 16 bounded histogram updates plus two integer comparisons (tree
split and admission threshold), with at most
16 histogram entries; it performs no surprise calculation, bigint codelength
product, transition tracking, floating-point operation, or neural call. It
transmits zero bytes and adds no route side stream.

The frozen policy is `frozen-policy.json`, digest
`02cb5a4fd9fb2d3695af55a874aff6ad2a4b49599af9d396878ef7cde116aa85`.
Its implementation source commit is
`f41a984f299b41de23a99d766268a91259f59906`; its development reproduction
digest is `9ca016c09a8a912c05b35f9766f9e9e18990f6b7fdec19e653760152229deab3`.

The final deployed-feature ablation on development block sums was:

| Rule | Validation bpb | Neural eval fraction |
|---|---:|---:|
| `unique_count <= 12` | 4.406189 | 0.440979 |
| minus histogram / always cheap | 4.599365 | 0 |

Thus the selected signal was useful on development, but that improvement did
not transfer reliably to the fresh holdout.

## Fresh holdout provenance

Source choice and six non-block-aligned stream recipes were committed before
content access in `holdout-preregistration.json`, digest
`3acab5dd2509a09e2642ac0e7f6d7180c903f5e2150771c7f115d3f544d80a4d`.

The immutable sources passed size, Git-blob and SHA-256 verification before
stream construction:

- Rust 1.80.0 `library/std/src/io/mod.rs`: 107137 bytes, blob
  `97b72f9664bb9c4e008d55bffb5203b68f34c478`, SHA-256
  `f453efe14ba96607176652dd12edfbe89aadfe7ec613099ad31f3b6aefa4d350`;
- SQLite 3.46.0 `src/json.c`: 167009 bytes, blob
  `4db468c92d3afc2491b90e4db67833a4a318be00`, SHA-256
  `3b863585dfc49a9631b8f189e05e92a2a83be2fa653bb86e7284bf998bdfe86c`.

The six 4096-byte streams combine those sources with deterministic JSON, DNA,
English-like text, repetition, random-64/random-256 controls and compressed
bytes. Transitions are deliberately not aligned to every 512-byte boundary.
No holdout label was used for fitting, pruning, thresholding or policy choice.

## Final result

| Method | Mean payload bpb | Mean actual neural eval fraction |
|---|---:|---:|
| cheap reset / always cheap | 4.931885 | 0 |
| neural reset | 4.523193 | 0.944417 |
| PILOT-012 max | 4.540405 | 0.827230 |
| PILOT-013 band | 4.747111 | 0.453369 |
| **PILOT-014 unique-count tree** | **4.747599** | **0.424601** |
| diagnostic 50% oracle (block sum) | 4.666423 | <=0.50 budget |
| zlib-9 | 4.243815 | n/a |
| zstd-19 | 4.102865 | n/a |

PILOT-014 was 0.000488 bpb worse than PILOT-013 on average: one stream won,
two lost and three tied. It retained 45.85% of mean per-stream cheap-to-neural
gain, below the frozen 50% threshold; PILOT-013 retained 46.39% on the same
fresh streams. The stronger four-of-six win target also failed.

| Stream | P13 bpb | P14 bpb | P14 eval fraction | P14 retained | Oracle bpb | Regret bits |
|---|---:|---:|---:|---:|---:|---:|
| fresh-a | 4.520020 | 4.537598 | 0.425293 | 35.58% | 4.444580 | 390 |
| fresh-b | 5.534180 | 5.534180 | 0.487793 | 58.51% | 5.451660 | 345 |
| fresh-c | 4.687256 | 4.687256 | 0.444824 | 39.69% | 4.582520 | 438 |
| fresh-d | 4.649658 | 4.649658 | 0.428955 | 57.91% | 4.627686 | 96 |
| fresh-e | 4.806885 | 4.758789 | 0.499023 | 55.70% | 4.708252 | 215 |
| fresh-f | 4.284668 | 4.318115 | 0.261719 | 27.72% | 4.183838 | 559 |

Every stream stayed within the budget; mean admitted-byte fraction was 0.47917
and maximum actual neural-evaluation fraction was 0.49902. Across 48 blocks the
selector admitted 23 and rejected 25. Against the fixed-budget diagnostic
oracle it made 27/48 matching route decisions (56.25%), had one false neural
admission costing 43 bits, and missed 20 individually beneficial neural blocks
worth 4127 bits in aggregate. Fixed-budget oracle regret averaged 340.5 bits per
stream, or 0.083130 bpb on comparable independently coded block sums. This gap
is large enough that selection remains the limiting mechanism.

PILOT-014 still lost clearly to zlib and zstd-19. The shared neural checkpoint
is not free: the table reports payload only; checkpoint/model description cost
must remain separate in any total-description-length claim.

## Correctness and reproducibility

The authoritative helper `rich_cheap_admission_decision` is called by search
simulation and the actual encode/decode provider. There were zero search-codec
divergences, zero neural evaluations before admission, zero side bits, zero
budget violations, zero route nondeterminism findings, zero roundtrip failures
and zero SHA-256 mismatches. The range coder, cheap expert, neural checkpoint,
block size and probe length were unchanged. PILOT-013 remains valid and its
directory is byte-for-byte unchanged.

The first literal root `pytest` invocation incorrectly collected standalone
course lesson suites; the repository-appropriate `pytest tests` run passed 99
tests. Missing local test/NumPy dependencies and a Python 3.14 dynamic-import
edge were repaired before freeze. After the first frozen measurement, one
reporting-only rerun added omitted PILOT-013 retained-gain and explicit
oracle/admission aggregates. It reproduced the full development firewall and
all scientific numbers; the frozen policy never changed.

The successful result run used Python 3.14.2, PyTorch 2.14.0, NumPy 2.5.3,
zstandard 0.25.0, deterministic CPU execution and one Torch thread. The exact
checkpoint model fingerprint is
`354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`;
checkpoint SHA-256 is
`713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7`.
Run with:

```bash
GITHUB_TOKEN="$(gh auth token)" \
  .venv/bin/python experiments/pilot-014/run_frozen.py
```

The local artifact identity and final bundle/manifest digests are recorded in
`run-metadata.json`. Development candidates, blocks, ablation, holdout blocks,
per-stream metrics and provenance are all persisted beside this README.

## Interpretation and next question

The negative result is specific to this registered mixed-domain mechanism
holdout. It does not show that cheap features are universally useless. It shows
that, at the inherited 16-byte horizon, the small candidate family collapsed to
a unique-byte-count rule that did not improve allocation over PILOT-013 on
fresh data and remained far from the fixed-budget oracle. Increasing neural
budget, retraining the model, changing block size or hiding selector bits would
not answer the failed question.

The smallest justified PILOT-015 question is a separate preregistered comparison
of the current 16-byte horizon with exactly one longer cheap-only horizon (for
example 32 bytes), keeping model, 512-byte blocks, codec and per-stream 50%
neural budget frozen and accounting explicitly for the extra cheap latency.
Do not implement that comparison inside PILOT-014.

`COURSE_UPDATE_RECOMMENDED: YES`, after this experiment is closed: the useful
lesson is scientific firewall discipline and the fact that development gains
from a cheap selector can vanish on a fresh same-budget holdout. No course file
was modified here.
