# UC-023 — Delay-Tolerant Private Mailbox

## Idea

Give people a small asynchronous mailbox that still works when there is **no simultaneous end-to-end path** between sender and recipient. Messages can wait on trusted or semi-trusted relay nodes and move later when students, devices or gateways meet.

The goal is not to reproduce WhatsApp over LoRa. The experiment is deliberately narrow: small text/control messages, receipts and metadata use the scarce bearer; attachments move later over BLE/Wi-Fi/Internet or by physical carry.

## Problem solved

A normal chat application assumes that sender, server and recipient are reachable within a short time. In a sparse school/province network that assumption fails: two groups may be disconnected for hours even though people carrying relay nodes move between them during the day.

PollicinoNet can treat a message like a delay-tolerant object: store it, carry it, suppress duplicates and deliver it when a valid route eventually appears.

## Actors / nodes

- student personal relay/store-and-forward nodes;
- one or more school/classroom nodes;
- sender and recipient identities or pseudonymous contact identities;
- optional Internet gateway when connectivity exists;
- optional teacher/field coordinator in a controlled drill.

## Why PollicinoNet fits

This use case is almost the smallest human-visible demonstration of store-carry-forward:

- **DISCOVERY:** compact mailbox/contact presence, pending-message hint or rendezvous metadata;
- **EXACT:** signed/encrypted message envelope, message ID, expiry and delivery receipt;
- **SEMANTIC:** optional local classification such as `ordinary`, `important`, `drill`, kept separate from the exact signed envelope.

A relay does not need to understand the message body. It only needs enough metadata to decide whether it may store/forward the ciphertext.

Nothing requires a change to the frozen LoRa PHY.

## Possible bearers

- **LoRa:** very small encrypted text envelopes, message IDs, ACK/receipt state and rendezvous metadata when payload/airtime measurements permit;
- **BLE:** nearby mailbox synchronization and larger short payloads;
- **Wi-Fi/LAN:** bulk synchronization and attachments;
- **Internet:** optional fast path when available;
- **physical transport:** a student/device carries queued ciphertext between disconnected islands.

## What we can test now in software

- define an immutable `MessageEnvelope` with sender key, recipient key/alias, message ID, creation epoch, expiry, priority and ciphertext;
- implement persistent outbox/inbox state;
- simulate two disconnected groups and a moving courier;
- implement duplicate suppression and idempotent delivery;
- compare single-copy, spray-and-wait and small bounded-copy policies;
- add delivery receipts without requiring a live reverse path;
- simulate delayed, reordered and duplicated packets;
- enforce per-node queue/storage budgets so a relay cannot be filled indefinitely;
- make expired/stale messages visibly expire rather than circulate forever;
- verify that relay nodes cannot decrypt end-to-end encrypted content;
- measure delivery ratio, time-to-delivery, duplicate overhead, queue pressure and bytes per bearer.

A useful invariant is:

> a message can be delayed or duplicated in transit, but it must never be delivered twice as two different logical messages.

## What requires real hardware

- at least 4 boards divided into two groups with no direct path;
- one student/device physically moving between groups;
- measured LoRa packet delivery and contact windows for the control/small-message path;
- optional BLE/Wi-Fi attachment handover;
- repeatable tests with recipient absent, relay absent and delayed return path.

The test must not be presented as an emergency-grade communications service.

## Messina teaching scenario

Create two classroom/lab islands, for example a simulated `Rometta` group and `Messina` group. Student A sends a small encrypted note to Student B while the groups are disconnected. A third student's node later visits both groups and acts as courier. B receives the exact logical message and, on a later reverse contact, A eventually receives the delivery receipt.

A second exercise can use three or four coarse zones along a controlled route and compare bounded-copy forwarding strategies. Do not collect students' home addresses or continuous movement histories.

## Privacy / security

End-to-end encryption is required for private content because store-and-forward relays may be curious or compromised. Authentication and anti-replay are required; message IDs must not be forgeable in a way that lets an attacker suppress someone else's message. Metadata is still sensitive: sender/recipient relationships, timing and queue presence can reveal social information even when bodies are encrypted.

Use pseudonymous test identities, short retention, storage quotas and coarse rendezvous metadata. Classroom experiments must use harmless synthetic messages.

## Difficulty

**Medium.** The basic queue is easy; secure identity, metadata minimization, bounded replication, receipts and correct behavior across long disconnections are the interesting parts.

## Research signal

Delay/Disruption-Tolerant Networking continues to formalize reliability without assuming a simultaneous end-to-end path. NASA describes DTN operationally as store-and-forward across disrupted links, and a 2026 IETF draft revisits reliability semantics for DTN. Recent offline messengers also experiment with persistent outboxes/courier-style delivery, reinforcing that asynchronous human messaging is a useful real-world test surface.

References:

- https://www.nasa.gov/communicating-with-missions/delay-disruption-tolerant-networking/
- https://datatracker.ietf.org/doc/draft-birrane-dtn-rel/
