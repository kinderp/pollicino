# PX8-PN-D4 contact-model preregistration

Preregistered before D4 implementation on the exact PX6 base.

## Models evaluated

**Model A — ephemeral contact over persistent state.** Each invocation is a
finite local opportunity. Fresh reconciliation derives missing work from the
receiver's current D2/D3 durable state. No contact report, cursor, peer journal,
acknowledgement, or session identifier is durable.

**Model B — persistent contact cursor/journal.** This could avoid rescanning
known identifiers, but would make a peer/session namespace and crash recovery
rules new correctness authorities. PX6 already makes every successful record
mutation durable and idempotent, so no registered correctness requirement yet
needs this model.

**Model C — custody/outbox log.** This would add delivery acknowledgements,
ownership transfer, deletion authority, and routing-adjacent policy. Those are
explicitly outside D4.

## Preregistered decision rule

Select Model A only if tests prove all of the following: interruption before
apply leaves no mutation; interruption after apply survives restart; a fresh
contact does not transfer that record again as missing; deleting the prior
report changes nothing; mule restarts preserve forwarding; conflicts and quota
failures remain fail-closed.

If any invariant requires remembered per-contact progress, stop and classify
`PERSISTENT_CONTACT_PROGRESS_REQUIRED`; do not silently add Model B or C.

Provisional selection: `EPHEMERAL_SESSION_DURABLE_STATE_RECONCILIATION`.

