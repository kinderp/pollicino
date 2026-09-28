# UC-132 — Authoritative Emergency Alert Update/Cancel Supersession Courier

## Idea

Carry the lifecycle of an authoritative emergency-drill alert — initial alert, update, cancellation and expiry — through partitions without letting an old message silently remain current after newer authoritative state exists.

This remains a drill/test profile until independently validated.

## Problem solved

Store-and-forward makes stale information a first-class risk. An initial alert may reach one group, a cancellation another, and an old relay may appear hours later carrying the original message.

If clients display the latest packet by arrival time, obsolete instructions can reappear.

We need an exact supersession graph so nodes distinguish active, updated, cancelled, expired, missing-reference and conflicting states.

## Actors / nodes

Authoritative exercise publisher, student relay/store-and-forward nodes, recipient nodes, optional coverage collector, optional UC-106 multilingual worker and optional laboratory CAP gateway.

## Why PollicinoNet fits

Alert lifecycle metadata is small and valuable before richer payloads arrive.

A compact state object can carry publisher ID, message ID, type, predecessor references, issue time, expiry, exact payload hash and TEST/EXERCISE status.

LoRa carries compact lifecycle state while BLE/Wi-Fi/LAN or physical transport can carry maps, audio, images and detailed material.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: message ID, ALERT/UPDATE/CANCEL type, references, expiry, source/hash and short drill text.
- BLE: complete compact alert objects.
- Wi-Fi/LAN: full package, maps, audio and evidence logs.
- Internet: optional laboratory CAP source.
- Physical transport: student-carried cache moving the alert history.

## What we can test now in software

Use only fictional messages marked TEST or EXERCISE.

Create:

A1 = ALERT

A2 = UPDATE references A1

A3 = CANCEL references A2 or A1 according to the chosen profile

Test normal order, cancellation before initial alert, update after cancellation, duplicates, missing predecessor, conflicting updates, stale UC-106 translation after cancellation, uncertain clock around expiry and a relay returning after the full lifecycle.

Compute explicit states such as ACTIVE, SUPERSEDED, CANCELLED, EXPIRED, REFERENCE_MISSING, CONFLICT and UNVERIFIED.

A delayed older message must never silently reactivate a state that is already provably superseded or cancelled.

## What requires real hardware

Use 6–10 boards split into three controlled islands.

Inject A1, allow only one island to receive A2, then inject A3 and physically move relays so messages arrive in different orders. Reconnect all groups and verify convergence.

Measure actual propagation/order/convergence only. Do not present the exercise as a production public-warning channel.

## Messina teaching scenario

A fictional civil-protection exercise starts at a school node in Messina. Villafranca receives the initial alert, Rometta/Venetico receives an update and Spadafora receives the cancellation first. Hours later a student relay carrying the original alert reaches Spadafora.

The receiver must preserve supersession state rather than treating late arrival as freshness.

## Privacy / security

Authenticate the exercise source, preserve exact message IDs/references/hashes, mark every trial TEST or EXERCISE, never let derived translations override authoritative lifecycle state, quarantine conflicts, avoid named attendance inference from receipts, keep delivery reporting aggregate, and define behavior for uncertain clocks.

Real emergency use requires independent safety/security validation.

## Difficulty

Medium. Message formatting is straightforward; correct convergence under reordering and stale relays is the valuable part.

## Why this is distinct

UC-002 distributes one signed bulletin; UC-089 models acknowledgment/escalation of a local sensor alarm; UC-102 studies dissemination of one object; UC-106 creates multilingual derivatives. UC-132 models authoritative alert update/cancel/supersession lifecycle.

## Standards signal

OASIS Common Alerting Protocol (CAP) 1.2 defines Alert, Update and Cancel message types. Update supersedes earlier messages identified through references, while Cancel cancels referenced earlier messages. Those semantics map naturally to store-and-forward delivery where messages can arrive out of order.

References:

- https://www.oasis-open.org/standard/cap/
- https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html
