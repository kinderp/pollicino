# PX9-PN-B1 scientific report

## Question and method

PX9 attempted to falsify whether PX8's ephemeral-contact, durable-state
reconciliation survives the first unreliable bearer boundary. The experiment
inserted a minimal complete-record adapter and a scripted in-memory link
between the PX8 work plan and native receiver stores. It exercised loss,
duplication, disconnect, bounded delay, direction-specific failure, sender
uncertainty, restart, permanent loss, quota/budget behavior, conflict, and a
three-node data mule.

The baseline was exact `checkpoint/px8-pn-d4` at
`e5cd094677e36e9f4b7a58c2aa81c897e7f43dc9`. Its declared suite passed 289
tests with 5 skips, the focused D2/D3/D4/PX8 suite passed 164 with 3 skips, and
compileall passed before implementation.

## Result

Loss before apply caused no durable mutation. Commit followed by sender
uncertainty survived close/reopen and the next contact made zero bearer
attempts for that record. Identical duplicates remained idempotent; known and
presented conflicts failed closed. Repeated and permanent loss returned
bounded partial outcomes rather than false convergence. Three contacts moved
105 queries and 105 results in bounded batches of 100, 100, and 10, with
restart between contacts and exact final canonical state.

In the mule experiment, A–C initially lost a query, a later contact committed
it, C restarted, and C–B forwarded it. B created a result outside B1, the first
B–C leg disconnected, a later leg committed it, C restarted, and C–A
forwarded it. The result did not transfer its D2 key automatically. The caller
selected the reference explicitly on B–C and again on C–A. No application
authority event occurred.

No persistent ACK, contact cursor, peer journal, custody log, outbox, route,
TTL, authentication, retry, fragment, socket, or application-specific branch
was introduced. `contact.py` and historical gate evidence remain unchanged.

Final validation passed 29 focused PX9 tests, 193 focused D2/D3/D4/PX8/PX9
tests with 3 skips, and the full declared `tests/` suite with 318 passes and 5
skips. Compileall passed and all 11 PX9 JSON artifacts parsed.

## Interpretation

The hypothesis survived the registered local complete-record loss model.
Sender knowledge may be uncertain while receiver state remains exact; durable
reconciliation resolves that uncertainty on a new contact. This is not an
exactly-once or eventual-delivery claim. It is an at-least-zero presentation
experiment whose native stores make repeated complete presentations
idempotent and conflicting identities fail closed.

The result remains local and model-level. The work plan still observes both
stores directly, complete units are Python objects, delay is not wall-clock
reordering, and no corruption or partial-frame state exists. Thus PX9 does not
prove a stable protocol, independent-process reconciliation exchange,
fragmentation, real bearer behavior, performance, security, routing, or
delivery guarantees.
