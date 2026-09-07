# UC-025 — Scheduled Mobility Backbone

## Idea

Use **predictable recurring movement** as part of the network plan. Instead of treating every encounter as completely random, PollicinoNet can learn or ingest a coarse schedule and predict that certain relay opportunities are likely to recur: school commute, train stops, bus routes, ferry crossings or repeated student routes.

The first experiments should use synthetic/public schedules and controlled student routes. Mounting hardware on public transport is a later step requiring explicit permission.

## Problem solved

In a sparse network, an object may eventually arrive through ordinary opportunistic forwarding, but the system has no idea whether waiting for a specific future contact is better than copying data to many peers.

When movement is partially predictable, we can ask a stronger question:

> can a contact plan reduce delay, duplicate copies or queue pressure compared with routing that ignores the schedule?

The answer must be measured, not assumed.

## Actors / nodes

- school/classroom anchor nodes;
- student relay/store-and-forward nodes following controlled recurring routes;
- optional bus/train/ferry emulator;
- later, authorized vehicle/public-transport relay;
- content/request sources and destinations;
- optional route/timetable data source.

## Why PollicinoNet fits

PollicinoNet already treats mobility as a valid bearer: a device can physically carry queued state until a later contact. This use case adds a **contact-plan layer** above that primitive.

- **DISCOVERY:** route/contact opportunity, next coarse rendezvous window and queue summary;
- **EXACT:** object/chunk/message IDs to carry;
- **SEMANTIC:** optional route class such as `school-commute`, not a claim about an individual's exact location.

LoRa can exchange compact queue/contact metadata at rendezvous points. Richer bearers move bulk content during the contact window.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** node discovery, queue summary, bundle/object IDs, coarse contact-plan metadata;
- **BLE/Wi-Fi:** bulk synchronization during a stop/contact;
- **Internet:** optional timetable ingestion or gateway fast path;
- **physical transport:** walking, bicycle, train, bus, ferry or vehicle carries the stored bytes.

## What we can test now in software

- define a `ContactPlan` with coarse zones and uncertain time windows;
- import synthetic timetables or public timetable data without tying them to student identities;
- simulate recurring routes plus realistic delay/missed-contact noise;
- compare schedule-aware forwarding with naive epidemic/spray-and-wait/single-copy baselines;
- test whether a node should hold an object for a high-probability future contact or hand it to an earlier low-value relay;
- model limited storage and transfer-rate windows;
- recompute plans when a trip is delayed/cancelled;
- combine scheduled contacts with opportunistic unscheduled student encounters;
- replay real UC-008 contact traces and identify repeatable windows without storing precise home trajectories;
- measure delivery delay, duplicate bytes, queue occupancy, missed-contact penalty and Age of Information.

A key rule is:

> the schedule is a prediction, never proof that a contact occurred; physical delivery is only credited from observed contact/transfer evidence.

## What requires real hardware

- repeated 3+ node experiments on the same controlled route at different times;
- measured contact start/end, packet delivery and transfer volume;
- deliberate missed/delayed contacts;
- comparison against a routing baseline on the same measured movement;
- public-transport deployment only after operator permission, safe mounting/power design and legal review.

## Messina teaching scenario

The Tyrrhenian corridor is unusually suitable for a teaching experiment because places already discussed for the network — Messina, Villafranca Tirrena, Rometta Marea, Spadafora, Milazzo and farther west — lie along recurring road/rail mobility.

A safe first scenario does **not** place radios on trains. Students emulate three recurring "services" along controlled school/lab routes. The simulator receives a rough timetable, chooses which relay should carry which object, and the real boards then reveal whether predicted contacts actually happen.

A later research exercise could compare public rail timetable windows with observed station-area contacts. RFI notices in September 2026 list regional services on the Messina–Palermo line stopping through Villafranca Tirrena, Rometta Messinese, Spadafora and Milazzo, which makes this corridor a concrete scheduling example; those published times are planning inputs, not guaranteed radio contacts.

## Privacy / security

Predictable mobility can become tracking if implemented carelessly. Do not store student home routes, exact continuous GPS traces or identity-linked commuting patterns. Use synthetic routes, public vehicle schedules, coarse zones and rotating node identifiers where possible.

Contact plans must not grant authority: knowing that a relay will probably visit a zone does not mean it may read the content it carries. Sensitive payloads remain encrypted and policy-bound.

## Difficulty

**Medium–High.** The radio protocol barely changes; the challenge is uncertainty-aware planning, privacy and proving that schedule awareness actually improves a measured metric.

## Research signal

Recent DTN work explicitly studies public transportation as a data-mule substrate and models random travel/contact duration plus Age of Information. This makes scheduled/semischeduled mobility a strong research direction for PollicinoNet, especially because we can compare predictions against the real contact graph collected by UC-008.

References:

- https://arxiv.org/abs/2512.01829
- https://www.rfi.it/it/news-e-media/infomobilita/avvisi/2026/9/13/linee-siracusa---messina-c-le--messina-c-le---palermo-c-le-.html
