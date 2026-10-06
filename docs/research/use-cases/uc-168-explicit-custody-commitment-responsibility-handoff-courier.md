# UC-168 — Explicit Custody Commitment and Responsibility-Handoff Courier

## Problem solved
In a store-and-forward network, a sender may need to free local storage before the final destination is reachable. A normal forwarding receipt only says that another node saw or accepted data; it does not necessarily mean that the new node has explicitly accepted responsibility for preserving and retrying that exact object.

UC-168 studies an application-level custody commitment: a relay can explicitly accept bounded storage/retry responsibility for an exact object, after which the previous holder may safely reduce its own responsibility according to policy.

## Actors / nodes
Origin node, student relay, next custodian/cache, final destination, optional custody auditor and experiment controller.

## Why PollicinoNet fits
PollicinoNet already separates compact control state from bulk transfer. A custody offer, acceptance, refusal, expiry, transfer epoch and object hash are small enough for the control plane, while the object itself can move over a richer bearer. Store-carry-forward makes responsibility handoff a natural experiment.

This does not modify the frozen LoRa PHY and does not assume Bundle Protocol custody semantics.

## Bearers
- LoRa: custody offer/accept/refuse/expiry, object ID/hash and responsibility epoch.
- BLE/Wi-Fi/LAN: object transfer and local verification.
- Internet: optional later audit or final receipt.
- Physical transport: large object carried on managed storage while custody state travels separately.

## Software test now
Build a state machine with OFFERED -> ACCEPTED -> FORWARDED -> RELEASED/EXPIRED. Inject relay storage full, node loss after acceptance, duplicate offers, stale acceptance, custody timeout and delayed final receipt.

## Real hardware
Use 4–6 boards plus 2–3 storage hosts. Move a public test artifact through several relays and record observed state transitions and bytes; do not infer reliability from simulation.

## Messina / provincial teaching scenario
A public course pack or environmental dataset starts at one school node, is accepted by a student relay, then reaches another school/public checkpoint hours later.

## Privacy / security
Bind the commitment to exact object hash, epoch, size and retention policy. Avoid student identity and detailed route history. A custody receipt proves protocol state, not permanent storage durability.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-098 records relay contribution/delivery progress; UC-109 decides when replicas can be retired; UC-138 models non-delivery reasons. UC-168 focuses on explicit transfer of bounded storage/retry responsibility between holders.

## Standards signal
RFC 4838 described custody transfer as movement of delivery responsibility between DTN nodes. RFC 9171 moved custody transfer out of the BPv7 core specification into bundle-in-bundle mechanisms. UC-168 is an application-level PollicinoNet experiment, not a BPv7 interoperability claim.
