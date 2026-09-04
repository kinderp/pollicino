# UC-012 — Opportunistic Backup and Restore

## Idea

Use PollicinoNet as the control plane for a small **content-addressed P2P backup fabric** that keeps useful replicas across intermittently connected school/home nodes. LoRa does not carry whole backups by default: it advertises compact inventories, missing-object coordinates and urgency, while Wi-Fi/LAN/Internet or physical carry moves bulk chunks.

A Messina-area teaching scenario can model a student notebook, a school cache and one or more home/NAS nodes. If one node disappears, another node should be able to discover which chunks are missing and reconstruct an exact test corpus from the surviving replicas.

## Problem solved

Cloud backup assumes stable Internet and a central provider. Local copies often remain on the same machine or site. For disconnected or rural nodes we want a way to learn *what is missing*, move only the needed chunks when an opportunity appears, and verify exact reconstruction later.

## Actors / nodes

- student notebook or portable node;
- school cache/server;
- optional home PC/NAS;
- student-carried relay/data mule;
- PollicinoStore on participating nodes.

## Why PollicinoNet fits

The core already models content-addressed chunks, manifests, provider hints, exact verification, store-and-forward and richer-link handover. Backup therefore becomes an application of the existing `DISCOVERY` + `EXACT` primitives rather than a new radio protocol. The frozen LoRa PHY remains untouched.

## Possible bearers

- **LoRa:** compact inventory summary, missing-chunk coordinate, priority/expiry, provider hint;
- **BLE:** nearby reconciliation for small state;
- **Wi-Fi/LAN/Internet:** encrypted chunk transfer and restore;
- **physical transport:** a student-carried cache or removable storage can ferry encrypted chunks between disconnected sites.

## What we can test now in software

- deterministic content-addressed test corpus;
- chunk inventories on 3–10 synthetic nodes;
- replication policies such as `keep 2 copies` or `keep one off-site copy`;
- simulated node loss followed by exact restore;
- partial restore of only one requested object;
- queueing and prioritization when a contact window is short;
- deduplication and resumable transfers;
- metrics: restore success, bytes moved, duplicate bytes avoided, time-to-durable-replica and unavailable-object rate.

## What requires real hardware

- 3+ nodes with deliberately partitioned storage;
- physically disconnect one node and perform a real restore from surviving peers;
- measure chunk transfer/retry behavior over chosen bearers;
- test a walking data-mule pass that carries encrypted backup state to another site;
- later, measure how much LoRa control traffic is actually needed for inventory reconciliation.

No durability or disaster-recovery claim is valid until restore tests succeed repeatedly on real storage.

## Privacy / security

Backups may contain the most sensitive data in the system. Encrypt payloads end-to-end before replication, authenticate manifests, separate content identity from authorization, and minimize public inventory leakage. Content-addressed deduplication can reveal that two nodes possess the same object, so provider hints and inventory summaries need privacy controls. Recovery keys must not live only on the nodes being backed up.

## Difficulty

**Medium–High.** Exact chunking/restore is manageable; secure key recovery, private inventory exchange and robust durability policy require careful design.
