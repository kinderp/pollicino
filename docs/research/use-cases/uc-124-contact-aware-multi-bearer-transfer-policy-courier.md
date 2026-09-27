# UC-124 — Contact-Aware Multi-Bearer Transfer Policy Courier

## Idea

Choose which available bearer should carry a PollicinoNet transfer: LoRa, BLE, Wi-Fi/LAN, Internet, or physical carry. This is an application-layer scheduling policy and does not change the frozen LoRa PHY.

## Problem solved

The network may discover a peer over LoRa but still need to decide how the real payload should move. BLE may be enough for a small file, Wi-Fi may suit a larger file, Internet may be unavailable, and a very large object may be better moved later by a student carrying a laptop or storage device.

Without one reusable decision model, every application can invent a different rule.

## Actors / nodes

Requester or producer, student relay/store-and-forward node, LoRa board, BLE/Wi-Fi companion device, optional Internet-connected node, optional physical carrier, and an experiment collector.

## Why PollicinoNet fits

The decision uses compact metadata such as object size, deadline, bearer availability, local resource budget, queue pressure from UC-108, and progress already made by UC-112.

- DISCOVERY: coarse bearer capability and availability.
- EXACT: transfer intent, object hash, policy version, selected bearer and fallback order.
- SEMANTIC: friendly classes such as small, bulk, or delay-tolerant.

## Possible bearers

- LoRa: discovery and compact control;
- BLE: nearby small/medium transfer;
- Wi-Fi/LAN: local bulk transfer;
- Internet: optional fast path when available and allowed;
- physical transport: device or storage carried between disconnected groups.

## What we can test now in software

Build a small policy engine and compare fixed rules with adaptive rules.

Test:
- small vs large objects;
- short vs long contact windows;
- one bearer disappearing before transfer;
- queue pressure changing during the decision;
- resumable progress already present;
- a policy that deliberately defers a very large object for later physical carry.

Measure completed objects, setup attempts, fallback count, wasted bytes, and time-to-completion in simulation. These are not radio-performance claims.

## What requires real hardware

Use 4–6 LoRa boards paired with at least two BLE/Wi-Fi-capable endpoints. Run the same scripted workload with BLE, Wi-Fi and delayed physical carry, then compare measured setup time, completion and transferred bytes.

Energy comparisons require real instrumentation.

## Messina teaching scenario

A student in Rometta has a requested Raiatea pack. Another student reaches that node only briefly. A small note can move over BLE, a larger pack can wait for Wi-Fi at school, and a very large dataset can be carried later on a laptop or storage device.

The same trace can be replayed with fixed and adaptive policies.

## Privacy / security

Advertise only coarse bearer capability, bind the decision to the exact object and policy version, preserve the authenticated handoff from UC-033, and respect local volunteer/resource policy from UC-095 and UC-108.

## Difficulty

Medium–High.

## Why this is distinct

UC-033 secures a rich-bearer handoff after a path has been chosen. UC-045 prioritizes downloads during one contact. UC-124 decides which bearer or fallback path should carry a particular transfer.

## Research / implementation signal

Recent standards and 2026 IoT work continue to treat multiple network paths and radios as a selection problem. PollicinoNet should measure its own field behavior rather than inherit external performance numbers.

References:

- https://www.rfc-editor.org/rfc/rfc9623.html
- https://www.rfc-editor.org/rfc/rfc9897.html
- https://doi.org/10.1007/s12083-026-02251-5
- https://doi.org/10.3390/s26103158
