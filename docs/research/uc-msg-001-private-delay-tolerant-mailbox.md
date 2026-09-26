# UC-MSG-001 — Private delay-tolerant mailbox

Status: PROTOTYPE / PRIVACY-SENSITIVE INTEGRATION

## Problem

Two people or devices may need to exchange a small private message even when sender and receiver are never online or radio-reachable at the same time. A message can be created in one territorial cluster, physically carried by intermediate nodes, and delivered hours later when the destination is encountered.

This is deliberately different from `UC-EMERG-001`, which is an authenticated community bulletin, and from `UC-EDU-001`, which carries classroom-resource state. Here the defining requirement is **destination-specific private mailbox semantics**: end-to-end confidentiality, delayed delivery, duplicate suppression and a privacy-preserving return receipt.

The first PollicinoNet experiment must use synthetic text/opaque test payloads or bot endpoints, not real student conversations.

## Actors / nodes

- sender node;
- destination node or destination mailbox role;
- student-carried relay nodes that never need to read the payload;
- optional school mailbox/referee gateway;
- optional home Wi-Fi/Internet endpoint for later rich delivery.

## Messina educational scenario

A synthetic message created in a pseudonymous `west-coast` cluster is destined for a node in a `north-coast` cluster. The two endpoints never meet that afternoon. One or more students carry ciphertext through ordinary movement; the school mixing phase the following morning provides another forwarding opportunity. A tiny delivery receipt may travel back by a different path.

Public town names such as Rometta, Spadafora, Villafranca or Saponara may be used only as scenario labels. No result may imply measured coverage between them.

```text
sender -> ciphertext bundle -> relay A
                              [physical carry]
                         -> relay B -> destination
                                         |
                                         +-> receipt -> later return path
```

## Why PollicinoNet fits

The use case needs exactly the properties already being studied:

- store-carry-forward when no contemporaneous path exists;
- stable bundle identity across bearer changes;
- finite relay storage and explicit expiry;
- duplicate suppression and bounded replication;
- custody/receipt state that can return asynchronously;
- opaque payload transport, so intermediate relays do not need application plaintext.

It also stresses destination-aware routing more strongly than broadcast/topic workloads and can therefore become a useful discriminator between Direct Delivery, Spray-and-Wait, PRoPHET and the current destination-recency family.

## Possible bearers

- LoRa for small opaque ciphertext bundles and receipts;
- BLE for short-range direct encounters if separately enabled;
- Wi-Fi/LAN for draining or resolving richer content;
- Internet as an optional later transport, not a requirement;
- physical student movement as the carry mechanism.

No new LoRa PHY value is proposed.

## What can be tested now in software

Use `MODEL_SYNTHETIC` only and keep cryptographic choices replaceable at first.

1. destination-specific bundles with synthetic ciphertext payloads;
2. receiver unavailable for hours or days;
3. bounded replication versus single-copy delivery;
4. delayed delivery receipts and replica retirement;
5. expiry versus application usefulness deadline;
6. duplicate/replay injection;
7. queue pressure when several private destinations compete;
8. metadata exposure comparison between stable destination IDs and rotating laboratory pseudonyms;
9. bearer transitions `CONNECTED_MESH -> OPPORTUNISTIC_DTN -> RICH_HOME` without object-identity change.

The first networking experiment does **not** require inventing a new cryptographic protocol. Payloads can be pre-encrypted fixtures while routing, receipts and metadata minimization are measured independently.

## What requires real hardware

Real boards are required before claiming:

- actual message delivery probability on student mobility;
- real time-to-delivery or inter-contact behavior;
- useful ciphertext bytes per encounter;
- energy impact of mailbox scanning/relay behavior;
- BLE/LoRa coexistence or handoff quality;
- reliability of real delivery receipts.

HW-006 remains the first RF gate.

## Privacy / security

This use case is privacy-critical, especially in a school deployment.

Requirements before any human pilot:

- end-to-end encryption; relays must not need message plaintext;
- authenticated destination binding and anti-replay;
- minimize routing metadata and retention;
- no real student chat content in the first field experiment;
- pseudonymous laboratory identities and bot/test destinations first;
- no central plaintext logging for network research;
- abuse/reporting policy before opening human-to-human messaging;
- do not infer friendship/social graphs from delivery telemetry;
- keep key-distribution and revocation work behind the security gate, with `UC-TRUST-001` as related research rather than silently inventing a new scheme.

Offline messaging does not remove metadata risk. End-to-end content encryption alone is insufficient privacy protection.

## Implementation difficulty

**Medium-high.** The basic bundle transport is small; secure identities, key lifecycle, metadata minimization and abuse-resistant human messaging are the hard parts.

## Minimal measurable hypotheses

- H1: a destination-specific workload exposes routing differences that topic/broadcast traffic does not.
- H2: delayed receipts can retire redundant replicas and reduce storage/forwarding cost without materially hurting delivery.
- H3: useful mailbox behavior can be represented without putting plaintext or stable human identity into relay-visible state.

## Metrics

- delivery probability;
- time to delivery;
- return-receipt latency;
- copies/forwards per delivered message;
- relay storage occupancy;
- bytes of payload versus routing/receipt metadata;
- expired/undelivered messages;
- replay/duplicate rejection rate;
- metadata fields exposed per relay.

## Success / kill criterion

**Continue** if the synthetic workload produces a useful destination-aware routing/receipt discriminator with bounded metadata and no new wire protocol requirement.

**Defer** human messaging if privacy/security governance dominates the research value or if the same experiment can be represented more safely with bot endpoints.

## Gate decision

**PROTOTYPE.** Implement only isolated synthetic/fixture experiments first. This document does not authorize a production chat service.

## Related precedent

Bundle Protocol Version 7 explicitly targets intermittent connectivity and physical motility through a store-carry-forward overlay: https://www.rfc-editor.org/rfc/rfc9171.html .

Briar is a concrete modern example of peer-to-peer private messaging that can work without Internet and uses Bluetooth/Wi-Fi for nearby connectivity: https://briarproject.org/ . It is precedent for the application need, not a claim that Pollicino should copy Briar's protocol or security design.
