# UC-CREDENTIAL-001 — Offline verifiable capability / permit

Status: RESEARCH / SECURITY PROTOTYPE

## Problem

Some interactions need a small proof that can be checked while disconnected: a temporary permission to use a lab device, eligibility for a supervised activity, authorization to collect a specific dataset, or a maintenance capability for a Pollicino node.

The verifier may have no Internet connection at the moment of use. Calling a remote identity service for every check defeats the offline-network goal, while broadcasting identity-rich credentials would create unnecessary privacy exposure.

This use case studies **small, signed, offline-verifiable capability tokens** plus delayed revocation/update state. It is not a proposal to put school identity documents or official credentials on LoRa.

## Actors / nodes

- trusted test issuer;
- holder node or companion device;
- verifier node such as a lab station, kit gateway or controlled service;
- school trust/revocation gateway;
- student-carried relay nodes for revocation/generation state;
- optional QR/NFC/BLE presentation channel.

## Why PollicinoNet fits

PollicinoNet is useful for the state around the credential rather than for identity itself:

- distribute issuer generations and revocation state through partitions;
- ferry short-lived capability references;
- enforce expiry and anti-replay semantics;
- carry acknowledgement/audit receipts;
- preserve exact signed bytes;
- use rich links later for full policy or credential refresh.

The W3C Verifiable Credentials 2.0 family is now a Recommendation and provides a relevant standards reference for cryptographically verifiable, privacy-aware claims. This use case does not imply adopting the whole VC stack on an ESP32; compact signed fixtures must be benchmarked first.

## Possible bearers

- QR/NFC: deliberate local presentation of the holder's capability;
- BLE: nearby presentation between companion device and verifier;
- LoRa: issuer/revocation generations, small capability fixtures, status receipts;
- Wi-Fi/LAN: refresh full trust material or policies;
- Internet: optional issuer synchronization when available;
- physical carry: nodes transport fresh revocation/generation state between school and disconnected verifiers.

## What we can test immediately in software

Start with synthetic keys and synthetic users/resources.

Experiments:

1. issuer creates a short-lived `CAN_USE_SENSOR_KIT` capability;
2. verifier checks it offline;
3. issuer publishes a newer revocation generation while verifier is disconnected;
4. student mule carries the new generation later;
5. replay an expired capability;
6. replay an older valid revocation snapshot after a newer one has been seen;
7. test selective/minimal claims versus identity-rich fixtures;
8. compare a tiny custom signed capability fixture with a standards-shaped CBOR/COSE or VC-inspired representation only at the byte/verification-cost level.

Measure:

- verification correctness;
- stale-revocation window;
- bytes required for capability and revocation update;
- CPU/memory proxy on host;
- duplicate/replay rejection;
- amount of identity information exposed.

## Messina student-network scenario

A school could use harmless fixtures such as permission to access a **synthetic lab service** or borrow a **test sensor kit**. A verifier in a territorial cluster may be offline when the permission is presented; fresh revocation/generation state can arrive later through a student-carried node.

No real student credential should be used in the first physical campaigns.

## What requires real hardware

After HW-006 and a security/privacy gate:

- cryptographic verification time and memory on the actual board;
- key storage/restart behavior;
- QR/NFC/BLE companion integration if selected;
- energy impact;
- real delay for revocation-state propagation through the student network.

A production credential system would need independent security review and institutional/legal governance.

## Privacy and security

- synthetic identities and test keys first;
- minimize claims: prove a capability, not a full identity;
- no names, birth dates, addresses or school-sensitive records over LoRa;
- short-lived credentials where feasible;
- signed issuer/revocation generations;
- monotonic anti-rollback state;
- separate holder authentication from network-node identity;
- authorization must fail closed when policy requires fresh online status that is unavailable.

## Difficulty

**High.** Basic signed fixtures are easy; safe lifecycle, revocation, compact representation and real institutional identity integration are security-sensitive.

## Success / kill criteria

Continue if a compact offline capability can be verified exactly, revocation/generation state converges through store-carry-forward, and the design exposes materially less personal information than identity-rich alternatives.

Do not promote a production credential architecture unless a concrete institutional use case, standards/interoperability requirement and independent security review justify it.

## Physical evidence boundary

No PHY change and no claim about real propagation speed or revocation latency is allowed before measured hardware/contact evidence. HW-006 remains unchanged.