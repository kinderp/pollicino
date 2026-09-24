# UC-109 — Durability-Aware Replica Retirement and Safe Cache GC

## Idea

Let a cache free space **only after it has enough evidence that retiring one local replica will not accidentally destroy the last useful copies** of an object or shard set.

This is not deletion of the object itself. UC-077 handles authoritative deletion/tombstones. UC-109 handles the opposite question:

> `This content should continue to exist, but may this particular relay safely stop storing its copy?`

## Problem solved

Student relays and small edge nodes have finite storage. Over time they will accumulate:

- course packs;
- map bundles;
- Raiatea artifacts;
- AI models/datasets;
- backup chunks;
- erasure-coded shards;
- experiment evidence;
- cached web/API responses.

Naive LRU eviction can be dangerous in a partitioned network. A node may believe several other replicas exist, while those peers are stale, offline, corrupted or carrying only overlapping erasure shards. Conversely, never deleting anything eventually fills every volunteer cache.

## Actors / nodes

- cache/relay nodes with local storage budgets;
- object publishers or durability-policy owners;
- optional inventory witnesses;
- repair/replication workers;
- requester/destination nodes;
- UC-036 integrity scrubber and UC-091 retrievability auditor;
- UC-095 resource-budget policy.

## Why PollicinoNet fits

PollicinoNet already uses exact content identity, replication and intermittent inventories. UC-109 makes **replica retirement** an explicit protocol decision rather than an accidental side effect of local cache pressure.

- **DISCOVERY:** approximate durability class, `safe-to-retire?`, free-space pressure and candidate object class;
- **EXACT:** object/shard hash, durability-policy ID, inventory epoch, witness set, required minimum independent copies/shards and retirement receipt;
- **SEMANTIC:** labels such as `rebuildable`, `important`, `ephemeral-cache` may influence policy but cannot replace exact object identity.

LoRa carries compact retirement/inventory state. Bulk repair or replacement replicas use richer bearers. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** compact replica/shard availability summaries, durability-policy ID, retirement proposal, approval/deny/unknown and repair-needed notice;
- **BLE:** nearby inventory reconciliation;
- **Wi-Fi/LAN:** actual replica repair, object migration or shard transfer;
- **Internet:** optional authoritative backup/source refresh;
- **physical transport:** a student device/SSD can create a replacement replica before another node evicts its copy.

## What we can test now in software

Create a simulator with exact object identities and finite caches.

Test policies such as:

1. plain LRU;
2. pin/never-evict;
3. `minimum N replicas`;
4. `minimum K independent erasure shards`;
5. age-bounded inventory evidence;
6. retire only after another node confirms a replacement copy;
7. conservative `UNKNOWN -> keep` policy;
8. emergency GC that may violate preferred replication but never lies about durability state.

Inject:

- stale inventory claiming a peer still has a replica;
- two nodes evicting simultaneously;
- a peer with a corrupted copy;
- erasure shards that are duplicates rather than independent;
- a node going offline immediately after promising to retain a copy;
- storage pressure on all relays at once;
- a tombstoned object from UC-077, which must not be preserved merely to satisfy durability;
- policy changes that raise or lower the desired replication level;
- UC-100 demand changes that suggest a hot object should remain nearby.

Useful metrics include accidental loss events, under-replicated time, storage reclaimed, repair bytes, replica diversity, stale-inventory mistakes and objects protected by conservative `UNKNOWN` handling.

A core invariant is:

> local space pressure may justify losing a preferred replica, but the protocol must never report `durability satisfied` from evidence it cannot still justify.

## What requires real hardware

A first physical experiment needs:

- 5–8 boards or small cache hosts;
- several exact test objects plus one erasure-coded object from UC-018;
- deliberately small per-node storage quotas;
- one node temporarily isolated so inventory becomes stale;
- one injected corrupt replica;
- repeated cache-pressure rounds followed by a real restore/reconstruction attempt.

Measure actual retained replicas/shards, successful reconstruction, bytes copied for repair and time spent under-replicated. Energy/storage-wear claims require dedicated instrumentation.

## Messina teaching scenario

Distribute a public course/map pack across student relays in `Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora`. Give every node a deliberately small cache and then introduce a new large public artifact.

A naive policy may evict the same older pack from several nodes because each saw stale evidence that somebody else still had it. The durability-aware policy should instead expose `UNDER-REPLICATED` or `UNKNOWN`, schedule one replacement copy, and only then retire a redundant local replica.

This produces a concrete classroom question:

> How much storage can we reclaim without making content silently unrecoverable?

## Privacy / security

Replica inventories can reveal what content a student probably has.

- exchange the minimum inventory detail required for the policy;
- use compact object IDs or scoped inventory summaries where possible;
- encrypt sensitive objects independently of replication policy;
- authenticate retirement and replacement receipts;
- prevent a malicious node from falsely claiming replicas to induce deletion elsewhere;
- distinguish `present`, `verified`, `recently verified` and `unknown`;
- never treat cache possession as authorization to read content;
- preserve UC-077 deletion/retention rules and UC-076 usage policy.

## Difficulty

**High.** Local eviction is easy; safe retirement under stale, partial and potentially dishonest inventories is the difficult distributed-systems problem.

## Why this is distinct

- **UC-036:** detects and repairs corrupted replicas.
- **UC-040:** decides where replicas should be proactively placed.
- **UC-077:** propagates intentional deletion so old data does not resurrect.
- **UC-091:** audits whether a backup replica appears retrievable.
- **UC-109:** decides when one local cache may **retire a still-valid replica** while preserving a declared durability target.

## Research / implementation signal

IPFS pinning and IPFS Cluster provide a useful reference model: pinned objects are protected from garbage collection, while cluster replication settings can define minimum and maximum replica counts and trigger re-allocation when content becomes under-replicated. PollicinoNet must adapt the idea to intermittent, stale inventories rather than assuming an always-connected cluster.

References:

- https://ipfscluster.io/documentation/guides/pinning/
- https://docs.ipfs.tech/how-to/pin-files/
