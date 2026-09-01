# FARO PX2 — bounded reference catalog cross-project checkpoint

Status: PASS / GENERIC CANDIDATE READY, 2026-09-01

## Result

FARO gate `PX2 — Bounded Reference Catalog over Pollicino` concluded:

```text
BOUNDED_REFERENCE_CATALOG_GENERIC_CANDIDATE_READY
confidence: HIGH
```

This result means that a bounded reference/catalog model survived a two-consumer experiment and is now justified as a **generic Pollicino candidate**. It does **not** mean that Pollicino already exposes a stable catalog API, that a distributed registry exists, or that DTN/Internet/P2P execution is authorized.

## Provenance

```text
FARO_BASE:
e2ad5e2c44e05112b212b18c91d67df184999795

FARO_IMPLEMENTATION_COMMIT:
3443e86eeaa90339726e202e30fc04eec687ab52

FARO_FINAL_CLOSURE:
6edf1f7d6f3ff91e07822a28910e7335958e1da3

POLLICINO_PIN:
750405a4aba86e7335141383396edf84347fc1d8

POLLICINO_MODIFIED:
NO

PR52_DEPENDENCY:
NO
```

Validation reported by FARO:

```text
FARO full suite:       488 PASS
PX2 focused:            52 PASS
PX1 regression:         29 PASS
Pollicino relevant:     29 PASS
doc links:             494 PASS / 0 broken
compileall:             PASS
git diff --check:       PASS
privacy scan:           PASS
private-key scan:       PASS
runtime network:        NOT_USED_BY_DESIGN
benchmark:              NOT_RUN_BY_DESIGN
accounting:             MODEL_PROTOCOL_ACCOUNTING_ONLY
```

## Candidate contract established by PX2

FARO used:

```text
reference schema:
faro.pollicino-reference.v0

catalog schema:
faro.bounded-reference-catalog.v0
```

The FARO catalog item did **not** require a new FARO `CatalogEntry`: existing canonical `FAROPollicinoReference` bytes were sufficient.

The logical application identity remained:

```text
FARO package_id
```

while Pollicino transport representations and retrieval hints remained operational metadata.

Bounds exercised by PX2:

```text
max reference bytes:     4096
max retrieval variants:     8
max catalog items:       10000
max catalog bytes:    16777216
max exchange items:        100
```

These are safety/model bounds, not measured network-optimal parameters.

## Genericity evidence

PX2 exercised two materially different consumers:

1. FARO signed scientific-package references;
2. CONTENT-like bounded opaque lawful-content references.

Both used the same candidate catalog/reconciliation engine.

```text
GENERIC_ENGINE_APPLICATION_BRANCHES = 0
```

The engine did not parse or branch on:

- FARO evidence grades;
- FARO MachineProfile;
- FARO Recommendation;
- DS4/Metal/model semantics;
- CONTENT URI/magnet/content semantics.

Application adapters remained responsible for application meaning.

This satisfies the Independent Consumer Generality Gate strongly enough to justify a **Pollicino-side implementation/validation Gate**.

## Strategy result

PX2 compared simple exact strategies and selected:

```text
RECONCILE_AND_PULL
```

for unknown-catalog discovery.

`PULL_SELECTED` remained the cheapest baseline when desired IDs were already known, while receiver-known comparison was strong in high-overlap/all-interest regimes.

Pre-registered thresholds:

```text
success:
>= 50% reduction in at least one target workload

kill:
no >= 25% reduction in any size >= 100 workload
```

Representative FARO model workload:

```text
catalog items: 1000
overlap:       0%
interest:      1%

push-all full references:
1,250,383 bytes

reconcile-and-pull:
55,539 bytes

modeled reduction:
95.558%
```

This is deterministic protocol/model byte accounting. It is not measured network throughput, latency, energy or LoRa/Internet capacity.

## Simplicity decision

PX2 did **not** justify probabilistic or advanced reconciliation structures.

Still deferred:

```text
minisketch
IBLT
Bloom filters
Cuckoo filters
```

The exact/simple mechanisms already crossed the pre-registered success threshold. Complexity must not be added merely because more sophisticated algorithms exist in Pollicino research.

## Identity and merge semantics

PX2 preserved:

```text
FARO package identity
    != Pollicino transport identity
```

Different Pollicino chunk layouts for the same FAROPackage remain one logical FARO package.

Compatible additional retrieval hints may become bounded operational variants of the same item.

A hard conflict such as:

```text
same package_id
+ incompatible digest/schema/exact-byte identity
```

produces:

```text
CATALOG_REFERENCE_CONFLICT
```

No majority vote, popularity rule or last-write-wins scientific decision is allowed.

## Authority boundary

PX2 preserved all required non-escalation properties:

```text
catalog presence
    != trust
    != evidence grade
    != local validation
    != recommendation

provider count
    != scientific corroboration

catalog popularity
    != scientific corroboration
```

Catalog metadata remains a discovery hint.

The retrieved and independently verified FAROPackage remains authoritative for FARO application/scientific semantics.

Catalog exchange produced:

```text
LocalKnowledgeStore mutation: NONE
LocalTrustStore mutation:     NONE
Recommendation mutation:      NONE
```

Catalog eviction does not delete previously imported FARO evidence and does not scientifically invalidate a package.

## Privacy boundary

PX2 reported no exposure of:

- complete MachineProfile;
- local paths;
- LocalTrustStore;
- LocalKnowledgeStore internals;
- Recommendation;
- private keys.

FARO query/filter semantics remained local to FARO.

A generic Pollicino catalog must preserve this property: it should reconcile bounded opaque references/IDs without requiring application-private query state.

## Pollicino decision

The bounded reference catalog moves from:

```text
SECOND_CONSUMER_JUSTIFIED
```

to:

```text
GENERIC_CANDIDATE_READY
```

It does **not** yet move to:

```text
GENERIC_REUSE_PROVEN
STABLE_PUBLIC_API
DISTRIBUTED_CATALOG_READY
PRODUCTION_READY
```

Those require implementation and validation inside Pollicino.

## Next gate

The next authorized cross-project/generalization Gate is:

```text
PX3-PN-D2
Pollicino Generic Bounded Reference Catalog Local Multi-Node Validation
```

PX3-PN-D2 should run primarily in the Pollicino repository and should:

- implement the smallest generic bounded catalog primitive justified by PX2;
- retain opaque application-owned reference bytes;
- validate FARO-like and CONTENT-like adapters/fixtures;
- validate deterministic local multi-node reconciliation and pull;
- preserve item/byte/exchange bounds;
- preserve exact conflict semantics;
- keep advanced sketches deferred unless a new discriminating Gate justifies them;
- avoid FARO/CONTENT-specific branches in core;
- avoid DTN, PNB1/PNC1, bearer runtime, sockets and Internet execution.

## Still blocked

After PX2, these remain blocked unless separately authorized:

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
TuneRun
CR9
```

## Current product story

```text
FARO RG2-PX0
  -> POLLICINO_SUBSTRATE_REUSE_READY_WITH_BOUNDARIES

FARO PX1
  -> FAROPACKAGE_POLLICINO_EXACT_CONTENT_READY

FARO PX2
  -> BOUNDED_REFERENCE_CATALOG_GENERIC_CANDIDATE_READY

next:
PX3-PN-D2
  -> Pollicino-native local multi-node validation
```
