# UC-066 — Pseudonymous Separated-Group Reunification Drill

## Idea

Test whether PollicinoNet can help **reconnect separated groups in a controlled emergency/civil-protection exercise** without broadcasting names, home addresses or continuous location histories.

A participant or team can publish a small pseudonymous `ReunificationNeed`; a trusted checkpoint can publish a compatible `SafeAtCheckpoint` or contact-ready state; student relay nodes carry those records across disconnected areas until a private rendezvous becomes possible.

This is deliberately a **training use case**, not an emergency-grade missing-person system. It composes ideas from UC-023 (private mailbox), UC-030 (privacy-preserving check-in), UC-048 (narrow credentials) and UC-050 (privacy-limited encounter trail), but the object being reconciled is a human/group relationship and therefore requires much stricter privacy rules.

## Problem solved

During a drill or communications outage, two authorized parties may not have a simultaneous path to each other or to a central server. A central public list of names and locations would be privacy-invasive and could become dangerous if copied or stale.

The useful minimum information may instead be:

```text
reunification_case = opaque token
status = seeking / safe-at-checkpoint / contact-ready / closed
checkpoint = coarse authorized label
valid_until = ...
```

The network should carry enough information to create a private rendezvous while revealing as little as possible to relays.

## Actors / nodes

- synthetic participants or supervised volunteer teams;
- trusted school/civil-protection exercise coordinator;
- authorized checkpoint nodes;
- student relay/store-and-forward nodes;
- optional guardian/group relationship issuer using synthetic credentials;
- optional Internet gateway when connectivity returns.

## Why PollicinoNet fits

The status objects are small and useful even when delivered late, provided freshness is explicit.

- **DISCOVERY:** opaque case token, status class, coarse checkpoint availability and expiry;
- **EXACT:** signed case/status object, authorization scope, checkpoint identity and one-use rendezvous token;
- **SEMANTIC:** human-friendly labels such as `safe`, `seeking`, `contact-ready`, never a substitute for exact authorization/state.

LoRa can transport opaque status/control records. Private details can be exchanged only after authorization over BLE/Wi-Fi or a direct supervised meeting.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** opaque case/status token, freshness, checkpoint code and rendezvous availability;
- **BLE:** local private confirmation at a checkpoint;
- **Wi-Fi/LAN:** authenticated case reconciliation and richer private messages;
- **Internet:** optional synchronization with a trusted exercise coordinator;
- **physical transport:** student relays carry encrypted/pseudonymous case state between disconnected checkpoints.

## What we can test now in software

Use only synthetic identities and relationships.

Implement and test:

- `ReunificationCase`, `ReunificationNeed`, `SafeAtCheckpoint` and `CaseClosed` objects;
- one-use or short-lived rendezvous tokens;
- two disconnected checkpoint groups and moving relays;
- duplicate/reordered status records;
- stale `safe` status after a participant moves;
- contradictory status from two checkpoints;
- case closure and deletion/retention rules;
- authorization failure for an unrelated requester;
- delayed consent/guardian relationship proof in a synthetic scenario;
- explicit `unknown` when status is too old;
- metadata minimization tests showing that relay logs cannot reconstruct a person's route;
- integration with UC-023 for encrypted private follow-up after a match.

Useful metrics include time-to-rendezvous, stale-status exposure, duplicate overhead, unresolved-conflict count and bytes of sensitive metadata exposed to relay nodes.

A key invariant is:

> `not seen` and `not yet reconciled` must never be interpreted as `missing`, `unsafe` or any other real-world conclusion.

## What requires real hardware

- 5+ boards split among two or three controlled school/campus checkpoints;
- synthetic participant identities only;
- a scripted separation/reconnection scenario;
- one or more moving student relays;
- real LoRa transport of pseudonymous status objects;
- optional BLE/Wi-Fi private confirmation at the final checkpoint;
- measured delay and stale-state behavior under intentional disconnection.

Do not use real missing-person cases, real minors' names, home addresses, medical data or actual emergency operations in the prototype.

## Messina teaching scenario

Run a school/civil-protection-style exercise with three named public checkpoints, for example `School`, `Villafranca checkpoint` and `Rometta/Spadafora checkpoint`. Synthetic team `G-17` is separated into two subgroups. One checkpoint records that subgroup A is safe; subgroup B creates a private reunification request while disconnected.

Student relay nodes move between checkpoints and eventually bring the compatible status objects together. Only after the match does the system produce a one-use private rendezvous token for the supervised coordinator.

The class can then test what happens when:

- a status is delayed;
- the same status arrives twice;
- two checkpoints claim incompatible current state;
- the relay carrying the newest update never arrives;
- the case expires before reconciliation.

The exercise demonstrates disruption tolerance while teaching why human-safety data needs stronger privacy than ordinary content distribution.

## Privacy / security

This is one of the highest-sensitivity use cases in the catalog.

- use synthetic people/relationships in all early experiments;
- never broadcast names, phone numbers, home addresses, medical state or exact GPS position;
- use opaque case identifiers and short retention;
- separate relay-visible status from private identity mapping;
- encrypt private case details end-to-end;
- authenticate checkpoint/status issuers;
- require narrow authorization before revealing a match;
- prevent replay of old `safe` or rendezvous records;
- make `unknown/stale` explicit;
- do not infer a person's condition from absence of data;
- perform a privacy/data-protection review before any non-synthetic pilot.

## Difficulty

**High.** The message sizes are easy; the hard problem is human safety, authorization, stale-state semantics and data minimization. This should remain a controlled educational drill until reviewed by appropriate organizations and privacy/safety experts.

## Humanitarian signal

The Red Cross/Red Crescent Restoring Family Links ecosystem exists precisely because conflict, migration and disasters can separate families and because reconnecting people requires careful handling of sensitive personal data. The ICRC explicitly treats privacy and data protection as core requirements. UC-066 uses that as a design warning and motivation, not as evidence that PollicinoNet is suitable for real humanitarian deployment.

References:

- https://www.icrc.org/en/what-we-do/reconnecting-families
- https://www.icrc.org/en/document/rfl-code-conduct
- https://familylinks.icrc.org/privacy-policy
