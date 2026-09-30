# UC-142 — Place-Bound Checkpoint Mailbox / Stored-Geocast Courier

## Idea

Address a bounded message or content drop to a public checkpoint or coarse service area, not to one person or one specific moving node.

A relay carries the object until it encounters an authenticated fixed checkpoint service. The checkpoint stores it locally for a defined lifetime and eligible nearby users can retrieve it later.

## Problem solved

Some offline tasks are location-bound: deliver a school content pack to a laboratory regardless of which gateway is online, leave a public field instruction at a checkpoint, collect sensor data at a rural service point, deposit a synthetic civil-protection exercise bulletin at a staging area, or leave a maintenance package for whoever reaches a site later.

## Actors / nodes

Publisher/sender, student relay/store-and-forward nodes, authenticated fixed checkpoint service(s), local reader/requester, optional mobility planner and experiment observer.

## Why PollicinoNet fits

Store-carry-forward naturally allows an object to wait for the first relay that reaches the intended checkpoint. A place-bound envelope can contain checkpoint/zone ID, object hash, validity interval, maximum replication count, delivery policy, checkpoint public key/trust anchor and deposit receipt state.

No continuous route disclosure is required. The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: checkpoint ID, compact destination hint, availability beacon and deposit status.
- BLE: nearby checkpoint handshake and small object deposit.
- Wi-Fi/LAN: bulk object delivery at the checkpoint.
- Internet: optional backhaul once the checkpoint reconnects.
- Physical transport: human/vehicle/data mule carries the object into the target area.

## What we can test now in software

Simulate 2–4 checkpoint services and mobile relays. Test first-match delivery, equivalent checkpoints, offline checkpoint, expiry before arrival, fake checkpoint with the same human-readable name, wrong-checkpoint visits, duplicate deposits, key rotation, withdrawal while a relay still carries the object and a reader arriving before Internet returns.

Compare person-specific endpoint delivery, fixed checkpoint ID, a group of equivalent checkpoint IDs and a coarse area label resolved to authenticated checkpoint services.

## What requires real hardware

Use 6–10 boards, with 2–3 fixed boards/laptops acting as authenticated public checkpoints and several student-carried relay nodes. Use only school/public test locations and harmless public objects. Measure actual contact/deposit events and do not claim geographic coverage beyond measured checkpoints.

## Messina teaching scenario

Create experiment checkpoints at school/lab locations in Messina, Villafranca, Rometta/Venetico and optionally Spadafora. A message can be addressed to checkpoint:Rometta-Lab rather than to a named student. Any relay may deposit it when it encounters that authenticated checkpoint, and another student can retrieve it later over local Wi-Fi/BLE even if Internet is absent.

## Privacy / security

Use public/coarse checkpoint IDs rather than homes, avoid continuous GPS traces, authenticate checkpoint identities, keep beacons coarse and rate-limited, use end-to-end encryption for private payloads, minimize deposit receipts so they do not become student movement histories, use experiment-scoped pseudonyms and explicit expiry/withdrawal semantics.

## Difficulty

**Medium.**

## Why this is distinct

UC-023 delivers to a private mailbox endpoint; UC-142 delivers to a stable place/checkpoint service that may be served by changing devices. UC-025 exploits scheduled mobility. UC-049 distributes route/access conditions. UC-128 reserves future contact capacity.

## Research / standards signal

DTN endpoints can represent one or more nodes, while geocast research studies messages whose destination is a geographic region and whose lifetime outlasts one instantaneous contact. PollicinoNet can test a privacy-minimized authenticated checkpoint variant without continuous tracking.

References:

- https://www.rfc-editor.org/rfc/rfc9171.html
- https://doi.org/10.1155/2015/163157
