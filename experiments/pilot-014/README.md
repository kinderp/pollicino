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

Development selection and fresh-holdout results are not yet recorded in this
preregistration snapshot.
