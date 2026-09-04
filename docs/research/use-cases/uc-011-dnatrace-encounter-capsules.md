# UC-011 — DNATrace Encounter Capsules

## Idea

Turn DNA/DNATrace into a concrete privacy-first PollicinoNet experiment. Two nearby nodes exchange **minimal pseudonymous encounter traces** over LoRa, discover that a later rendezvous may be useful, and defer any richer or personal data exchange until explicit consent and a better bearer are available.

For a school demo, students can use synthetic identities and harmless project topics such as `robotics`, `linux`, `3d-printing` or `sensor-data`. A trace says only enough to discover a compatible intent; any later DNAFragment is exact, scoped and authorized.

## Problem solved

Offline discovery is useful, but broadcasting identities or profiles over long-range radio would be unacceptable. We need a minimal temporary signal that can survive intermittent connectivity without leaking the full person, profile or intent history.

## Actors / nodes

- two or more DNA-enabled student devices;
- PollicinoNet transport adapters;
- optional school rendezvous/resolver service;
- optional student relay nodes carrying unresolved traces;
- synthetic DNA profiles for initial experiments.

## Why PollicinoNet fits

The PollicinoNet architecture already places DNATrace above the network layer and defines `DISCOVERY` as a compact rendezvous contract, not proof or payload. This use case exercises exactly that boundary: ephemeral discovery first, consented exact data later, with store-and-forward when no end-to-end path exists.

## Possible bearers

- **LoRa:** compact DNATrace/short coordinate, expiry and capability hints;
- **BLE:** nearby consent/rendezvous confirmation;
- **Wi-Fi/Internet:** authorized DNAFragment or application data;
- **physical transport:** a relay can carry unresolved rendezvous tokens between disconnected areas.

## What we can test now in software

- generate synthetic DNATrace objects and compact wire encodings;
- rotating/scoped identifiers and expiry;
- semantic/topic matching without revealing full profiles;
- consent state machine before any DNAFragment release;
- store-and-forward of unresolved rendezvous coordinates;
- replay, duplicate and stale-trace handling;
- privacy tests that verify sensitive fields never appear in LoRa payloads.

## What requires real hardware

- two-board pseudonymous trace exchange;
- 3+ node relay/store-and-forward of an unresolved trace;
- measured discovery success and delay under controlled movement;
- BLE/Wi-Fi handover after a LoRa rendezvous.

Use synthetic profiles until the privacy model is reviewed. No claim about human matching or social usefulness should be made from radio tests alone.

## Privacy / security

Privacy is the core requirement: rotating ephemeral IDs, short lifetimes, unlinkability where practical, explicit consent, minimal metadata, authenticated fragments and revocation. Do not broadcast names, school class, exact interests tied to a real identity, home location or stable device identifiers.

## Difficulty

**Medium.** The transport is small; the difficult part is getting identity, consent, replay resistance and metadata minimization right.
