# UC-113 — Sensor Maintenance Ticket and Repair-Evidence Courier

## Idea
Let isolated sensors or field nodes create a small maintenance ticket that can travel through PollicinoNet until it reaches a person or service point able to act, then return a repair/inspection result later. The frozen LoRa PHY is unchanged.

## Problem solved
A rural or school sensor can stay reachable only intermittently. A fault such as low battery, dirty probe, calibration due, enclosure open or repeated reboot may be known locally but never reach the maintainer in time.

## Actors / nodes
Sensor node, relay/store-and-forward nodes, maintainer, optional school/lab service point, verifier.

## Why PollicinoNet fits
- **DISCOVERY:** fault class, urgency, required skill/part, coarse asset ID.
- **EXACT:** ticket ID, device ID, fault code, firmware/config version, creation time evidence, status and repair-evidence hash.
- **SEMANTIC:** human description for the maintainer.

LoRa carries ticket/status; BLE/Wi-Fi carries logs/photos; physical transport carries spare parts or the device itself.

## What we can test now in software
Simulate duplicate tickets, stale tickets, two maintainers claiming the same job, repair-before-ticket-arrival, reopen after failed repair, and offline closure. Measure time-to-assignment, duplicate work and unresolved-ticket age.

## What requires real hardware
Use 4–6 boards, one deliberately induced harmless fault such as low-battery threshold or disconnected sensor, one maintainer node and one relay. Physical tests must measure only observed delivery/latency, not infer radio range.

## Messina teaching scenario
Place a few harmless sensor nodes in school/lab locations and one remote test node in a permitted area. A fault can be relayed through normal movement until the maintenance ticket reaches school, then the closure state returns later.

## Privacy / security
Do not include personal data; authenticate status changes; bind repair evidence to the exact device/ticket; prevent an old `CLOSED` state from hiding a new occurrence.

## Difficulty
**Medium.**

## Why this is distinct
UC-062 reports crashes for debugging; UC-031 tracks calibration provenance; UC-113 manages the **maintenance workflow from fault ticket to repair evidence** across intermittent connectivity.
