# UC-077 — Deletion Tombstone and Retention-Expiry Ferry

## Idea

Treat **deletion intent as data that must itself propagate** through a disconnected replicated system.

If an object is copied to several PollicinoNet caches and one node later decides that the object must no longer be served or retained, simply deleting the local file is not enough. An offline replica may return days later and accidentally reintroduce the old object.

UC-077 carries a compact signed tombstone/retention-expiry state so cooperating caches can converge on "this exact old version is no longer live" before safely garbage-collecting deletion evidence.

## Problem solved

Store-carry-forward and opportunistic caching create a difficult lifecycle problem:

1. object `O:v3` is replicated to nodes A, B and C;
2. C goes offline;
3. A and B receive a valid deletion/expiry decision and erase their visible copy;
4. later C returns with the old bytes;
5. if A and B forgot the deletion state, C may look like the only node that still has valid content and the object can be resurrected.

The same issue appears with expired messages, withdrawn course material, stale model versions, deleted Raiatea documents, revoked cached artifacts and privacy-limited datasets.

This use case does **not** promise magical erasure from malicious devices or irreversible derivatives. It studies deletion convergence among cooperating PollicinoNet nodes under long partitions.

## Actors / nodes

- artifact owner/publisher or authorized deletion issuer;
- student relay/store-and-forward nodes;
- opportunistic content caches;
- Raiatea/document stores;
- backup/content-distribution nodes;
- optional UC-056 consent-state issuer;
- optional UC-019 trust/revocation and UC-020 freshness sources;
- optional audit collector at school.

## Why PollicinoNet fits

A deletion marker is tiny compared with the object it suppresses.

- **DISCOVERY:** `tombstone/update available`, stale-replica hint, retention epoch summary;
- **EXACT:** exact object/content hash, deleted version/range, tombstone ID/version, issuer, reason class, effective epoch, retention/grace policy and acknowledgement state;
- **SEMANTIC:** labels such as `expired`, `withdrawn`, `superseded`, used for explanation but not as the authoritative deletion identity.

LoRa can propagate the compact tombstone and acknowledgements. Richer bearers can reconcile full manifests or securely purge larger object stores later.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** tombstone digest, object hash/version, deletion epoch, acknowledgement and stale-replica warning;
- **BLE:** nearby cache reconciliation;
- **Wi-Fi/LAN:** full manifest repair, audit state and bulk cache cleanup;
- **Internet:** optional authoritative lifecycle/policy synchronization;
- **physical transport:** an offline cache or relay physically returns carrying either the stale object or the newer tombstone state.

## What we can test now in software

Create a deterministic replicated-object simulator with 3–10 nodes and long partitions.

Test:

- delete while one replica is offline;
- stale replica returns before receiving the tombstone;
- stale replica returns after other nodes garbage-collected deletion evidence too early;
- duplicate and reordered tombstones;
- tombstone arrives before the object itself;
- object is recreated legitimately as a newer exact version;
- conflicting delete/recreate operations;
- unauthorized deletion issuer;
- deletion of one version versus all versions in a namespace;
- expiry-based tombstone versus explicit withdrawal;
- node reinstallation that loses local tombstone state;
- acknowledgement tracking and safe-compaction criteria;
- encrypted object where crypto-shredding/key destruction is part of the local cleanup strategy;
- integration with UC-036 integrity scrub so deleted objects are not mistakenly "repaired" back into existence.

Useful metrics include:

- deletion convergence delay;
- stale-serving window;
- zombie-resurrection count;
- tombstone bytes/storage overhead;
- number of replicas whose deletion state is known/unknown;
- time until garbage collection is considered safe under the chosen experiment policy.

Key invariant:

> absence is not proof of deletion. A disconnected replica must learn a newer deletion fact before its old copy can be safely treated as obsolete.

## What requires real hardware

- 4–6 PollicinoNet nodes with small test caches;
- replicate a harmless public file to all nodes;
- isolate one node physically;
- issue a signed deletion/expiry while that node is absent;
- reconnect it through a student relay and verify that it does not resurrect the old object;
- repeat with deliberately premature tombstone garbage collection as a negative test;
- measure real convergence/contact time and control bytes.

Use only disposable public/synthetic content. The test demonstrates protocol behavior, not certified secure erasure of storage media.

## Messina teaching scenario

A small course-pack object is replicated to caches representing `Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora`. The Spadafora cache is deliberately disconnected. The teacher publishes a signed `superseded` tombstone for version 1 and then publishes version 2.

Student relay nodes carry the lifecycle state. When the stale cache returns, it must not advertise version 1 as live merely because it still has the bytes. It first learns that v1 is tombstoned, then may fetch or advertise v2.

A second exercise intentionally deletes the tombstone too early on the online nodes and demonstrates, in software first, how a stale replica can make the old object appear again. This makes the anti-resurrection requirement visible to students.

## Privacy / security

Deletion metadata can reveal that a sensitive object existed, so even tombstone identifiers may require protection.

- use opaque content IDs/hashes rather than human-readable private titles;
- authenticate and authorize deletion issuers;
- bind tombstones to exact object/version scope;
- protect acknowledgements from forgery;
- do not claim remote secure erase on untrusted/malicious devices;
- distinguish `not served`, `logically deleted`, `local bytes purged` and `cryptographic key destroyed` as separate states;
- retain deletion evidence only as long as necessary for the protocol/policy being tested;
- ensure backups and UC-036 repair logic understand tombstones so they do not restore deleted content automatically.

## Difficulty

**Medium–High.** The tombstone object is simple; the hard parts are long-offline replicas, safe garbage collection, recreate semantics and preventing repair/backup mechanisms from undoing deletion.

## Relationship to existing use cases

- **UC-012 / UC-036:** preserve and repair wanted replicas; UC-077 provides the opposite signal—this exact old replica must *not* be restored.
- **UC-056:** a consent withdrawal can trigger future-use restrictions; UC-077 generalizes delayed deletion/expiry to arbitrary cached objects.
- **UC-004 / UC-006 / UC-024:** all create replicated artifacts that eventually need lifecycle/retention semantics.

## Research / systems signal

Distributed databases commonly model deletion as a replicated tombstone because removing a local value is ambiguous when another replica was offline. Apache Cassandra documentation explicitly describes deletion as writing a time-stamped tombstone that later expires during compaction. The underlying anti-resurrection problem is directly relevant to a delay-tolerant cache where nodes may be absent for long periods.

References:

- https://cassandra.apache.org/doc/stable/cassandra/managing/operating/compaction/tombstones.html
- https://ieeexplore.ieee.org/document/8069082/
