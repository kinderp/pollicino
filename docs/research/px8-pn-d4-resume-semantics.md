# PX8-PN-D4 resume semantics

`resume` means a new contact over the same reopened durable node roots. It never
means reviving an old in-memory object.

The resume authority is the current canonical D2 and D3 state. Query/result
identifiers and explicitly selected D2 keys are reconciled anew. A successfully
committed record is already known and consumes zero transfer items and zero
accounted transfer bytes. A record interrupted before apply remains missing.

The 105-record proof is:

1. A stores queries 0..104.
2. Contact 1 transfers sorted queries 0..99 and ends normally with
   `BUDGET_EXHAUSTED`.
3. A and B close; both persistent objects are destroyed and reopened.
4. Contact 2 observes 0..99 as already known and transfers only 100..104.
5. Canonical D3 states are byte-identical.

The ContactReport from step 2 is explicitly deleted before one restart/resume
test. Resume still succeeds. No durable session ID, peer cursor,
acknowledgement database, contact store, or custody log exists.

Identifier scanning is linear and locally bounded by the finite store; every
native reconciliation page is at most 100 identifiers. This is acceptable for
D4 semantics but is not an advanced reconciliation or performance claim.
