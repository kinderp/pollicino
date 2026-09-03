# PX5 PN-D2R scientific report

## Hypothesis

A bounded dual-generation full snapshot can make the PX3 catalog restart-safe
and corruption-detecting while preserving native semantics and FARO PX4
authority boundaries, without a journal/database, network or PR #52.

## Method and results

The control is exact PX3 final `6dbc79e...`; FARO conformance is exact PX4
final `44af3e4...`. Implementation commit `cdae923e6084eabe24ce593c7e591bbff68504a5`
adds one generic persistence module and
leaves `catalog.py` unchanged. Fifty-five core persistence cases and twelve
FARO-specific conformance cases pass, including a real subprocess boundary,
six fault points, corrupt/truncated/overbound states, two-generation recovery,
ambiguity, independent A/B/C restart and native post-restart reconciliation.

The design writes one bounded canonical full snapshot per successful semantic
mutation. Tests at 10/100/1000/10000 items establish correctness only.
Benchmark: `NOT_RUN_BY_DESIGN`; accounting:
`LOCAL_PERSISTENCE_MODEL_ONLY`; network: `NOT_USED_BY_DESIGN`.

## Interpretation

Strategy A is insufficient only because recovery of an immediately previous
valid generation was preregistered as required. Strategy B meets it with two
files and one local integer. Strategy C adds no correctness required by this
Gate. Native duplicate, conflict, quota, canonical and reconciliation behavior
is retained. Persistence paths, generation/write/restart history and recovery
status never enter native catalog identity or application authority.

The validated limits are single POSIX authoritative writer, no concurrent
readers/writers, full-snapshot write amplification, and no cross-filesystem or
physical power-loss claim. These are material but fail-safe local limits.

## Classification

`POLLICINO_PERSISTENT_BOUNDED_REFERENCE_CATALOG_READY_WITH_LIMITS`, confidence
`HIGH`. This is a validated local persistent generic primitive, not yet a
stable public persistence API. The exact next Gate is `PX6-PN-D3 — Generic
Asynchronous Query/Result Local Persistent Multi-Node Validation`.
