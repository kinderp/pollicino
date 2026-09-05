# UC-015 — Partition-Tolerant Resource Ledger

## Idea

Maintain a small shared ledger of **resources, requests and reservations** even when groups are temporarily disconnected. In a civil-protection drill, for example, different school or field nodes can hold synthetic counts of water packs, batteries, radios, first-aid kits, blankets or available transport. Each node continues to record local changes while offline; later contacts exchange compact operations and converge toward the same state.

The same mechanism can be tested first with ordinary school-lab inventory, avoiding any claim that the system is ready for real emergency operations.

## Problem solved

A central inventory server is fragile when connectivity disappears. During a partition, people still need to record that an item was added, consumed, requested, reserved or moved. When the network reconnects, those independent changes must reconcile predictably instead of silently overwriting each other.

## Actors / nodes

- school or command node holding the complete ledger;
- student relay/store-and-forward nodes;
- simulated field posts or assembly points;
- optional mobile vehicle/person acting as data mule;
- authorized operators producing signed ledger operations.

## Why PollicinoNet fits

Ledger operations are small, ordered only partially, and can tolerate delay better than a continuous database connection. PollicinoNet can carry compact operation IDs, version vectors or summaries over LoRa, suppress duplicates, store operations while disconnected and use richer bearers for larger audit snapshots. `EXACT` is appropriate for authoritative operation records and ledger snapshots; no semantic reconstruction is allowed for quantities or authorization data.

This is an application-layer replicated-data experiment. It does **not** modify the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact inventory deltas, request IDs, acknowledgements, version summaries and priority flags;
- **BLE/Wi-Fi/LAN:** reconciliation of larger operation sets or snapshots;
- **Internet:** eventual synchronization with a school/server dashboard;
- **physical transport:** a relay carries an operation backlog between disconnected groups.

## What we can test now in software

- implement a synthetic resource ledger with operation IDs and signed actors;
- partition 3–10 virtual nodes, apply concurrent add/remove/request/reserve operations, then reconnect them;
- test duplicate, delayed and reordered operations;
- compare simple append-only logs with CRDT-style counters/sets where the semantics are safe;
- assert deterministic convergence for the supported operation types;
- test stale reservations, expiry and explicit conflict states instead of hiding ambiguity;
- prioritize urgent synthetic requests while preserving the exact audit trail;
- measure convergence delay, scarce-link bytes, duplicate suppression and unresolved-conflict count.

A useful invariant is: after all valid operations have propagated, every fully synchronized node must compute the same ledger state from the same exact operation set.

## What requires real hardware

- 3–5 boards divided into two intentionally disconnected groups;
- real store-and-forward exchange of a small operation backlog through a moving relay;
- measured convergence time and packet delivery for the radio segment;
- one richer-link reconciliation test for a larger snapshot or audit log.

Any civil-protection scenario must remain a **drill with synthetic resources** until independently validated with the appropriate authorities and procedures.

## Privacy / security

Use synthetic inventory first. Do not place names, medical status, home addresses or identifiable evacuee information in the LoRa payload. Operations must be authenticated and role-scoped. Deletions and corrections require an auditable strategy; silent last-write-wins behavior is not acceptable for safety-relevant quantities. Encryption may be required when even resource location is sensitive.

## Difficulty

**Medium.** The payloads are small and excellent for LoRa experiments; the main challenge is defining reconciliation semantics that are understandable, deterministic and auditable.

## Research signal

Recent work on distributed emergency-management systems has explicitly explored offline replication with operation-based CRDTs under mobile and weakly connected conditions. That makes this a useful research direction to reproduce at small teaching scale, while keeping PollicinoNet results separate from external systems and from real emergency certification.
