# PX3-PN-D2 — Pollicino Generic Bounded Reference Catalog Local Multi-Node Validation

Status: AUTHORIZED NEXT GATE / SOFTWARE-ONLY, 2026-09-01

## Why this Gate exists

FARO PX2 concluded:

```text
BOUNDED_REFERENCE_CATALOG_GENERIC_CANDIDATE_READY
confidence: HIGH
```

The candidate passed a two-consumer test:

- FARO scientific-package references;
- CONTENT-like opaque lawful-content references.

Both consumers used the same candidate catalog/reconciliation engine with zero application-specific branches.

PX2 also demonstrated material model/protocol byte savings for simple exact reconciliation and pull, while advanced probabilistic/sketch structures remained unjustified.

The next question therefore belongs in Pollicino:

> Can the proven candidate be implemented as a small application-independent Pollicino primitive and remain correct across multiple local nodes without importing FARO/CONTENT semantics or prematurely activating DTN/network functionality?

## Scope

PX3-PN-D2 may implement and validate a **local generic bounded reference catalog** in Pollicino.

It may include:

- bounded opaque reference bytes;
- deterministic logical keys;
- canonical catalog snapshots/state;
- item and byte quotas;
- deterministic insertion/merge/rejection;
- exact duplicate suppression;
- exact receiver-known-ID comparison;
- exact set difference/reconciliation;
- selected/new reference pull;
- deterministic local multi-node exchange simulation;
- optional in-memory node/catalog fixtures;
- FARO-like and CONTENT-like application adapters/fixtures used only for conformance testing;
- model/protocol byte accounting;
- restart/persistence design analysis only if required to define the boundary, not implementation unless separately justified.

## Explicitly out of scope

PX3-PN-D2 must not implement or activate:

- sockets;
- HTTP/REST/RPC;
- public networking;
- LoRa/BLE/Wi-Fi transport;
- PNB1/PNC1 catalog carriage;
- custody;
- DTN routing;
- NodeRuntime/bearer runtime integration;
- BitTorrent;
- Mainline DHT;
- BEP44;
- BEP46;
- IPFS;
- federation;
- reputation/ranking systems;
- auto-fetch;
- auto-import;
- application trust;
- application Recommendation logic.

No physical hardware is required.

## Core generality invariant

Pollicino core must be able to process catalog items without understanding their application meaning.

Forbidden core patterns include semantic equivalents of:

```text
if application == "faro": ...
if application == "content": ...
if evidence_grade == ...: ...
if model_backend == ...: ...
if reference_is_magnet == ...: ...
```

The generic primitive may know only the minimal information required for catalog correctness, such as:

```text
logical key
canonical bounded opaque reference bytes
optional generic observation/retention metadata if independently justified
```

Application adapters own application semantics.

## Candidate identity model

The generic primitive must not assume that Pollicino transport identity is the authoritative application identity.

Each adapter supplies a deterministic logical key.

For FARO-like fixtures, the logical key corresponds to FARO `package_id`.

For CONTENT-like fixtures, the adapter supplies the opaque application reference identity.

Pollicino must not parse the application object to derive meaning.

## Candidate bounds inherited from PX2 evidence

PX2 exercised:

```text
max reference bytes:     4096
max retrieval variants:     8   # application-side FARO bound; do not blindly make generic
max catalog items:       10000
max catalog bytes:    16777216
max exchange items:        100
```

PX3-PN-D2 must review which bounds genuinely belong to the generic Pollicino primitive.

Do not copy FARO-specific `max retrieval variants = 8` into generic core unless a generic need is demonstrated.

Safety/model bounds are not network-optimal parameters.

## Required simplest baseline order

Keep the PX2 simplicity result.

Compare/retain only as needed:

1. explicit bounded full-reference list;
2. deterministic sorted logical IDs;
3. receiver-known-ID comparison;
4. selected/new reference pull;
5. exact reconcile-and-pull.

Do not add:

```text
minisketch
IBLT
Bloom
Cuckoo
```

unless a new separately preregistered discriminating workload demonstrates that the exact/simple methods are insufficient.

PX2 currently says they are not justified.

## Local multi-node model

Use at least three deterministic local nodes:

```text
A
B
C
```

Each owns a bounded catalog with overlapping and non-overlapping logical keys.

Required flows include:

```text
A <-> B
B <-> C
A <-> C
```

No sockets are needed. Local method calls/fixtures are sufficient.

The Gate should show that different nodes may hold different catalog state without requiring global consensus.

## Required correctness scenarios

At minimum validate:

1. empty catalog;
2. one item;
3. deterministic insertion order;
4. exact duplicate insertion;
5. same logical key + same immutable identity + compatible operational variation;
6. same logical key + conflicting immutable reference bytes/identity;
7. malformed reference;
8. oversized reference;
9. item quota overflow;
10. byte quota overflow;
11. exchange-page bound;
12. zero overlap;
13. partial overlap;
14. high overlap;
15. full overlap;
16. receiver knows none;
17. receiver knows all;
18. sparse selected pull;
19. exact reconcile-and-pull;
20. repeated exchange/idempotency;
21. A->B then B->C propagation in local model;
22. independently ordered nodes converge to identical canonical state when logical contents become equal;
23. eviction/removal does not become application invalidation;
24. application adapter may reject/ignore an item without changing generic catalog semantics.

## Two-consumer conformance

PX3-PN-D2 must include two adapters/fixtures.

### FARO-like fixture

The Pollicino repo should not import FARO runtime code as a mandatory dependency.

Use a small canonical fixture contract reproducing only the already-proven generic boundary:

```text
logical key
opaque bounded reference bytes
```

Document provenance back to FARO PX2.

Do not duplicate FARO scientific logic.

### CONTENT-like fixture

Use synthetic lawful opaque references.

No external download occurs.

The same generic catalog engine must process both consumers without branches.

## Conflict semantics

A generic catalog must never silently choose between incompatible values bound to the same logical key.

Required behavior:

```text
same logical key
+ incompatible immutable value
-> explicit conflict / rejection / HOLD-style result
```

No:

- last-write-wins by default;
- majority vote;
- popularity rule;
- provider-count rule.

The exact canonical error/result name should follow Pollicino conventions.

## Operational variants

PX2 showed that one FARO package may have multiple compatible retrieval hints/transport layouts while retaining one application identity.

PX3 must decide whether generic core should:

A. store exactly one opaque application reference value per logical key and leave variants entirely to the adapter; or
B. support a small generic bounded set of equivalent opaque variants.

Prefer A unless B is independently required by both consumers.

Do not generalize FARO retrieval-hint structure into Pollicino merely because FARO has it.

## Canonical state

If the catalog exposes a snapshot/serialization, it must be:

- versioned;
- deterministic;
- canonical;
- bounded;
- insertion-order independent.

Same logical state -> byte-identical canonical output.

A digest may protect deterministic state/integrity for local tests.

A digest is not trust or application authenticity.

## Authority boundary

The generic catalog says only:

> this node currently knows an opaque bounded reference under logical key X.

It does not mean:

```text
trusted
valid science
authorized content
locally validated
recommended
popular = better
many peers = corroborated
```

Adapters/applications retain those decisions.

## Storage/retention boundary

PX3 should implement only the minimum local bounds necessary to validate the primitive.

If removal/eviction is included, it must mean only:

```text
reference no longer retained/discoverable in this catalog
```

not:

```text
underlying application object deleted
scientifically invalid
revoked
```

Do not couple the catalog to `PollicinoStore` object deletion unless a separate Gate justifies lifecycle coordination.

## Model accounting

PX3 may reproduce deterministic protocol byte accounting for local exchange strategies.

Label it:

```text
MODEL_PROTOCOL_ACCOUNTING_ONLY
```

No claims about:

- real bandwidth;
- latency;
- energy;
- LoRa capacity;
- Internet scalability.

## PX2 reference point

PX2 preregistered:

```text
success threshold:
>= 50% reduction in a target workload

kill threshold:
no >= 25% reduction in any size >= 100 workload
```

Representative FARO fixture:

```text
1000 items
0% overlap
1% interest

push-all:
1,250,383 bytes

reconcile-and-pull:
55,539 bytes

reduction:
95.558%
```

PX3 does not need to rediscover the same result from scratch, but its native Pollicino implementation must reproduce equivalent semantics on deterministic fixtures and must not materially regress accounting without explanation.

## Security/privacy

The generic primitive must fail closed on malformed/bounds-violating state.

Do not place into generic catalog fixtures:

- usernames;
- hostnames;
- local filesystem paths;
- IP/MAC addresses;
- private keys;
- real student identity;
- complete FARO MachineProfile;
- FARO LocalTrustStore/Recommendation;
- sensitive copyrighted-content fixtures.

## Dependency rule

The primitive should use the Python standard library and existing Pollicino project dependencies unless a new dependency is independently justified.

No new reconciliation dependency is expected or authorized by PX2 evidence.

## Required classification

End with exactly one primary classification:

```text
POLLICINO_BOUNDED_REFERENCE_CATALOG_LOCAL_READY
POLLICINO_BOUNDED_REFERENCE_CATALOG_LOCAL_READY_WITH_LIMITS
POLLICINO_CATALOG_GENERICITY_FAILED
POLLICINO_CATALOG_IDENTITY_UNSAFE
POLLICINO_CATALOG_BOUNDS_UNSAFE
POLLICINO_CATALOG_COMPLEXITY_NOT_JUSTIFIED
INCONCLUSIVE
```

Confidence:

```text
HIGH
MEDIUM
LOW
```

## Strongest success meaning

`POLLICINO_BOUNDED_REFERENCE_CATALOG_LOCAL_READY` means:

> Pollicino now has a validated, bounded, application-independent local reference catalog/reconciliation primitive that works for multiple local nodes and two materially different consumer fixtures without application branching.

It does **not** mean:

- distributed network ready;
- DTN ready;
- persistent-node catalog ready;
- public registry ready;
- Internet P2P ready.

## Stop conditions

STOP rather than widening the Gate if:

- FARO semantic parsing is required in core;
- CONTENT semantic parsing is required in core;
- a universal query language starts being designed;
- PR #52 DTN/custody/bearer APIs become necessary;
- sockets/networking become necessary;
- BitTorrent/DHT appears necessary;
- a new crypto authority is introduced;
- advanced reconciliation is added without a new discriminating Gate;
- application identity is replaced by Pollicino transport identity.

A STOP is a valid scientific result.

## Expected deliverables

Use repository conventions, but produce at least:

```text
docs/research/px3-pn-d2-*.md or equivalent gate/checkpoint docs
artifacts/px3-pn-d2/*.json or existing experiment-record equivalent
```

Code should live in a generic Pollicino namespace, not an application integration namespace, only if the Gate supports that decision.

Focused tests should cover the required correctness matrix plus two-consumer conformance.

Run the full feasible Pollicino test suite and document unrelated optional skips/errors separately.

## Next-Gate rule

Choose exactly one next Gate from evidence.

Likely paths:

### If local generic catalog is READY

Next should validate persistence/local restart or local catalog-node lifecycle **before** DTN carriage, unless persistence is already independently proven reusable.

A possible next Gate:

```text
PN-D2R — Persistent Bounded Reference Catalog Restart/Recovery
```

or, if existing persistence primitives can be reused without new semantics:

```text
PX4-PN-D4 — Bounded Catalog over Persistent Pollicino Node Local Lifecycle
```

### If persistence is unnecessary for the immediate architecture

A deterministic multi-node partition/contact model may be next, still without real network execution.

### Do not jump directly to

```text
BitTorrent
DHT
BEP44/BEP46
public deployment
```

## Still blocked

```text
production distributed catalog
public FARO/Pollicino network
DTN catalog carriage
PNB1/PNC1 catalog integration
bearer runtime catalog integration
BitTorrent
Mainline DHT
BEP44
BEP46
IPFS
auto-fetch
auto-import
auto-trust
auto-recommend
```
