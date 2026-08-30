# UC-COURIER-001 — Physical object custody and handoff

Status: PROTOTYPE / EDUCATIONAL FIELD CANDIDATE

## Problem

Sometimes the object that must move is physical, not digital: a sensor kit, environmental sample container, robot part, sealed envelope, library item or lab device. Connectivity can be intermittent while the item passes through several supervised hands.

PollicinoNet can carry a compact **digital handoff record** alongside the physical item:

- opaque item ID / QR-derived coordinate;
- current custody generation;
- handoff receipt;
- expected destination or role;
- deadline / return-by time;
- optional condition summary from an attached sensor;
- hash/reference to richer documentation stored elsewhere.

The network must not claim that a digital receipt proves a physical event unless the handoff procedure actually ties them together.

## Actors / nodes

- teacher/lab custodian or supervised source;
- physical item with QR/NFC/printed opaque ID;
- student/group carrying the item during an approved activity;
- receiving lab/classroom/checkpoint;
- Pollicino nodes carrying receipts and pending handoff state;
- optional asset catalog / evidence manifest / sensor service.

## Messina educational scenario

A supervised environmental-science activity has three identical sampling kits. One kit is assigned to a pseudonymous team associated with a Rometta-like logical cluster and must return to the school lab the next morning. A second kit changes hands at a supervised school/field checkpoint.

At each handoff, the parties scan the kit's opaque ID (QR/NFC/BLE can be used locally) and produce a small signed or test-signed receipt. If Internet is unavailable, the receipt is carried over LoRa/store-and-forward and reconciled later at school.

A variant can use a robot sensor module or classroom electronics kit instead of an environmental sample.

Public place names are scenario labels; no inter-town LoRa coverage is assumed.

## Why PollicinoNet fits

The problem naturally combines:

- delayed receipt delivery;
- persistent custody state;
- exact identity of small records;
- store-carry-forward;
- duplicate suppression;
- deadlines/returns;
- optional rich-document references;
- physical mobility that already exists for the item itself.

The transport can therefore remain ordinary PollicinoNet while the application layer defines physical handoff semantics.

## Possible bearers

- QR/NFC/BLE for immediate local item-to-person/checkpoint association;
- LoRa for compact handoff receipts and status;
- Wi-Fi/LAN at school/home for catalog reconciliation or rich documentation;
- Internet only for optional backend synchronization;
- physical carry is the primary movement of the actual item.

No LoRa PHY change is required.

## What can be tested now in software

1. synthetic items with opaque IDs;
2. `ISSUED -> IN_CUSTODY -> HANDED_OFF -> RETURNED` state machine;
3. duplicate handoff receipt;
4. out-of-order receipts arriving after a later generation;
5. missed/expired return deadline;
6. item and receipt taking different network paths;
7. conflicting handoff claims;
8. offline checkpoint followed by next-morning convergence;
9. integration with `UC-ASSET-001` availability only after a valid return receipt;
10. integration with `UC-EVIDENCE-001` when rich photos/logs accompany an item;
11. finite storage and receipt retention;
12. compare simple monotonic generation rules with more complex conflict handling only if needed.

Use fake items/IDs first. No physical-person inference is necessary for the software model.

## Minimal measurable hypotheses

- H1: monotonic custody generations plus idempotent receipts converge correctly despite delayed/out-of-order delivery.
- H2: compact handoff state can travel through the student DTN while the physical item follows an independently supervised path.
- H3: separating asset availability from custody transition prevents stale catalogs from marking an in-transit item as available.

## Metrics

- correct final custody state;
- stale/out-of-order receipts rejected;
- duplicate receipts suppressed;
- return-before-deadline ratio;
- receipt delivery delay;
- bytes per handoff;
- number of physical/digital path divergences resolved;
- catalog consistency after return;
- unresolved conflict count.

## What requires real hardware

After HW-006, a supervised physical pilot can measure:

- actual scan/handoff usability;
- whether LoRa delivery of receipts adds value beyond next Wi-Fi sync;
- restart/battery behavior during a school day;
- real time between handoff and receipt convergence;
- BLE/NFC/QR ergonomics if those local bearers are added;
- sensor-condition attachment only after separate hardware validation.

No real student tracking or unsupervised courier experiment is required.

## Privacy / security

A custody system can easily become a person-tracking system if designed poorly.

Requirements:

- item-centric records, not person-location logs;
- pseudonymous role/team IDs for first pilots;
- no exact home address/GPS;
- retain only the minimum handoff metadata;
- explicit signatures/test signatures for authoritative handoffs;
- anti-replay / monotonic generation;
- access control for sensitive item metadata;
- do not infer that possession of a relay node proves possession of the physical item;
- supervised procedure is required for any claim about physical custody.

For environmental samples or other regulated workflows, this prototype is not a certified chain-of-custody system.

## Implementation difficulty

**Medium.** The state machine is simple and produces a very tangible demonstration; reliable identity binding, signatures and real-world procedure require more care.

## Relationship to existing use cases

- Not `UC-ASSET-001`: ASSET is a catalog/reservation problem for stationary or borrowable resources; COURIER follows the actual physical handoff/return lifecycle.
- Not `UC-EVIDENCE-001`: EVIDENCE binds digital rich-media integrity/provenance; COURIER tracks a physical item's custody state.
- Not `UC-MOBILITY-001`: MOBILITY studies carriers as network relays; COURIER's primary entity is a physical item whose handoffs generate application state.

## Success / kill criterion

**Continue** if a software fixture and later supervised kit pilot show that delayed receipts resolve real offline handoff/catalog ambiguity with small overhead.

**Keep it inside ASSET** if no workload needs physical custody generations beyond ordinary borrow/return status.

## Gate decision

**PROTOTYPE / CONTINUE.** Suitable for a visible educational pilot after HW-006 because it can use harmless school/lab items and synthetic identities while exercising real store-carry-forward semantics.
