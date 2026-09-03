# UC-001 — Student Knowledge Ferry

## Idea

Use student-carried PollicinoNet nodes as **delay-tolerant data mules** between school, home and nearby towns. LoRa carries compact discovery/request coordinates; larger payloads move later over BLE, Wi-Fi, Internet, LAN/NAS or by physical carry.

A concrete Messina-area experiment can model students moving among school and homes in places such as Rometta, Venetico, Spadafora and Villafranca Tirrena. The goal is not continuous coverage: it is to exploit normal human mobility as store-and-forward connectivity.

## Problem solved

Some nodes may be offline for hours, lack Internet, or have only a scarce radio link. A student can carry requests, manifests and cached chunks from one disconnected island to another and synchronize when a richer link becomes available.

## Actors / nodes

- student-carried LoRa boards;
- school gateway/server;
- optional home node, PC or NAS;
- optional peer students acting as relays;
- PollicinoStore caches at each participating node.

## Why PollicinoNet fits

PollicinoNet already separates `DISCOVERY` from `EXACT` payload transfer and supports store-and-forward, TTL, duplicate suppression and richer-link handover. A tiny LoRa exchange can say *what is wanted or available* without pushing the whole object over LoRa.

## Possible bearers

- **LoRa:** rendezvous, wanted/offered coordinates, compact inventory, priority/expiry;
- **BLE:** nearby handshake and small exchanges;
- **Wi-Fi/LAN/Internet:** manifests and bulk chunks;
- **physical transport:** the student literally carries cached state between disconnected places.

No PHY change is required or proposed.

## What we can test now in software

- synthetic mobility/contact traces for school/home/town encounters;
- store-and-forward queues with TTL and hop limits;
- request propagation and duplicate suppression;
- content-addressed chunk inventory and partial reconstruction;
- opportunistic rich-link handover;
- metrics: TRC, cache hit ratio, delivery delay, duplicate overhead, successful reconstruction rate.

All initial traces should be synthetic; no student location data are needed.

## What requires real hardware

- 2–6 real LoRa boards carried through controlled routes;
- measured contact success, RSSI/SNR, packet loss and delivery delay;
- verification that a later Wi-Fi/BLE handover actually resumes the intended object transfer.

No physical performance claim is valid until these measurements exist.

## Privacy / security

Use rotating/scoped node identifiers. Do not encode student identity, home address, precise routine or stable location in public LoRa frames. Start with public teaching material only. Private content needs authorization, encryption and metadata-minimizing coordinates.

## Difficulty

**Medium.** Most logic is simulator/store/resolver work; the interesting difficulty is opportunistic routing and privacy-safe mobility, not the radio PHY.
