# UC-FIND-001 — Privacy-preserving lost-object finding ferry

Status: PROTOTYPE / privacy-sensitive educational field candidate

## Problem

A school or laboratory object can disappear from the place where it is expected even though it still carries a very small BLE beacon or other short-range identifier. The owner may never directly encounter the object again, but many student-carried Pollicino nodes may pass near it during an ordinary day.

The useful question is not continuous tracking. It is:

> can an owner publish a bounded search request, have unrelated carriers opportunistically detect the missing beacon, and receive a privacy-minimized delayed sighting without exposing student trajectories?

This is distinct from `UC-ASSET-001`, which manages known inventory/reservations, and `UC-COURIER-001`, which reconciles expected handoffs. FIND begins when the object's current location is unknown and uses opportunistic detection.

## Actors / nodes

- a tagged school/lab object used only for an authorized pilot;
- owner or school lost-and-found authority;
- student-carried Pollicino nodes acting as passive finders/relays;
- school/home gateway that can resolve an opaque sighting report;
- optional BLE-capable companion device;
- experiment recorder using synthetic or rotating identifiers.

The first pilot should use deliberately placed laboratory objects, not personal possessions.

## Why PollicinoNet fits

The workload naturally separates into two scarce pieces:

1. a small **WANT/search token** describing an authorized missing beacon;
2. a small **sighting report** that can be stored, carried and returned asynchronously.

PollicinoNet already provides bounded object identity, store-carry-forward, expiry, duplicate suppression, exact reconstruction and multi-bearer lifecycle state. The rich location/context detail, if any, can remain off-LoRa and be resolved only at a trusted endpoint.

A sighting is useful even if the detecting node never has Internet and never directly meets the owner.

## Possible bearers

- BLE: short-range tag discovery and optional local proof-of-presence;
- LoRa: bounded search tokens and privacy-minimized sighting reports between Pollicino nodes;
- Wi-Fi/LAN/Internet: owner-side resolution, authorization and richer context retrieval;
- physical carry: student mobility moves search state and sightings between disconnected clusters.

## What we can test immediately in software

Use synthetic tags, pseudonymous carrier IDs and an explicit temporal contact trace. Compare:

```text
broadcast every active search request
subscription/WANT-scoped search requests
single sighting report
bounded replicated sighting report
```

Inject:

- beacon rotations;
- false detections;
- duplicate sightings;
- replayed old sightings;
- search expiry;
- multiple concurrent lost objects;
- carriers that never return to the school hub.

Track:

- time to first useful sighting;
- LoRa bytes per recovered object;
- duplicate reports;
- stale/replayed reports rejected;
- number of carriers exposed to each search token;
- amount of location/context information disclosed.

The simplest useful baseline is one authorized search token plus one opaque sighting token. Do not invent probabilistic crowd-location algorithms unless this baseline fails.

## Messina student-network scenario

A tagged test object is deliberately left at one supervised school/lab checkpoint. Students later disperse into logical `Rometta-like`, `Spadafora-like`, `Saponara-like` and `Villafranca-like` clusters. A finder node that encounters the beacon stores a compact sighting and physically carries it until it can reach another Pollicino node or the school/home rich-link gateway.

Town names are only scenario labels. The experiment does not infer or publish student home locations and does not assume LoRa coverage between towns.

## What requires real hardware

After the general HW-006 gate, a separate FIND pilot is required to measure:

- BLE discovery reliability and scan duty cycle;
- BLE/LoRa coexistence on the actual node/companion configuration;
- tag battery life;
- real detection latency during ordinary supervised movement;
- energy cost of background scanning;
- effect of rotating identifiers on discovery;
- end-to-end delayed return of a sighting.

No physical detection range is claimed from software simulation.

## Privacy and security

This use case is privacy-sensitive by construction.

Required principles:

- use rotating or experiment-scoped beacon identifiers;
- do not broadcast a stable student or owner identity;
- do not require continuous GPS;
- prefer coarse checkpoint IDs or owner-only encrypted context over precise coordinates;
- bound retention of raw sightings;
- authenticate search authorization so arbitrary parties cannot request tracking;
- protect against replay and forged sightings;
- make finder participation explicit in any real pilot;
- never use student devices to track people.

Research on crowd-sourced Bluetooth finding systems shows both feasibility and significant privacy risk; privacy is therefore a first-order acceptance criterion, not an add-on.

## Difficulty

**Medium technically; high privacy/governance sensitivity.**

## Success / kill criteria

Continue if a privacy-minimized scheme returns useful authorized sightings with substantially less exposure than a naive stable-ID/location log and with bounded LoRa/storage cost.

Defer or reject a field pilot if useful recovery requires stable personal identifiers, continuous location history, opaque background participation or unbounded scanning energy.

## Related-work note

Relevant prior art includes SecureFind (IEEE TWC 2016, DOI `10.1109/TWC.2015.2495291`) and published analyses of crowd-sourced Bluetooth offline-finding systems. These establish the problem class and privacy risks; they are not evidence that PollicinoNet itself is secure or effective.

## Physical evidence boundary

The frozen Pollicino LoRa PHY is unchanged. No BLE or LoRa range, reliability, energy or provincial coverage claim is authorized before measured hardware evidence.