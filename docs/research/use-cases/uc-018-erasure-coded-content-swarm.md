# UC-018 — Erasure-Coded Content Swarm

## Idea

Distribute a large exact object across several intermittently connected carriers so that the destination can reconstruct it after collecting **enough independent coded shards**, even if no single student/data-mule node ever carries the whole object.

A simple first design can use deterministic Reed–Solomon-style `k-of-n` shards. A later research branch may compare rateless/fountain/network-coding approaches, but coding is an application-layer object strategy, not a change to the frozen LoRa PHY.

## Problem solved

Ordinary chunk replication works well when one relay eventually meets the destination or when there is enough storage to duplicate many chunks. A student network across the Messina hinterland can instead have short, unpredictable contact windows: one student may carry only part of a map pack, another part of a dataset and a third a different subset. If the destination needs one specific missing chunk, progress can stall.

Erasure coding changes the question from "did I receive these exact N chunks?" to "did I receive enough valid shards to reconstruct the exact original object?". This can increase path diversity in a delay-tolerant content experiment, but any benefit must be measured on PollicinoNet traces rather than assumed.

## Actors / nodes

- origin node that owns the exact source object;
- encoder/cache node producing a signed coding manifest;
- student relay/store-and-forward nodes carrying different shards;
- destination node accumulating shards until reconstruction is possible;
- optional school/server/NAS node holding the complete source as a reference copy.

## Why PollicinoNet fits

PollicinoNet already has content-addressed exact objects, per-node stores, inventories and opportunistic handover. The coding manifest can remain an `EXACT` object that binds:

- source object hash;
- coding scheme/version;
- `k` and `n` parameters;
- shard IDs/hashes;
- original size;
- encryption/provenance metadata.

LoRa is useful for compact shard inventories, need summaries, manifest hashes and rendezvous. Bulk shards should normally move over BLE/Wi-Fi/LAN/Internet or physical carry when those bearers are available. Nothing in this use case requires changing the PHY.

## Possible bearers

- **LoRa:** object/manifest IDs, compact shard availability, need summaries, priorities and acknowledgements;
- **BLE/Wi-Fi/LAN:** actual coded shards and reconstructed-object verification;
- **Internet:** optional source/cache refresh and comparison baseline;
- **physical transport:** students carry shard caches between otherwise disconnected areas.

Small shard transfer over LoRa may be tested only as a measured experiment within the existing frozen PHY and airtime constraints; it is not assumed to be the preferred bulk path.

## What we can test now in software

- implement deterministic `k-of-n` erasure coding for synthetic/public objects;
- content-address the source object, manifest and every shard;
- give virtual nodes disjoint shard subsets and replay UC-008-style synthetic contact windows;
- verify reconstruction succeeds only from a valid sufficient shard set;
- inject missing, duplicated, stale, corrupted and malicious shards;
- compare plain chunk replication versus coded distribution under the **same** contact trace;
- measure completed-object rate, bytes transferred per bearer, time-to-reconstruction, redundant bytes and cache occupancy;
- prove the reconstructed object is bit-for-bit identical to the source hash;
- test re-encoding/version changes without confusing shards belonging to different source-object hashes.

A key invariant is:

> reconstruction is accepted only if the final exact source-object hash matches the signed manifest.

## What requires real hardware

- at least 4–6 real relay nodes with different shard inventories;
- controlled student walking routes or classroom-to-classroom contact windows;
- one destination that cannot retrieve all required information from any single carrier;
- real measurement of contact duration, transfer success, bytes moved and time-to-reconstruction;
- comparison against a non-coded baseline using the same routes and object sizes.

No physical advantage of erasure coding should be claimed before this comparison is measured.

## Messina teaching scenario

Prepare an open-data object such as a map/dataset pack for several coarse areas of the province. Five student nodes start with different coded shards. During an agreed school/home/town route experiment, their devices meet other nodes and exchange only what is useful. A destination at school or another controlled point should reconstruct the exact pack after accumulating any valid `k` shards, even though no individual student carried the full pack.

Use synthetic/open data only; do not infer or publish student home locations from the experiment.

## Privacy / security

Erasure coding is **not encryption**. Depending on the code, individual shards can expose content. Sensitive objects should be encrypted before coding, with keys distributed under a separate authorization policy. Coding manifests must be signed/authenticated, shards hash-verified and poisoning prevented before expensive decoding. Different object versions must not share ambiguous shard namespaces.

Location/contact logs should follow the same privacy rules as UC-008: rotating identifiers, controlled routes and coarse zones where possible.

## Difficulty

**High.** The coding library itself is manageable; the interesting work is exact manifest binding, cache policy, poisoning resistance, comparison against replication and evaluation on real opportunistic contact traces.

## Research signal

Forward erasure correction and network coding remain active research directions for networks with delayed/expensive feedback. Recent 2025–2026 work explores adaptive FEC and network coding under disrupted or variable links. These results motivate the experiment but are not evidence that coding improves PollicinoNet until the same object and contact traces are measured locally.