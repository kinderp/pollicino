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
Build a state machine with `OFFERED -> ACCEPTED -> FORWARDED -> RELEASED/EXPIRED`. Inject:
- relay storage full;
- acceptance followed by node loss;
- duplicate offers;
- stale acceptance after a newer epoch;
- custody timeout;
- delayed final delivery receipt;
- upstream deletion attempted before durable acceptance.

Compare naive "delete after send" against "delete only after explicit custody policy".

## Real hardware
Use 4–6 boards plus 2–3 storage hosts. Move a public test artifact through several relays. Intentionally power off one accepted custodian, fill another cache and delay the next contact. Record only observed state transitions and bytes; do not infer reliability from simulation.

## Messina / provincial teaching scenario
A large public course pack or environmental dataset starts at one school node, is accepted by a student relay, then reaches another school/public checkpoint hours later. The experiment asks when the previous holder is allowed to delete its copy without creating a silent single point of failure.

## Privacy / security
Custody acceptance must be authenticated and bound to an exact object hash, epoch, size and retention/retry policy. Do not encode student identity or detailed route history into the custody record. A custody receipt proves an explicit protocol state, not that storage can never fail.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-098 records relay contribution/delivery progress; UC-109 decides when replicas can be retired; UC-138 models non-delivery reasons. UC-168 focuses on explicit transfer of bounded storage/retry responsibility between holders.

## Standards signal
RFC 4838 described custody transfer as movement of delivery responsibility between DTN nodes. Bundle Protocol Version 7 (RFC 9171) moved custody transfer out of the core specification into bundle-in-bundle mechanisms. UC-168 therefore treats custody as a PollicinoNet application experiment, not as a claim of BPv7 interoperability.
