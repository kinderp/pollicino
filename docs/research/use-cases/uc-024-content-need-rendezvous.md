# UC-024 — Content-Need Rendezvous / Interest Ferry

## Idea

Let a node say **"I need this content"** without knowing which peer currently has it. The request itself becomes a small delay-tolerant object that can move through the network until it meets a cache, server or data mule able to satisfy it.

This is the missing pull-side complement to the existing content-distribution use cases. Instead of only pushing known artifacts toward known destinations, PollicinoNet can propagate compact needs/interests and let any authorized holder answer.

## Problem solved

In a fragmented network the requester may know the exact object/hash/version it needs but not where a copy currently exists. A source may also move, go offline or be unknown.

Examples:

- a student needs one Raiatea document version;
- a notebook needs one missing map tile;
- an AI node needs a model shard or adapter;
- a backup restore needs a chunk whose current holder is unknown;
- a field node needs the newest signed bulletin or trust epoch.

Hard-coding one server address wastes the main advantage of opportunistic caching.

## Actors / nodes

- requester node;
- student relay/store-and-forward nodes;
- arbitrary authorized cache holders;
- school/server/NAS nodes;
- optional Internet gateway;
- optional mobile gateway/vehicle.

## Why PollicinoNet fits

PollicinoNet already separates discovery from exact content identity:

- **DISCOVERY:** a compact `Need`/interest, availability hint or cache summary;
- **EXACT:** exact content hash/version and final object/chunk verification;
- **SEMANTIC:** optional broader query such as "latest map pack for coarse zone X" before resolving to an exact object identity.

LoRa is useful for propagating the small request and small availability response. The actual object can then use BLE/Wi-Fi/Internet or physical carry.

Store-carry-forward is important because the requester, relay and content holder do not need to be connected at the same time.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** content ID/version, compact need token, priority, TTL, coarse namespace and availability reply;
- **BLE:** nearby cache inventory exchange and moderate-size object transfer;
- **Wi-Fi/LAN:** chunk/object transfer;
- **Internet:** optional retrieval from a remote authoritative source;
- **physical transport:** a node carries both the pending need and later the resulting object/chunks.

## What we can test now in software

- define a deterministic `ContentNeed` with requester pseudonym, exact target or typed namespace, expiry, priority and privacy class;
- propagate the need through synthetic contact traces;
- allow any valid cache holder to satisfy it;
- suppress duplicate needs while keeping multiple possible responders;
- cancel/retire a need after exact satisfaction;
- simulate stale availability advertisements and caches that disappear before transfer;
- compare source-addressed retrieval against content-addressed opportunistic retrieval;
- test exact-hash requests versus broader semantic/version requests that must resolve to an exact object before transfer;
- use compact cache sketches/Bloom filters only as hints and verify all final content exactly;
- measure need-propagation delay, cache-hit ratio, time-to-first-provider, completed-object rate and redundant-response overhead;
- feed UC-008 contact traces into the simulator to test which nodes are useful request carriers.

A key invariant is:

> discovery may be probabilistic or stale; successful delivery is only declared after exact object verification.

## What requires real hardware

- 4+ nodes with deliberately different cache inventories;
- one requester that cannot directly contact the holder;
- one or more moving student relays;
- a real LoRa need/availability exchange;
- one richer-bearer handover for the requested object;
- measurements of how quickly the need reaches a useful cache and how often stale availability causes wasted contacts.

## Messina teaching scenario

Prepare three content caches representing coarse zones such as `Rometta/Venetico`, `Villafranca` and `Messina`. A student node in one zone requests an exact document or map tile only present in another cache. No route is initially available. A relay carries the compact `ContentNeed`; later another relay or the same relay encounters the cache and eventually returns the exact object over a richer bearer.

A second exercise can use the measured UC-008 contact graph and ask which relay placement minimizes time-to-provider without revealing students' exact movements.

## Privacy / security

Requests themselves reveal interests. A request for a particular document, medical topic, person or location can be sensitive even when content is encrypted. Prefer opaque exact IDs, coarse namespaces, short retention and policy-limited forwarding. Avoid putting human-readable private queries into broadcast LoRa discovery.

Responses require authorization: possessing an object does not automatically mean a peer may disclose it. Final object identity/signature must be verified because cache summaries and availability hints are not authoritative.

## Difficulty

**Medium–High.** The request object is small; the interesting work is duplicate control, privacy, stale cache state, multiple responders and deterministic transition from discovery to exact verified content.

## Research signal

Information-Centric/Named Data Networking treats content names and in-network caching as first-class mechanisms, and recent work continues to explore mobile/edge caching and forwarding under changing topologies. This is conceptually close to PollicinoNet's separation between discovery coordinates and exact content identity, but PollicinoNet should validate its own store-carry-forward behavior rather than import performance claims.

References:

- https://named-data.net/project/archoverview/
- https://www.jocm.us/show-325-2164-1.html
- https://dl.acm.org/doi/10.1145/3517212.3558081
