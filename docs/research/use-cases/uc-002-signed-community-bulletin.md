# UC-002 — Signed Community Bulletin and Civil-Protection Drill

## Idea

Propagate small, signed, expiring bulletins across a disconnected student mesh: school notices, test messages, meeting points, synthetic road-closure notices or civil-protection **drill** traffic. The design is useful for resilience research, but it must not be presented as an operational emergency service until reliability is independently validated.

## Problem solved

When Internet access is absent or fragmented, a short authoritative message may still need to reach many local nodes without transmitting a large document repeatedly.

## Actors / nodes

- school or laboratory publisher;
- optional municipal/civil-protection test publisher;
- student relay nodes;
- fixed gateways at school or community locations;
- recipient devices that verify signatures and expiry.

## Why PollicinoNet fits

A bulletin can be a tiny `EXACT` signed object or a `DISCOVERY` coordinate for a larger signed manifest. Store-and-forward, TTL, duplicate suppression and versioning are natural fits for intermittent relay networks.

## Possible bearers

- **LoRa:** compact signed bulletin, version/expiry, or manifest coordinate;
- **BLE/Wi-Fi:** nearby bulk document retrieval;
- **Internet:** authoritative manifest/document retrieval when available;
- **physical transport:** relay nodes carry pending bulletins across network partitions.

No PHY change is required or proposed.

## What we can test now in software

- signature verification and rejection of forged messages;
- expiry, replay protection and superseding an older bulletin with a newer version;
- priority queues and deterministic conflict rules;
- network partitions, delayed relays and duplicate floods in the simulator;
- comparison of full-message vs coordinate-only scarce-link cost;
- synthetic emergency-drill scenarios with no real operational dependency.

## What requires real hardware

- controlled multi-hop relay tests with synthetic bulletins;
- measured propagation time, loss, duplicates, RSSI/SNR and airtime;
- physical verification of expiry/supersession after nodes reconnect.

No claim of emergency reliability is valid without dedicated field validation, operational procedures and independent fallback channels.

## Privacy / security

Public bulletins should be signed and replay-resistant. Private/group bulletins need encryption and scoped identifiers. Avoid broadcasting names, medical information, precise household locations or other sensitive data. Publisher keys and revocation must be handled explicitly.

## Difficulty

**Medium.** The data volume is small; the hard parts are authority, replay/supersession semantics and proving behavior under partitions.
