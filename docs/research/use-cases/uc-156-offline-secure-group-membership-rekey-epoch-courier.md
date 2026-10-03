# UC-156 — Offline Secure Group Membership and Rekey-Epoch Courier

## Problem solved

A secure student or emergency-drill group can change membership while some members are offline. A removed member should not keep receiving future protected group traffic, while a newly added member may not obtain the current group state until a relay reaches it.

UC-156 studies how standardized group-membership and key-epoch state can be transported over an intermittent DTN without inventing new cryptography.

The first implementation target should use an existing Messaging Layer Security (MLS) implementation or another reviewed group-messaging primitive.

## Actors / nodes

Group members, a school/application authorization service, optional messaging delivery components, student relay/store-and-forward nodes and one synthetic offline/removed member for testing.

## Why PollicinoNet fits

MLS is designed for asynchronous group operation, but it still needs a delivery mechanism. PollicinoNet can provide delayed transport for compact group-state indicators and, where appropriate, handshake material.

Useful state includes group ID, epoch, commit identity, membership-change type, authorization-policy version and visible states such as `CURRENT`, `STALE`, `NEEDS_COMMIT`, `NEEDS_WELCOME` or `FORKED`.

Large handshake/catch-up objects should use BLE/Wi-Fi/LAN or physical transport unless real measurements show that a specific bounded object is appropriate for LoRa.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** group/epoch summary, commit identity, stale-state notice and small bounded control objects.
- **BLE:** nearby handshake synchronization.
- **Wi-Fi/LAN:** Welcome/Commit traffic, catch-up state and diagnostics.
- **Internet:** ordinary delivery service when reachable.
- **Physical transport:** authenticated catch-up package between disconnected islands.

## What we can test now in software

Use synthetic identities and an established MLS implementation.

Test group creation, partition into two islands, add/remove operations during a partition, delayed state delivery, out-of-order application messages, a member that returns after several epochs, and concurrent membership changes based on the same old epoch.

Check that stale members are visibly stale, current epoch never moves backward, losing/conflicting updates are not silently accepted, and application authorization policy remains separate from cryptographic group state.

## What requires real hardware

Use 4–6 LoRa boards plus laptops/phones running the group-messaging implementation. Split them into two controlled network islands and change membership while one side is disconnected. Student-carried relays later move the required control/handshake material.

Measure real object sizes and catch-up latency before deciding what belongs on LoRa versus a richer bearer.

## Messina teaching scenario

Create a synthetic project group spanning Messina, Villafranca and Rometta/Venetico-Spadafora. One island remains offline during a membership change. A relay later carries the new epoch state so students can observe the difference between a valid old message and current group membership.

This is a security/state-convergence exercise, not a real emergency communications service.

## Privacy / security

Group membership is sensitive metadata. Do not broadcast member lists or stable personal identities on LoRa. Use pseudonymous test identities and minimal epoch/status disclosure.

Do not implement ad-hoc cryptography. Keep access-control rules explicit at the application layer and test stale/forked states.

PollicinoNet is only evaluating delayed delivery and convergence; security properties come from the reviewed group-messaging protocol and implementation.

## Difficulty

**High.**

## Why this is distinct

UC-019 propagates general trust revocation. UC-023 provides a private delay-tolerant mailbox. UC-102 spreads one exact object to many nodes. UC-156 focuses on dynamic encrypted group membership and group epochs across partitions.

## Standards signal

MLS is standardized in RFC 9420. RFC 9750 describes the architecture, including asynchronous use, group epochs, add/remove/update operations and the need for a delivery service.

References:

- RFC 9420 — The Messaging Layer Security (MLS) Protocol.
- RFC 9750 — The Messaging Layer Security (MLS) Architecture, April 2025.
