# PX10-PN-B2 independent endpoint contract

`PX10-PN-B2` is the candidate identifier supplied by the repository owner.
The exact PX9 decision described this experiment but assigned no gate number;
no authoritative replacement name was found in the baseline repository.

An `IndependentEndpoint` owns references to exactly one local D2 catalog and
one local D3 query/result store. Its public reconciliation surface emits
encoded advertisements or a caller-selected D2 selection, and accepts one
encoded message. A receive operation may emit only bounded encoded response
messages plus local diagnostic counters.

`run_independent_contact()` receives two endpoint interfaces and an encoded
message bearer. It never receives or accesses either endpoint's catalog,
query/result store, state digest, or native reconciliation methods. It moves
response bytes across the bearer before the other endpoint can interpret them.
The central test driver aggregates diagnostics but supplies no peer state to an
endpoint.

## Authority

Advertisement digests and requests influence transfer planning only. They do
not establish local possession or validity. A `RECORD` body is structurally
decoded and then applied by the existing native D2/D3 store method. Native
identity, conflict, quota, and persistence rules remain authoritative.

There is no durable B2 state. In particular there is no ACK database, session
cursor, peer journal, custody log, outbox, or receipt. Sender uncertainty stops
the contact after receiver presentation. A new endpoint instance advertises
from durable state again; a receiver that committed the record emits no new
request.

## Contact flow

1. Each endpoint advertises bounded pages of its local query identifiers and
   result identities with per-record digests.
2. The receiving endpoint compares only against its own local state and emits
   a request for missing identities. A known identity with another digest fails
   closed using the native conflict category.
3. The source encodes requested complete records. The receiver decodes and
   applies each complete record atomically through its native store.
4. D2 references are never generally advertised. A caller-selected endpoint
   first sends `REFERENCE_SELECTION`; the source answers with a bounded
   reference advertisement; only missing selected references are requested.

`NO_MORE_PLANNED_WORK` means this finite fresh plan completed without an
observed drop. It is deliberately not named “converged”: stale metadata,
future state, or unreachable pages may still exist.

## Bounds

Every identity page contains at most 100 identities. The maximum decoded input
is 29,245 bytes, derived from the largest lawful 100-entry identity-plus-digest
advertisement. Control and record messages, encoded bytes, native logical record
bytes, total bearer attempts, and trace entries have separate positive budgets.
The default and hard bearer-attempt/trace ceilings are 100. One attempt carries
one complete encoded message and produces at most two presentations.

The link is deterministic, in memory, and ephemeral. It provides delivery,
drop, duplicate, disconnect, bounded intra-attempt delay, and sender
uncertainty. It is a thin experimental complete-message use of the B1 boundary,
not a socket, queue service, frame protocol, or stable transport adapter.
