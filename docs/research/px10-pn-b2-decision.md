# PX10-PN-B2 decision

## Classification

```text
POLLICINO_INDEPENDENT_ENDPOINT_RECONCILIATION_READY_WITH_LIMITS
```

Confidence: **HIGH** for deterministic local complete-message behavior.

`PX10-PN-B2` remains a candidate identifier supplied by the repository owner;
the baseline repository had no authoritative post-PX9 gate number. PX9 was
preserved locally at exact `checkpoint/px9-pn-b1` before this branch began.

The selected protocol uses exact bounded identity-plus-digest advertisements,
missing-identity requests, explicit reference-selection messages, and one
complete native record per record message. The encoding is explicitly
experimental. Native stores remain the only possession/validity authority.

All preregistered success criteria passed. Direct remote-store reads,
application-specific B2 branches, and concrete-bearer D4 branches are zero.
Persistent ACK/session state is not required. Loss before commit mutates
nothing; uncertainty after commit causes zero record retransfers after restart;
conflicts fail closed; permanent loss terminates boundedly; 105+105 pagination
and restarted mule flows pass.

PX3, PX5, PX6, PX8, and PX9 remain valid unchanged. `catalog.py`,
`persistent_catalog.py`, `query.py`, `persistent_query.py`, `contact.py`,
`bearer.py`, and `link.py` were not modified.

## Inherited limits

- bounded D2/D3 state, no TTL/GC/query authentication;
- PX5 POSIX/full-snapshot, single-authoritative-writer assumptions;
- PX8/PX9 complete-record atomicity, local deterministic accounting, no
  routing, custody, automatic selection/fetch/import, or delivery guarantee;
- no production bearer, fragmentation, MTU, timer, retry, RF, or security
  validation.

## New B2 limits

- synchronous in-process endpoint invocation around a real encoded-byte
  boundary, not independent OS processes communicating via I/O;
- four experimental message types and a 29,245-byte maximum message;
- exact identifiers, per-record digests, requests, page shape, and selected D2
  keys are disclosed in clear;
- SHA-256 provides accidental integrity only, not authenticity or secrecy;
- reordered self-contained requests/records are accepted and bounded native
  state remains the authority; unsolicited-record authentication is deferred;
- exact reconciliation is linear and full scans repeat on fresh contacts;
- fair progress at extreme page counts is not proven and later categories can
  starve under the 100-attempt ceiling;
- no stale-snapshot convergence claim, clock/reordering model, corruption
  recovery, concurrent endpoint execution, or production wire compatibility;
- the encoded-message link is a B2-local B1 adapter, not the older PNF1 link.

## Next experiment

The smallest evidence-justified experiment is bounded fair reconciliation
paging plus disclosure-efficiency validation: prove that repeated finite
contacts can cover every native page without a persistent peer/session cursor,
and measure whether exact identity/digest disclosure can be reduced safely.
Repository evidence provides no authoritative identifier for that experiment,
so none is invented here. Fragmentation and real transport remain later
frontiers unless this reconciliation experiment changes the evidence.
