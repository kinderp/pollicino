# PILOT-011 — Regret-Aware Bit-Credit Routing

PILOT-010 showed that route-classification accuracy is not the right compression objective: avoiding a nearly free false-positive neural route can cost far more than accepting it if the conservative policy creates a high-regret false negative.

## Scientific question

Can POLLICINO tune an asymmetric, deterministic bit-credit router directly for **compression regret under an explicit neural-compute budget**, instead of classifying every file as cheap/neural with equal error cost?

## Bit-credit router

For the probe prefix, define

```text
R = P_neural(prefix) / P_cheap(prefix)
credit_bits = log2(R)
```

The implementation never computes the logarithm. `credit_bits > A` is tested exactly as `R > 2^A` using integer CDF likelihood products. Likewise rejection uses `R < 2^-B`.

Activation and rejection thresholds are independent. This is the key change from the symmetric PILOT-009 policy.

The route remains causal, deterministic, zero-selector-bit and one-way: bytes are coded by cheap while probing; after activation the neural gate is used for the remainder; after rejection the specialist is never evaluated again.

## Development data

Only already-consumed POLLICINO benchmark files are used for tuning:

- 6 Silesia files from PILOT-007;
- 3 Large Corpus files from PILOT-008;
- 5 Pizza&Chili pseudo-real files from PILOT-009;
- 6 remaining Silesia files from PILOT-010.

Total: **20 development streams**. Their previously recorded cheap/neural payload bpb values define oracle regret; the original bytes are retrieved again only to reconstruct the first 256 bytes of exact quantized likelihood evidence.

## Candidate grid

- `min_observations`: 4, 8, 16;
- `max_probe_bytes`: 16, 32, 64, 128, 256;
- `activation_credit_bits`: 0, 2, 4, 6, 8, 10, 12;
- `rejection_credit_bits`: 2, 4, 6, 8, 10, 12, 16.

For a candidate policy and development stream:

```text
oracle_bpb = min(cheap_bpb, neural_bpb)
regret_bpb = selected_bpb - oracle_bpb
```

The deterministic compute proxy is the fraction of bytes for which the neural gate is evaluated:

- neural route: `1.0`;
- cheap route: `decision_byte / stream_bytes`.

No wall-clock timing enters policy selection.

## Three predeclared modes

No arbitrary weighted sum of bpb and seconds is used.

- **max**: minimum development mean regret, with lower max-regret and compute as tie-breakers;
- **balanced**: minimum mean regret among policies with mean specialist-call fraction `<= 0.50`;
- **fast**: minimum mean regret among policies with mean specialist-call fraction `<= 0.20`.

The three policies are frozen before opening the new holdout.

## New holdout

A fixed six-collection subset of the official Pizza&Chili **real repetitive corpus** is used and is not part of any earlier POLLICINO pilot:

- `cere` — yeast DNA;
- `para` — yeast DNA;
- `influenza` — DNA sequence collection;
- `coreutils` — source-code versions;
- `kernel` — Linux kernel source versions;
- `world_leaders` — document collection converted to text.

Archives are downloaded from the official real-corpus directory. The run records archive and full extracted SHA-256 plus exact sizes. Only the first 4096 bytes are entropy-coded in this pilot.

## Comparisons

Every holdout slice is round-tripped with:

- cheap gate;
- always-neural gate;
- frozen PILOT-009 sequential router;
- PILOT-011 `max`;
- PILOT-011 `balanced`;
- PILOT-011 `fast`;
- zlib;
- zstd level 19.

Primary metrics are mean and maximum oracle regret, payload bpb, specialist-call fraction, decision byte, and measured encode/decode time (reported only).

## Success criterion

PILOT-011 succeeds scientifically if direct regret optimization produces a useful Pareto frontier and at least one budgeted mode preserves substantially more of PILOT-009's compression quality than PILOT-010 while reducing specialist compute. A negative result is retained unchanged.

Block-local re-routing is deliberately left for the next step: PILOT-011 isolates whether **the objective function itself** was the problem before adding another architectural dimension.
