# PILOT-010 — Stability-Aware Value Routing

PILOT-010 tests whether the false-positive neural activation left by PILOT-009 can be reduced without returning to a long fixed probe.

## Scientific question

Can a deterministic router require **stable**, **recent** and **economically meaningful in bits** evidence before activating the shared neural specialist, while preserving early rejection, zero selector side bits and bit-perfect decoding?

## Router

`StabilityValueSpecialistRouterCDFProvider` extends the sequential idea with four simultaneous conditions for neural activation:

1. cumulative neural/cheap likelihood exceeds the frozen PILOT-009 threshold;
2. a recent window has a minimum neural advantage;
3. that condition persists for several consecutive decoded bytes;
4. a conservative lower bound on the future recoverable bit advantage exceeds a policy margin.

The value floor is deliberately integer-only:

```text
projected_gain_bits = floor(remaining_bytes / recent_window) * recent_gain_bits
```

It is not a prediction of actual future entropy. It is a deterministic admission rule: if even the policy's recent-gain floor cannot justify the required margin over the remaining stream, neural activation is forbidden.

No wall-clock time, CPU model, floating-point log, random choice or selector side-stream participates in the route decision.

## Frozen invariants from PILOT-009

- minimum observations: `8`;
- cumulative activation threshold: `256:1`;
- cumulative rejection threshold: `1:256`;
- meaningful neural gain label: `>= 0.05 bpb`;
- neural checkpoint: exact `winner.pt` from PILOT-003, retrieved and verified by artifact digest and canonical tensor fingerprint.

PILOT-010 does **not** simply raise the 256:1 threshold.

## Development-only grid

Only already-consumed files are used to choose the new stability/value parameters:

- the six Silesia files from PILOT-007;
- the three Large Corpus files from PILOT-008;
- the five Pizza&Chili pseudo-real files from PILOT-009.

Total: 14 development files.

Grid:

- `max_probe_bytes`: 64, 96, 128;
- `recent_window`: 4, 8, 16, 32;
- `persistence_observations`: 2, 4, 8;
- `recent_gain_bits`: 1, 2, 3, 4;
- `min_projected_gain_bits`: 0, 32, 64, 128, 256.

Candidate ranking is frozen before the new holdout:

1. maximize correct meaningful route classifications;
2. minimize false-positive neural activations;
3. minimize false negatives;
4. minimize mean regret relative to the better of cheap/neural;
5. minimize decision latency.

## New holdout

The holdout is the six Silesia files that have **not** appeared in earlier POLLICINO pilots:

- `mozilla` — mixed application/executable tar;
- `mr` — MRI/DICOM image;
- `nci` — chemical structure database;
- `samba` — tarred source project;
- `sao` — binary astronomical database;
- `webster` — English dictionary in HTML.

The official Silesia raw sizes and MD5 values are checked after download. SHA-256 values are recorded by the run.

Only the first 4096 bytes are entropy-coded in this pilot; full-file identity remains in the manifest.

## Comparisons

Every holdout slice is coded and decoded with:

- cheap gate;
- always-neural gate;
- PILOT-009 sequential router;
- PILOT-010 stability/value router;
- zlib;
- zstd level 19.

Primary routing metrics:

- payload bpb;
- route accuracy under the predeclared 0.05 bpb useful-neural rule;
- regret versus `min(cheap, neural)`;
- decision byte;
- specialist calls;
- encode/decode timing as a reported metric only, never as routing input.

## Success criterion

PILOT-010 is useful if stability/value gating reduces false neural activation or oracle regret relative to PILOT-009 without materially damaging the in-domain neural control. A negative result will be retained unchanged and will argue against adding more router complexity.
