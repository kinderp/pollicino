# PX11-PN-B2F decision

## Classification

```text
POLLICINO_FAIR_PAGED_RECONCILIATION_READY_WITH_LIMITS
```

Confidence: **HIGH** for the registered finite static deterministic model.

`PX11-PN-B2F` remains the candidate identifier supplied by the repository
owner. The exact PX10 repository state contained no authoritative replacement.

## Decision

Use ephemeral, bounded, exact page-range directories to derive divergent work
from each receiver's current durable state, and rotate active direction/category
lanes inside one contact. Do not persist a peer cursor. The next contact
reconstructs all planning from local native D2/D3 state and messages received in
that contact.

```text
PERSISTENT_PEER_PROGRESS_AUTHORITIES: 0
DIRECT_REMOTE_STORE_READS: 0
APPLICATION_SPECIFIC_B2_BRANCHES: 0
STARVED_ELIGIBLE_RECORDS: 0
STARVED_DIRECTION: NONE
```

PX3, PX5, PX6, PX8, PX9, and PX10 remain valid unchanged. PX10's explicit
“fair progress at extreme page counts is not proven” limit is resolved for the
registered finite static workloads; its historical evidence is not edited.

## Inherited limits

- D2/D3 state remains bounded to 10,000 entries per native category and pages
  remain 100 identities.
- PX5 persistence retains POSIX/full-snapshot and single-authoritative-writer
  assumptions.
- Complete-record atomicity, local synchronous in-memory B1/B2 invocation, and
  no delivery guarantee remain.
- No TTL/GC, authentication, encryption, routing, custody, automatic D2
  selection/fetch/import, real transport, fragmentation, MTU, timing, RF, or
  production retry is validated.

## New B2F limits

- Page directories expose exact first/last identities, record counts, page
  digests, and canonical order. Detailed reconciliation still exposes exact
  identities and record digests.
- Directory construction/comparison is linear in exact local state. At most 50
  descriptors fit one message, so a maximum native state uses two directory
  messages. Maximum B2F control size is 27,745 bytes, inside B2's 29,245-byte
  complete-unit ceiling.
- A one-page lane requires five successful bearer opportunities; the populated
  two-chunk late-page case requires eight. Budgets below a full causal chain can
  terminate repeatedly without progress.
- Fair lane rotation is ephemeral and deterministic. The success claim assumes
  contacts with sufficient budgets and eventually deliverable attempts.
- Stale ranges remain safe but concurrent growth can make a formerly bounded
  range exceed 100 identities; that fails closed and is a churn limitation.
- Arbitrary infinite churn fairness is unproven. Bounded churn followed by a
  static period converged.
- Exact reconciliation is inefficient at high overlap and provides no metadata
  privacy.

## Failure classifications

- PX10 prefix replay starvation: **B — B2 paging implementation error** for the
  PX11 candidate, corrected additively without changing PX10.
- Two initially short test horizons: **A — test harness error**; observed
  progress was monotonic and only the explicit horizon changed.
- Continuous infinite churn: **H — continuous churn limit**.
- High-overlap disclosure/control cost: **I — disclosure efficiency limit**.
- No D/E/F/G failure was observed.

## Next experiment

The dominant measured frontier is reconciliation disclosure/control cost, not
fairness, fragmentation, or physical I/O. The smallest justified next
experiment is a dedicated compact reconciliation and disclosure-efficiency
gate, provisionally `PX12-PN-B2C`; that name is a candidate, not authoritative.
It should compare exact and compact summaries against the PX11 fairness oracle
without weakening fail-closed native apply or introducing real transport.
