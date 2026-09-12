# Pull-based reference catalog exchange

Status: use-case-driven design study, no wire-format adoption yet

## Motivation

`UC-CONTENT-001` suggests that a portable Pollicino node can carry compact references to large authorized content and resolve the content later through Wi-Fi, Internet, NAS or local storage.

A naive implementation would continuously push every reference a node owns or has ever learned to every encountered peer. That approach is deliberately **not** adopted here. With long-lived mobile nodes it creates unbounded catalog growth, stale references, repeated airtime, privacy leakage and eventually O(N)-style anti-entropy exchanges where N is the total history rather than the receiver's actual demand.

The proposed research direction is instead **pull-based reference discovery and reconciliation**.

## Core idea

A node is a bounded mobile index, not an archive of every reference ever observed.

```text
peer A                          peer B
  |                               |
  |---- compact interest/want --->|
  |<--- compact catalog summary --|
  |---- request missing refs ----->|
  |<--- selected coordinates ------|
  |                               |
  + later at home: resolve/fetch   +
```

The receiver determines what is useful. The sender does not push its complete lifetime catalog by default.

## Why not one PND1 per file

Current `PND1` is a complete rendezvous descriptor with a fixed header plus a rendezvous key and optional metadata/authenticator. It is appropriate for an individual discovery item, but repeating the complete descriptor for a large catalog can waste scarce-link bytes.

The experiment should therefore distinguish:

1. full `PND1` descriptors;
2. compact reference identifiers/coordinates inside one shared catalog exchange;
3. full descriptor/manifest retrieval only for references selected by the receiver.

A short catalog identifier is **not proof of content identity**. Exact identity remains resolved through the complete Pollicino manifest/hash or the external ecosystem's authoritative identifier.

## Proposed three-stage flow

### Stage 1 — WANT

The receiver expresses demand as narrowly as practical.

Possible forms, from simplest to more advanced:

- explicit wanted reference IDs;
- content/reference class (`URI`, `MAGNET`, `CID`, `POLLICINO`, local provider);
- topic/category filters supplied by an application;
- size/age/freshness constraints;
- exact wanted-object hashes;
- later, a compact subscription or query representation if a real use case requires it.

Do not introduce a generic query language into PollicinoNet unless multiple use cases require one.

### Stage 2 — CATALOG RECONCILIATION

The peers determine which candidate references are new to the receiver.

Simplest baselines first:

1. explicit short-ID list;
2. sorted/delta-encoded IDs;
3. receiver-known-ID list for small catalogs;
4. compact bitmap when a shared bounded catalog universe exists;
5. Bloom/Cuckoo/sketch/set-reconciliation techniques only when measured catalog size/difference justifies the complexity.

This is conceptually related to PNA2 but the objects being reconciled are **references**, not PCM1 chunk indices.

### Stage 3 — PULL

The receiver asks only for selected entries.

The sender may return, depending on the request and byte budget:

```text
short coordinate
full PND1 descriptor
magnet/URI/CID
provider hint
manifest reference
small manifest
selected content chunks
```

The rich home path later performs actual resolution/retrieval.

## Catalog state

The catalog should distinguish ownership from learned rumor state.

### Owned/pinned references

References representing the node/user's own authorized content or explicit wanted items may be pinned/persistent according to application policy.

### Learned references

References learned from other peers should be bounded.

Candidate retention dimensions:

- expiry/TTL;
- last seen;
- last requested;
- demand/request count;
- source/provenance confidence;
- hop count;
- reference resolvability history;
- topic/category quota;
- total catalog byte/item quota.

A simple TTL + LRU/per-class quota is the first baseline. Popularity/demand-aware retention is an experiment, not a default feature.

## Why "all references ever seen" is risky

Potential failure modes:

- unbounded flash/RAM growth;
- repeated LoRa airtime for stale/unwanted references;
- stale providers and dead links;
- adversarial catalog pollution/spam;
- stable reference identifiers becoming privacy/correlation signals;
- one high-volume topic crowding out useful local references;
- propagation cost growing with node history rather than current usefulness.

Therefore lifetime accumulation may be retained as an **offline archival log** on a rich storage device if desired, but it should not automatically equal the active LoRa exchange catalog.

## Privacy boundary

A coordinate can leak interest/content identity even when it contains no file bytes.

Rules for experiments:

- public content may use stable public identifiers where appropriate;
- private/local content should prefer scoped/opaque rendezvous coordinates rather than public stable hashes when correlation matters;
- a node must not broadcast a user's complete wanted list by default;
- pull filters should reveal no more interest metadata than required by the selected mode;
- learned references should preserve provenance without exposing precise student identity/location.

## Use-case gate

### Concrete use case

A portable node meets many peers during the day and would like to return home with a useful set of references to authorized files/content that can later be downloaded through Internet/NAS/local storage.

### Baselines

Compare:

1. push every full PND1/reference;
2. push every short coordinate;
3. pull by explicit wanted IDs;
4. pull by coarse class/topic then explicit selection;
5. pull + known-reference reconciliation.

### Metrics

- references learned that are later selected/resolved;
- irrelevant references received;
- catalog-control wire bytes;
- reference wire bytes;
- total scarce-link TRC;
- duplicate references suppressed;
- stale/unresolvable references retained/transmitted;
- catalog storage footprint;
- time to useful reference discovery;
- privacy exposure class;
- eventual rich-path retrieval success.

### Success criterion

A pull/reconciliation strategy should be adopted only if it materially reduces scarce-link bytes or irrelevant catalog accumulation compared with the simplest push/explicit-list baselines in a workload we actually care about.

### Kill/defer criterion

If real catalogs are small enough that a simple short-ID list fits comfortably within the encounter budget, keep the simple list and do not add Bloom filters, sketches or a new protocol family.

## Relationship to routing

Reference selection and DTN routing are different dimensions.

Routing answers:

> which encountered node should receive/relay something?

Reference pull answers:

> among the references this peer could provide, which ones does this receiver actually want and not already know?

Experiments should compare these dimensions independently before composing them.

## Decision

**Status: PROTOTYPE/JUSTIFIED AS A RESEARCH EXPERIMENT.**

The use case justifies studying a bounded pull-based reference catalog. It does not yet justify a new wire format. Start with opaque short IDs and explicit request lists, measure them, and only then consider compressed summaries or set-reconciliation structures.
