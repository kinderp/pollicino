# PX8-PN-D4 scientific report

## Question and hypothesis

Can independent persistent Pollicino nodes accumulate correct progress across
finite contacts without a bearer, route, custody log, or persistent contact
journal? The preregistered hypothesis was that a fresh reconciliation against
the receiver's durable D2/D3 state is sufficient.

## Method

The implementation starts from exact PX6 closure
`3d574773035677d30eb566dc1fa7c0f0ecb9c051`. It orchestrates existing D3 query
and result reconciliation and existing D2 selected pull. Each missing record is
budgeted and committed separately. Deterministic injection stops at a phase
boundary, before apply, or after a committed apply. Three independent durable
roots model A, B, and mule C; C is closed and reopened between encounters. One
restart crosses a real subprocess boundary.

The workload test stores 105 queries. Contact 1 commits 100 and exhausts its
item budget. After both nodes restart, Contact 2 scans durable identities,
skips the first 100, and commits only the final 5. The metric
`ALREADY_DURABLE_RECORDS_RETRANSFERRED` is zero.

## Finding

Model A passed. Query A→C→B and result B→C→A survive mule restarts. An orphan
result remains bounded and non-actionable until its query arrives. Explicit D2
selection carries one byte-identical reference B→C→A. Duplicate loops converge;
query, result, and reference conflicts fail closed; quota failure preserves
earlier commits and does not partially apply the failing record. Contact order
and history do not alter canonical D2/D3 state.

The large restart test also exposed an inherited PX6 restore defect: D3 reopened
only its first 100-item page. PX8 corrects `_load_into_memory` to iterate every
bounded page and adds a 105-query/105-result regression. Durable encoding and
record identity are unchanged.

Exact FARO PX7 at `43725b2988f24ebad93fbb79f11cbb3d410432aa`
passed through the same mule core. Candidate receipt did not mutate D2,
knowledge, trust, or recommendation. Explicit D2 carry, PX1 exact retrieval,
FARO verification, and explicit import remained separate. A deliberately bad
signature passed contact/D2/PX1 exactness and failed only as
`FARO_SIGNATURE_FAILURE`.

## Result

```text
CLASSIFICATION:
POLLICINO_BEARER_NEUTRAL_CONTACT_STORE_CARRY_FORWARD_READY_WITH_LIMITS

CONFIDENCE:
HIGH

CONTACT_PROGRESS_MODEL:
EPHEMERAL_SESSION_DURABLE_STATE_RECONCILIATION

CONTACT_RESUME_MODEL:
NEW_CONTACT_RECONCILES_FROM_DURABLE_STATE
```

Limits are POSIX-tested single-writer full-snapshot persistence, no concurrent
reader contract, local complete-record method calls, bounded linear identifier
scans, and no TTL/GC, authentication, routing, custody, fragmentation, stable
wire protocol, or delivery guarantee. No performance benchmark was run.
