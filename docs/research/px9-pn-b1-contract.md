# PX9-PN-B1 complete-record bearer contract

PX9 selects a minimal complete-record model. `CompleteRecordBearer.attempt()`
receives one bounded `CompleteRecordUnit` and returns one bounded
`BearerAttemptResult`. The unit contains one existing D2 reference, D3 query,
or D3 result object plus its PX8 logical-byte accounting. It is a local Python
value, not a frame, serialization, public wire format, or MTU claim.

The bearer may deliver the exact unit zero, one, or twice. Zero represents loss
or disconnect, one represents delivery, and two represents deterministic
duplicate presentation. A delayed delivery is held temporarily and released
inside the same attempt. Sender uncertainty is represented independently from
receiver state: the exact record can commit while the sender observes no
confirmation.

The receiver applies the exact presented value through the existing native
D2/D3 store methods. Those methods remain authoritative for validation,
idempotence, conflict rejection, quotas, persistence, and complete-record
atomicity. B1 does not reimplement record encoding or mutation rules.

## Bounds

- D4 `ContactBudget`: at most 100 attempted records and 2,606,200 logical
  bytes per invocation.
- B1 `BearerBudget`: 1–100 attempts and 1–100 diagnostic trace entries.
- scripted impairment plan: at most 100 actions per direction;
- presentation multiplicity: at most two complete units per attempt;
- temporary delay queue: at most one complete unit;
- no retry loop, background worker, retained backlog, or persistent bearer
  state.

A dropped unit consumes both one D4 logical item and its logical bytes. It also
consumes one bearer attempt and one trace entry. These are experimental model
counts, not bandwidth, airtime, latency, or stable wire-byte measurements.

## Authority boundaries

Bearer delivery is not durable commit. Durable commit is not application
acceptance. A result does not trigger reference transfer, and reference
transfer does not trigger fetch, trust, execution, or import. D2 selections are
still supplied explicitly for each contact.

## Progress and completion

There is no persistent B1 session. A later invocation rebuilds the PX8 work
plan from current durable state. Outcomes distinguish no eligible work,
partial non-delivery, D4 budget exhaustion, B1 budget exhaustion, disconnect,
sender uncertainty, and error. No outcome promises future or global delivery.

The current implementation locally reuses PX8's deterministic internal work
planner. Consequently B1 validates delivery of planned complete records, not
transport of reconciliation metadata. Exposing reconciliation across an
independent serialized duplex boundary remains a later experiment.
