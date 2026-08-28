# UC-ASSET-001 — Offline physical-asset catalog and reservation ferry

Status: PROTOTYPE / EDUCATIONAL INTEGRATION

## Problem

Schools, labs, libraries and community spaces often manage physical resources that are useful but not continuously connected: robotics kits, sensors, books, test equipment, adapters, tools, 3D-printing consumables or loan devices.

A student or teacher may only need to know a small amount of state: asset ID, type, availability generation, current site/coarse custodian, reservation lease, return deadline and where the item can be collected. The physical item itself moves later; the network only needs to reconcile compact catalog and reservation state.

This differs from `UC-CONTENT-*` and `UC-RAIATEA-001`: the primary object being discovered/reserved is physical, and the hard problem is eventual-consistency/conflict handling rather than rich-content retrieval.

## Actors / nodes

- school/lab/library inventory authority;
- asset shelf/station gateway;
- teacher/student client node;
- student-carried relay;
- optional QR/NFC/BLE asset tag;
- optional central inventory service when Internet is available.

## Messina educational scenario

A school hub owns a pool of robotics kits and sensors. A second lab or territorial club has a different pool. Students relay signed availability snapshots and reservation requests between clusters during normal movement.

```text
lab A catalog ----> student relay ----+
                                       +--> school hub / inventory authority
lab B catalog ----> student relay ----+

request/lease acknowledgement travels back later
physical kit is collected separately
```

No home inventory or named student location should be exposed over the shared network.

## Why PollicinoNet fits

The workload is compact and strongly state-oriented:

- inventory versions/generations;
- set reconciliation;
- stale state detection;
- bounded reservation leases;
- acknowledgements that may return later;
- duplicate requests;
- conflicting reservations across partitions;
- physical movement already exists independently of network delivery.

Pollicino can carry small availability/reservation objects over scarce links and defer any rich catalog media/manuals to Wi-Fi or Internet.

## Possible bearers

- LoRa for compact inventory/reservation state;
- BLE/NFC/QR for local asset identification;
- Wi-Fi/LAN for full catalog, manuals and administrative actions;
- Internet for optional central synchronization;
- physical movement for the item itself and for mobile relays.

## What can be tested now in software

Without hardware we can model:

1. 100–1,000 synthetic assets divided across sites;
2. inventory generation changes;
3. two partitions receiving competing reservation requests;
4. lease expiration and reissue;
5. duplicate request suppression;
6. full-catalog sync versus changed-ID reconciliation;
7. stale availability served by a relay;
8. delayed acknowledgement/return state;
9. priority classes for high-demand assets.

The first design should prefer simple authoritative leases over a complex multi-writer CRDT unless a real use case proves that multi-authority writes are required.

## What requires real hardware

Hardware is required before claiming:

- practical scan/tag reliability;
- real inventory update latency between rooms/sites;
- contact capacity with students carrying nodes;
- battery life for optional active tags;
- usable BLE/NFC/QR integration;
- real-world conflict/return workflow usability.

HW-006 remains the first LoRa evidence gate. Asset-tag experiments are a later, separate campaign.

## Privacy / security

Requirements:

- public/shared network sees asset state, not borrower identity;
- borrower/reservation details encrypted end-to-end to the authority where needed;
- signed authority for availability and lease grants;
- monotonic generation or explicit version conflict rules;
- no home address or student movement history;
- short retention of reservation metadata;
- do not use the experimental network as the sole source of truth for expensive or safety-critical equipment.

## Implementation difficulty

**Medium.** The transport and reconciliation pieces already exist conceptually. New work is mainly the physical-asset schema, lease/conflict semantics and local identification interface.

## Minimal measurable hypotheses

- H1: changed-ID/set reconciliation is materially cheaper than repeatedly broadcasting the complete inventory.
- H2: bounded authoritative leases avoid most double-booking under partitions without requiring continuous connectivity.
- H3: student relays can return useful availability and reservation acknowledgements despite missed direct contacts.

## Metrics

- catalog convergence time;
- bytes per useful inventory change;
- stale availability served;
- conflicting reservation attempts;
- lease success/expiry rate;
- duplicate suppression;
- acknowledgement latency;
- per-bearer TRC.

## Gate decision

**PROTOTYPE.** This is a concrete school-facing application with clear eventual-consistency semantics and little need to move large payloads over LoRa.
