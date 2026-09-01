# Track D status after FARO PX2

Status: current cross-project status, 2026-09-01

This note records the current Track D state after FARO PX2. It is intentionally narrow and does not promote networking/runtime features beyond their evidence.

```text
D0 — Independent consumer generality
STATUS: CONTINUE / TWO-CONSUMER EVIDENCE STRENGTHENED

D1 — Stable external exact-content surface
STATUS: EXTERNALLY EXERCISED / STABILIZATION REQUIRED

D2 — Generic bounded reference catalog
STATUS: GENERIC CANDIDATE READY / POLLICINO IMPLEMENTATION GATE AUTHORIZED

D3 — Generic asynchronous query/result transport
STATUS: PENDING / AFTER D2 LOCAL VALIDATION

D4 — Persistent distributed node surface
STATUS: RESEARCH / PR #52 / NOT STABLE EXTERNAL API

D5 — Distributed security state and witness gossip
STATUS: RESEARCH / SECURITY-SENSITIVE

D6 — Serverless Internet distribution adapters
STATUS: DEFERRED / DESIGN GATE REQUIRED

D7 — Multi-application integration
STATUS: PENDING
```

## D2 evidence

FARO PX2 concluded:

```text
BOUNDED_REFERENCE_CATALOG_GENERIC_CANDIDATE_READY
confidence: HIGH
```

Two materially different consumers used the same candidate catalog/reconciliation engine:

- FARO scientific-package references;
- CONTENT-like opaque references.

No application-specific branches were required.

Simple exact `RECONCILE_AND_PULL` crossed the preregistered success threshold, while minisketch/IBLT/Bloom/Cuckoo remained unjustified.

Therefore the next authorized Gate is:

```text
PX3-PN-D2 — Pollicino Generic Bounded Reference Catalog Local Multi-Node Validation
```

PX3-PN-D2 may implement the generic primitive inside Pollicino at local/software scope only.

It does not authorize DTN, PNB1/PNC1, bearer runtime, public networking, BitTorrent, DHT, BEP44/BEP46 or deployment.
