# UC-EMERG-001 — Resilient community bulletin and safety-status relay

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Problem

During a local Internet/mobile outage, congestion event or civil-protection exercise, people may still need to move a small amount of **time-sensitive, verifiable information** between disconnected local clusters.

The target is not voice, video or an emergency-services replacement. The target is compact information such as:

- official/public warning identifiers and short updates;
- road/service availability notices;
- shelter, charging, water or local-service availability;
- coarse area status;
- a minimal `safe / need-assistance / unknown` status under an explicit privacy policy;
- requests for non-life-critical supplies or local coordination;
- a rendezvous/reference that can be resolved when richer connectivity returns.

PollicinoNet must never be described as an emergency-grade or life-safety system without an independently validated reliability, security and operational design.

## Actors / nodes

- student-carried relay nodes used in supervised exercises;
- fixed school/community nodes;
- optional authorized publisher/gateway;
- territorial relay nodes;
- DNA Commons/Topic/Subscription when DNA supplies application semantics;
- optional Internet/Wi-Fi gateway when infrastructure becomes available again.

## Messina educational scenario

Use pseudonymous logical clusters representing, for example, a school hub and territorial clusters such as Rometta, Spadafora, Saponara and Villafranca. These names identify scenario areas only; the experiment must not encode student home addresses or infer that direct LoRa coverage exists between towns.

Example flow:

```text
authorized bulletin source
        |
        v
school hub / dense morning contacts
        |
        +--> student mule A --> territorial cluster A
        +--> student mule B --> territorial cluster B
        +--> student mule C --> territorial cluster C
                              |
                              v
                    later local/off-grid contacts
```

## Why PollicinoNet fits

This case needs properties already central to PollicinoNet:

- store-carry-forward when no end-to-end path exists;
- expiry and priority;
- duplicate suppression;
- compact discovery/reference transfer;
- custody and resumable exact delivery;
- multiple bearers and later rich-link handover;
- explicit wire/TRC accounting.

DNA can decide **topic, geo-scope, subscription, visibility, provenance and verification state**. PollicinoNet can decide how to move the smallest permitted representation.

## Possible bearers

- LoRa for scarce long-range discovery/compact notices;
- BLE for close-range phone/node rendezvous;
- Wi-Fi/Wi-Fi Direct for richer local synchronization;
- Internet when available;
- physical student/vehicle movement as the carry phase.

No PHY change is justified by this use case.

## What can be tested now in software

A useful synthetic experiment needs no physical boards:

1. create official, community-confirmed and unverified message classes;
2. give messages explicit usefulness deadlines separate from transport TTL;
3. model a dense school phase followed by sparse territorial contacts;
4. compare Direct Delivery, Epidemic, Spray-and-Wait and later PRoPHET;
5. compare priority-aware scheduling with FIFO;
6. measure delivery before deadline, duplicate traffic, TRC and stale-message suppression;
7. inject an intermittent Internet gateway and measure how many messages can finish through handover.

This is also a concrete justification for adding **application usefulness deadline** to the experimental workload model, without redefining PNB1 TTL.

## What requires real hardware

HW-006 or a later field campaign is required before claiming:

- that a school or territorial cluster is physically connected by LoRa;
- useful bytes per real contact;
- range through buildings/terrain;
- delivery probability or latency on real student routes;
- emergency-priority airtime capacity;
- battery/energy behavior.

The frozen 42-byte / 2 dBm physical campaign remains unchanged.

## Privacy / security

Difficulty is dominated by authenticity and metadata safety, not payload size.

Requirements:

- authenticated publisher for official messages;
- clear distinction between `OFFICIAL`, `COMMUNITY_CONFIRMED`, `UNVERIFIED` and `DISPUTED` information;
- anti-replay and expiry;
- no persistent public radio identity;
- no exact home location in the pilot;
- minimal personal safety status, opt-in and short-lived;
- no automatic action by critical systems based solely on an experimental message.

A forged emergency notice is worse than a missing entertainment message, so security failure modes must be first-class metrics.

## Implementation difficulty

**Medium-high.** Routing and store-carry-forward primitives largely exist. The harder work is application deadline semantics, authenticated provenance, abuse/spam controls and safe UX.

## Minimal measurable hypotheses

- H1: priority + deadline-aware scheduling increases delivery-before-deadline for urgent messages compared with FIFO under the same contact budgets.
- H2: bounded replication can preserve most delivery benefit while reducing wire bytes relative to full epidemic flooding.
- H3: the school mixing phase improves later territorial dissemination under identical afternoon contacts.

## Metrics

- delivery-before-deadline ratio;
- delivery latency;
- urgent-message delivery ratio;
- expired/stale transmissions suppressed;
- duplicate copies and forwarding actions;
- payload, metadata, ACK and retransmission bytes;
- TRC per useful delivered message;
- false/invalid/replayed message rejection;
- privacy exposure class.

## Gate decision

**PROTOTYPE.** The use case is concrete and materially different from generic DNA topic exchange because it introduces usefulness deadlines, stronger provenance/authenticity requirements and asymmetric cost of stale/forged information. It does not justify claims of emergency-service reliability.

## Related research precedent

DTNs are widely studied for post-disaster and infrastructure-disrupted communication. A recent example explicitly frames deadline-constrained routing for disaster response: https://doi.org/10.1016/j.comcom.2024.108038 .