# POLLICINO Experiment Protocol

Every reported experiment must record enough information for another machine to reproduce or audit the result.

## Identity

- experiment ID
- UTC timestamp
- git commit
- experiment configuration hash
- random seed(s)

## Data

- dataset name/version
- manifest
- content hash
- split policy
- train/validation/test byte counts
- explicit leakage checks when applicable

## Model

- model specification
- parameter count
- checkpoint hash and byte size
- context length
- numeric precision
- initialization policy

## Training

- backend and version
- hardware
- optimizer
- learning-rate schedule
- batch size
- gradient accumulation
- training bytes/tokens seen
- wall time
- peak memory when measurable

## Predictive metrics

- train cross-entropy
- validation cross-entropy
- theoretical bits/byte
- calibration or distribution diagnostics when useful

## Coding metrics

- realized coded bits/byte
- payload byte size
- container/header overhead
- model/checkpoint bytes
- amortized total description length
- encode throughput
- decode throughput
- peak encode/decode memory

## Baselines

Record compressor name, exact version and settings for every classical baseline.

## Correctness

A result is **not** a valid lossless-compression result unless decoding succeeds independently and the reconstruction is byte-for-byte identical.

Record at least:

```text
input bytes
output bytes
SHA256(original)
SHA256(decoded)
round_trip_ok
```

A cryptographic hash is used only as a final integrity check. It must never smuggle information required for reconstruction unless those hash bits are explicitly counted as payload.

## Negative controls

Every serious benchmark suite must include data that should resist compression, especially uniformly random bytes. Unexpected gains on these controls are grounds to suspect leakage, incorrect accounting or a broken experimental setup.
