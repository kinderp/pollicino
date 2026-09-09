# UC-036 — Proactive Integrity Scrub and Repair Swarm

## Idea

Do not wait for a restore request to discover that a backup replica or shard has silently become corrupt or disappeared.

PollicinoNet nodes periodically exchange compact integrity/inventory state, detect missing or invalid content-addressed objects, and schedule repair from another peer when a richer bearer or physical contact becomes available.

## Problem solved

UC-012 proves that data can be restored after node loss. UC-018 explores encoded fragments. This use case asks a different question:

> Can the network detect **latent damage before the day we actually need the data**?

Storage can fail silently through bit rot, accidental deletion, stale disks, incomplete replicas or malicious/untrusted storage behavior. A backup that has never been checked may only fail when it is urgently needed.

## Actors / nodes

- NAS/server/storage nodes;
- student laptops with selected replicas/caches;
- school storage node;
- student relay/store-and-forward nodes;
- optional erasure-coded UC-018 fragment holders;
- integrity verifier/scrubber process.

## Why PollicinoNet fits

The high-value control messages are tiny compared with the stored data.

- **DISCOVERY:** which content roots/epochs a node claims to store and which repair needs exist;
- **EXACT:** object/chunk/shard hash, manifest version, verification result and repair target;
- **SEMANTIC:** labels such as `class project backup` are for humans only and never replace exact identity.

LoRa can carry `I have / I am missing / verification failed` control state. Actual repair bytes move over Wi-Fi/LAN/BLE, Internet when allowed, or physical carry.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** compact inventory roots, scrub status, repair need/offer and completion acknowledgement;
- **BLE:** nearby small repair or metadata exchange;
- **Wi-Fi/LAN:** normal repair bearer for chunks/shards;
- **Internet:** optional remote repair source;
- **physical transport:** SSD/laptop/student node carries verified repair data between disconnected storage islands.

## What we can test now in software

Build a small content-addressed store with multiple replicas and deliberately damage it.

Test:

- random bit flips in stored chunks;
- complete chunk deletion;
- stale manifest/inventory advertisement;
- node that claims to hold a chunk but cannot serve it;
- repair from one of multiple valid peers;
- repair after delayed/offline contact;
- integration with UC-018 encoded shards;
- exact re-hash after repair;
- idempotent duplicate repair requests;
- race where two peers attempt the same repair;
- repair prioritization under limited bandwidth;
- policy that refuses eviction while durability is below target;
- simulated malicious peer returning wrong bytes;
- periodic scrub scheduling without assuming the network is always connected.

Useful metrics include latent-corruption detection delay, time-to-repair, bytes repaired, unnecessary duplicate repair traffic, verified durability level and number of unrecoverable injected faults.

## What requires real hardware

- at least 3 real storage nodes or laptops;
- one deliberately corrupted/deleted test object on a non-critical dataset;
- a real LoRa repair need/offer exchange;
- a real Wi-Fi/LAN/BLE repair transfer;
- a scenario where the valid repair source is only encountered later by a moving relay;
- measured detection-to-repair time and actual transferred bytes.

Real disks/SSDs can be used only with disposable test data for fault injection.

## Messina teaching scenario

Give three or four student/lab nodes different replicas of a synthetic course archive.

One node silently loses one chunk. It should not wait for a user to open the archive. The next scrub detects the mismatch, advertises a repair need, and later obtains the exact missing chunk from a peer reached through the student network.

A useful second exercise deliberately disconnects the school storage node so the repair has to wait for a student relay/store-and-forward contact.

## Privacy / security

Inventory metadata can reveal what content a node stores.

Therefore:

- advertise compact/authorized inventory information only;
- do not expose private filenames when hashes/opaque roots suffice;
- authenticate repair state when it affects durability decisions;
- verify every repaired object by exact content identity;
- separate storage possession from decryption authority;
- reject rollback/stale manifests where freshness matters;
- never trust a peer because it volunteered a repair.

For encrypted CAS objects, a storage node may repair ciphertext without being able to decrypt it.

## Difficulty

**Medium–High.** Hash verification is simple, but useful proactive repair requires durable inventory, scheduling, concurrency control, privacy-safe discovery and careful interaction with replica/erasure-code policies.

## Research signal

Storage-integrity auditing and repair remain active research areas. A 2026 paper studies hash-based auditing for outsourced storage, while recent distributed-storage work continues to optimize repair locality and bandwidth. These motivate the problem but do not provide PollicinoNet field results.

References:

- https://link.springer.com/article/10.1007/s12083-026-02243-5
- https://doi.org/10.1109/SP61157.2025.00196
- https://www.mdpi.com/2078-2489/16/9/803
