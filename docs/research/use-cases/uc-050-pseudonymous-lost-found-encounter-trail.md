# UC-050 — Pseudonymous Lost-and-Found Encounter Trail

## Idea

Use PollicinoNet and DNATrace-like encounter ideas to help recover a **lost tagged object without continuously tracking the people who carried or observed it**.

A tagged school object emits or exposes a rotating pseudonymous identifier. Nearby student nodes can record a compact local encounter. If the owner later marks the object as lost, a privacy-limited query can move through the network and matching sightings can return through store-and-forward relays.

The first experiment should use harmless school-owned objects and synthetic owners.

## Problem solved

Ordinary lost-and-found systems depend on somebody manually reporting an item to one central place. Continuous GPS/cellular trackers solve a different problem but require infrastructure, battery and often create a detailed location history.

PollicinoNet can explore a middle ground:

```text
I lost object X.
Has any participating node encountered X recently?
If yes, can I learn only the minimum coarse information needed to recover it?
```

The observer need not have Internet at encounter time, and the object's full route need not be reconstructed.

## Actors / nodes

- tagged object, initially a school-owned book, kit, calculator case or equipment box;
- owner/requester node using a synthetic test identity;
- student witness nodes that may encounter the tag;
- student relay/store-and-forward nodes;
- optional school lost-and-found node;
- optional UC-042 custody system when the item was deliberately handed over rather than simply observed.

## Why PollicinoNet fits

The problem is naturally encounter-based and delay tolerant.

- **DISCOVERY:** a compact lost-item need or opaque tag epoch token;
- **EXACT:** exact item identity known only to authorized recovery logic, encounter token, time window and signed/hashed sighting record;
- **SEMANTIC:** coarse labels such as `school`, `lab`, `checkpoint-B`, never a substitute for exact identity or proof.

BLE is well suited to short-range tag encounters. LoRa can ferry compact lost-item queries, match notices and coarse sighting results across groups. Wi-Fi can carry images or richer evidence only after a match.

Student mobility becomes useful infrastructure without requiring a live end-to-end path.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **BLE:** short-range detection of a rotating tag identifier;
- **LoRa:** lost-item query token, compact match notice, coarse zone/checkpoint and freshness metadata;
- **Wi-Fi/LAN:** optional photo, detailed description or exact recovery instructions;
- **Internet:** optional synchronization with a school lost-and-found service;
- **physical transport:** witnesses/relays carry unresolved encounter logs until they meet a query or gateway.

## What we can test now in software

- generate rotating pseudonymous tag IDs derived from an exact synthetic asset identity;
- simulate encounters between one item and many witness nodes;
- publish a lost-item query only after the simulated loss;
- match historical encounter tokens without exposing every unrelated encounter;
- test false positive, duplicated, delayed and reordered sightings;
- expire old encounters and queries;
- reveal only coarse checkpoint/time-bucket information after an authorized match;
- compare central full-history storage against query-triggered disclosure;
- test an attacker replaying an old tag ID;
- test a malicious node submitting a fabricated sighting;
- integrate UC-011 consent/rendezvous ideas, UC-020 freshness and UC-042 if the item transitions into explicit custody;
- measure query-to-first-match delay, useful-sighting rate, storage overhead and privacy leakage.

A useful invariant is:

> finding one lost object must not require building a continuous movement history of every student or every tagged object.

## What requires real hardware

- 4–6 participating nodes;
- one harmless BLE-capable tag or second board acting as a tag;
- controlled movement of the object through predeclared school checkpoints;
- delayed publication of the lost-item query;
- real LoRa ferrying of match/query metadata;
- replay and stale-sighting tests;
- explicit measurement of encounter detection and recovery-message delay.

No range or recovery-rate claim should be made until those measurements exist.

## Messina teaching scenario

Tag a school-owned electronics kit and move it through a controlled sequence of checkpoints representing `school`, `Venetico`, `Rometta` and `Spadafora`. Student nodes only record rotating encounter tokens plus coarse checkpoint/time bucket.

After the item has stopped moving, declare it “lost”. The owner node injects a recovery query. Student relays carry the query through the network until one or more stored encounters match. The response should reveal something like:

```text
seen recently at checkpoint C
freshness: 2 epochs old
```

not a complete trajectory or the identities of every observer.

The exercise can compare `central track everything` with `privacy-limited encounter trail` and quantify what information each design exposes.

## Privacy / security

This use case can easily become surveillance if designed badly.

- participation must be opt-in for teaching tests;
- use school-owned items and synthetic owners first;
- rotate public tag identifiers;
- avoid stable student identifiers in encounter logs;
- use coarse checkpoints/time buckets;
- retain encounter data briefly;
- do not reveal a witness identity to the requester unless the experiment explicitly requires and authorizes it;
- require proof that the requester is authorized to resolve the exact asset identity;
- reject stale/replayed tokens where possible;
- do not use the prototype to track people, vehicles or covertly tagged possessions.

## Difficulty

**Medium.** The basic encounter/query mechanism is simple; privacy-preserving identifier rotation, authorized resolution and false-sighting resistance are the interesting parts.

## Research / industry signal

Modern asset-tracking systems increasingly use crowds of nearby BLE-capable devices as opportunistic readers rather than installing a fixed reader everywhere. Commercial systems such as Nodle ConnectX describe BLE-tag sightings collected by existing mobile devices, while other tracking systems combine BLE, UWB and LoRa. PollicinoNet's research question is narrower: can we reproduce a privacy-limited, delay-tolerant version with student relays and without adopting continuous commercial tracking semantics?

References:

- https://www.nodle.com/nodle-connectx
- https://www.continum.ai/
