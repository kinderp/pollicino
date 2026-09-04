# PX9-PN-B1 adversarial matrix

| Experiment | Expected invariant | Result | Failure class |
|---|---|---|---|
| lossless control | same canonical state as PX8 | pass | none |
| query drop | receiver unchanged; later eligible | pass | none |
| two commits then loss | commits survive; only missing attempted later | pass | none |
| duplicate query/result/reference | one semantic record | pass | none |
| known query/result/reference conflict | fail closed, no attempt/overwrite | pass | none |
| substituted conflicting presentation | reject before any receiver mutation | pass | B, deliberately induced bad adapter |
| malformed adapter result | bounded error, no mutation | pass | B, deliberately induced bad adapter |
| disconnect after commit | bounded partial progress | pass | none |
| directional loss | opposite direction may succeed safely | pass | none |
| sender uncertainty after commit | fresh reconciliation performs no attempt | pass | none |
| repeated/permanent loss | no false convergence or internal retry | pass | none |
| D4 budget plus loss | attempts remain item/byte bounded | pass | none |
| B1 attempt/trace budget | returns explicit exhaustion | pass | none |
| receiver quota after prior commit | exact bounded error; prior commit remains | pass | none |
| process/reopen | committed skipped; uncommitted remains missing | pass | none |
| 105 queries + 105 results | three bounded contacts restore all 210 | pass | none |
| lossy A–C–B / B–C–A mule | restart-safe propagation | pass | none |
| selected D2 mule | explicit at both hops; no automatic pull | pass | none |

One early test asserted that two durable queries would produce exactly two
“known” considerations. PX8's frozen entry snapshot considers each in both
directions, producing four, while still causing zero bearer attempts. This was
classified `A. TEST_HARNESS_OR_IMPAIRMENT_MODEL_ERROR`; the assertion was
corrected, not the architecture.

The first quota experiment also exposed a PX9-only reporting defect: error
report construction attempted a fresh reconciliation while the receiver was
already at its monkeypatched quota, masking the intended bounded error. This
was classified `B. BAD_BEARER_ADAPTER_DESIGN`. B1 now derives a monotonic
remaining-work counter from the frozen contact-entry plan; report construction
does not inspect or mutate stores. The native quota failure is returned and the
prior complete commit remains durable. No PX8 code changed.

The unsuitable reuse of `transmit_exact()` is classified
`C. EXISTING_B1_CANDIDATE_REUSE_MISMATCH`: it would import fragmentation,
stop-and-wait retry, ACK-loss, bitrate, and exact-content reconstruction that
B1 does not require. No unexpected D2/D3/D4 correctness bug, missing generic
B1 capability, or durable-reconciliation falsification was observed.

Transport of reconciliation metadata, serialization, corruption detection,
fragmentation, and concrete backend adaptation are
`G. OUT_OF_SCOPE_FUTURE_GATE_REQUIREMENT`, not silently implemented limits.
