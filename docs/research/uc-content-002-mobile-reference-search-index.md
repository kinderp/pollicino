# UC-CONTENT-002 — Mobile reference search index

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Summary

A portable Pollicino node acts as a **bounded mobile search index** for authorized content references.

During daily encounters it does not push its complete lifetime catalog to every peer. Instead, two nodes exchange compact interest/wanted state and compact catalog summaries, reconcile what is already known, and let the receiver **pull only new references that are relevant to it**.

The node can therefore return home with references to content it did not know existed in the morning. Once a rich network becomes available, those references can be resolved through Internet, Wi-Fi, NAS, local disks or other authorized providers.

This use case is distinct from `UC-CONTENT-001`:

- `UC-CONTENT-001` asks how to carry a known reference/manifest/content object efficiently;
- `UC-CONTENT-002` asks how a mobile node can **discover useful references from the distributed knowledge of encountered peers without exchanging entire catalogs**.

The use case is intended only for content the user is authorized to retrieve, possess or share.

## Core idea

The network behaves less like a push broadcast system and more like an asynchronous distributed search engine.

```text
peer A                                   peer B
  |                                        |
  |---- WANT / interest summary ---------->|
  |<--- compact candidate catalog summary -|
  |---- reconcile known IDs -------------->|
  |---- PULL selected refs ---------------->|
  |<--- selected coordinates/details -------|
  |                                        |
  +--- physically carry learned refs -------+

later at home:

portable node
   |
   +-- Wi-Fi / Internet
   +-- NAS / HDD / PC
   +-- authorized torrent client
   +-- CID/content resolver
   |
   v
resolve and retrieve selected content
```

## Actor

A person carrying a portable Pollicino node through environments where it meets many other nodes during the day and later returns to a richer home network.

Examples include:

- a student who meets many peers at school;
- a commuter moving between towns;
- a participant at an event/conference;
- an offline/community network user whose node periodically reaches richer connectivity.

## Situation

Each node possesses or knows references to a potentially large set of authorized files/content:

- magnet/info-hash;
- URL;
- CID/content ID;
- Pollicino rendezvous coordinate;
- provider hint;
- personal NAS/HDD object reference;
- manifest reference;
- locally generated object identifier.

Over time the node also learns references from other peers.

Naively pushing all owned + learned references at every contact makes traffic and storage grow with the node's lifetime history rather than with current usefulness.

## Problem

The node needs to answer two questions under a scarce contact budget:

1. **Which references known by the encountered peer are potentially interesting to me?**
2. **Which of those references do I not already know?**

Only after those questions are answered should scarce-link bytes be spent on the actual selected references/details.

## Three-stage exchange

### 1. WANT / INTEREST

The receiver expresses demand as narrowly as practical.

Initial/simple forms:

- explicit wanted object/reference IDs;
- reference class (`URI`, `MAGNET`, `CID`, `POLLICINO`, local provider);
- coarse application/topic category;
- freshness/age constraint;
- optional size/content-class constraint.

DNA may provide topic/subscription semantics when DNA is present, but PollicinoNet must also support the use case without requiring DNA.

Do not introduce a generic query language unless multiple real use cases require one.

### 2. CATALOG RECONCILIATION

The peers determine which candidate references are new to the receiver.

Start with the simplest baselines:

1. explicit short-ID list;
2. sorted/delta-encoded short IDs;
3. receiver-known-ID list for small catalogs;
4. bounded bitmap only when a shared bounded universe exists;
5. Bloom/Cuckoo/sketch/set reconciliation only after measurements justify them.

A catalog short ID is only a lookup/reconciliation token. It is not proof of object identity.

### 3. PULL

The receiver asks for selected entries only.

Possible returned forms:

- short Pollicino coordinate;
- full PND1 descriptor;
- magnet URI / info-hash;
- URL/CID;
- provider hint;
- manifest reference;
- small manifest;
- selected chunks if no richer provider is expected and the contact budget justifies it.

## Catalog lifecycle

The active LoRa catalog is **not** the same thing as the complete historical archive.

### Owned/pinned state

The node may retain persistently:

- its own authorized references;
- explicitly pinned references;
- explicit wanted objects;
- references required by active application policy.

### Learned state

References learned from other nodes are bounded and subject to retention.

Initial baseline:

- TTL/expiry;
- LRU/last-seen;
- total item/byte quota;
- per-class/topic quota.

Potential later experiments, only if justified:

- last-requested time;
- request/popularity count;
- source/provenance confidence;
- successful resolvability history;
- hop count;
- adaptive retention by topic demand.

A node may optionally keep a complete archival history on rich local storage, but the active LoRa exchange catalog remains bounded.

## Why not propagate every coordinate ever seen?

Lifetime push-all creates several failure modes:

- unbounded flash/RAM growth;
- repeated transmission of stale/unwanted references;
- catalog traffic proportional to lifetime history;
- dead provider/link propagation;
- privacy/correlation leakage;
- catalog pollution/spam;
- high-volume categories crowding out useful local information;
- duplicate reference circulation.

The default experiment therefore treats the node as a **bounded index cache**, not an immortal rumor database.

## Relationship with PND1

Current PND1 is an individual rendezvous descriptor, not a bulk catalog representation.

Repeating a complete PND1 for every catalog item adds repeated descriptor overhead. Therefore the experiment should compare:

1. full PND1 per reference;
2. compact short catalog IDs with one shared exchange header;
3. full PND1/detail retrieval only after the receiver selects an item.

No new catalog wire format is adopted by this use case alone.

## Relationship with PNA2

PNA2 asks:

> Which chunks of this known manifest differ between peers?

UC-CONTENT-002 asks:

> Which references in this candidate catalog are new/useful to this receiver?

Both are set-reconciliation problems at different semantic levels.

The implementation should reuse generic reconciliation primitives only if measurements demonstrate genuine commonality; do not force both problems into one abstraction prematurely.

## Relationship with DNA

DNA can provide semantic filtering before reference reconciliation:

```text
peer knows 100,000 references
        |
DNA topic/subscription filtering
        v
2,000 relevant candidates
        |
reference reconciliation
        v
150 unknown candidates
        |
contact byte budget / ranking
        v
40 selected references
```

Without DNA, PollicinoNet can still use explicit wanted IDs or coarse application-defined reference classes.

## Relationship with routing

Routing and reference discovery are orthogonal dimensions.

Routing decides:

> Which encountered node should receive/relay a message/reference?

Reference discovery decides:

> Which references available from this peer are useful and unknown to this receiver?

The two should be benchmarked independently before composing them.

## Baselines

Compare at least:

1. push all full references/descriptors;
2. push all short coordinates;
3. explicit pull by wanted ID;
4. pull by coarse class/topic then explicit selection;
5. pull + known-reference reconciliation;
6. later, compressed/sketch summaries only when simple methods stop scaling.

## Measurable hypotheses

H1. Pull-based selection substantially reduces irrelevant reference traffic compared with push-all when peer catalogs are large and user interest is sparse.

H2. Reference reconciliation reduces duplicate reference traffic when nodes repeatedly meet overlapping social/contact groups.

H3. A mobile node can accumulate useful new references across multiple encounters and later resolve a significant subset through a rich home path.

H4. Bounded TTL/quota retention prevents active catalog growth from becoming proportional to total lifetime encounters while preserving useful discovery performance.

H5. Dense school/event mixing can improve reference discovery diversity without requiring bulk content transfer over LoRa.

## Metrics

Track separately:

- candidate references at sender;
- references matching receiver interest;
- references already known by receiver;
- references actually pulled;
- useful references later selected/resolved;
- irrelevant references received;
- duplicate references suppressed;
- catalog-control wire bytes;
- selected-reference wire bytes;
- total scarce-link TRC;
- active catalog item/byte footprint;
- stale/unresolvable references retained;
- references expired/evicted;
- number of distinct encounters contributing useful references;
- time from first discovery to home resolution;
- eventual rich-path retrieval success;
- privacy exposure class.

Rich-path payload bytes must be reported separately. Moving retrieval to home Internet/NAS changes where/when cost occurs; it does not make payload cost disappear.

## Minimal synthetic experiment

Create a scenario with:

- 20–100 pseudonymous mobile nodes;
- overlapping but non-identical reference catalogs;
- multiple reference categories/topics;
- sparse per-node interest sets;
- repeated dense school-hub contacts followed by sparse territorial contacts;
- home/rich-path resolution events;
- configurable catalog TTL/quota.

Compare:

```text
PUSH_ALL_FULL
PUSH_ALL_SHORT_IDS
EXPLICIT_PULL
INTEREST_PULL
INTEREST_PULL + RECONCILIATION
```

Use paired seeds and the existing evidence methodology.

Do not derive real LoRa capacity from synthetic duration.

## Success criteria

Continue toward implementation if at least one realistic workload shows that pull + reconciliation materially reduces scarce-link catalog traffic and irrelevant accumulation while maintaining or improving eventual useful-reference discovery.

The simplest successful method wins. If explicit short-ID lists are sufficient, do not add probabilistic sketches.

## Kill/defer criteria

Defer added complexity when:

- typical catalogs are small enough that simple lists fit easily;
- filtering reveals more private interest metadata than the bytes saved justify;
- reconciliation overhead exceeds saved duplicate traffic;
- references become stale before home resolution often enough to make the feature low-value;
- catalog retention/storage complexity dominates the benefit;
- a new wire protocol would be required without a demonstrated gain.

## Privacy and security boundary

References can reveal content interest even when the content itself is not transferred.

Initial rules:

- do not broadcast the user's complete wanted list by default;
- use scoped/opaque coordinates for private/local content when stable public identifiers would create correlation risk;
- preserve provenance/source confidence without exposing exact student identity/location;
- apply quotas and validation against catalog poisoning/spam;
- application policy determines whether a particular reference/source is authorized.

## Physical evidence boundary

This use case can be modeled and benchmarked synthetically now.

Claims about how many catalog entries fit in a real encounter, discovery latency, collision behavior, range, simultaneous school nodes, airtime or energy remain blocked by the existing **HW-006 physical-evidence gate** and later field campaigns.

## Decision

**Status: PRIMARY USE CASE / PROTOTYPE-DRIVING.**

The use case justifies a bounded pull-based reference-index experiment and catalog-reconciliation benchmarks.

It does **not** yet justify:

- a new bulk catalog wire protocol;
- Bloom filters/sketches/IBLT by default;
- unlimited lifetime propagation of references;
- embedding BitTorrent/IPFS/HTTP semantics in PollicinoNet core.

Start with opaque short IDs, explicit interest/want state, TTL/quota retention and simple reconciliation. Measure before generalizing.
