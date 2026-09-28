# UC-128 — Future Contact Capacity Reservation and Transfer-Appointment Courier

## Idea

Reserve a bounded amount of a **future expected contact window** for one or more transfers before the nodes physically meet.

Instead of every queued object competing at encounter time, a node can advertise or negotiate a small appointment such as:

```text
contact_window = school-bus-stop-07:45..07:50
reserved_bytes = 20 MiB
priority = course-pack
deadline = 09:00
```

The reservation is advisory and must degrade safely when the expected contact does not happen.

## Problem solved

A real student network can develop predictable encounters: arrival at school, bus stops, lab sessions, sports activities or recurring commuting corridors.

UC-025 already exploits recurring contacts. UC-128 adds a capacity-planning question:

> if several objects are waiting for the same short future contact, which ones should be admitted before the contact begins?

Without this, large opportunistic transfers can crowd out smaller deadline-bound ones and setup time can be wasted deciding what to send only after the rich bearer is available.

## Actors / nodes

Producer/requester, student relay/data mule, expected peer or school gateway, optional contact-plan coordinator and optional UC-008/UC-025 observatory.

## Why PollicinoNet fits

A reservation is tiny: contact/window ID, bytes estimate, object hash or class, deadline, priority, reservation expiry and status. The actual payload remains on BLE/Wi-Fi/LAN or physical media.

LoRa can carry reservation/control state well before the rich-bearer meeting.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: reservation request, accept/reject, capacity summary, expiry and compact queue state.
- BLE: nearby confirmation just before the contact.
- Wi-Fi/LAN: bulk transfer during the reserved window.
- Internet: optional coordinator fast path.
- Physical transport: the same reservation can describe handoff to a laptop/SSD carried by a student.

## What we can test now in software

Replay synthetic and UC-008-style contact schedules and compare:

1. no reservation, first-come-first-served;
2. deadline-first;
3. small-job-first;
4. fair-share;
5. reservation with overbooking factor;
6. reservation plus UC-108 queue pressure.

Inject missed contacts, late arrival, shorter-than-expected windows, oversized objects, duplicate reservations, cancellation and a higher-priority late request.

Measure logical metrics such as admitted bytes, missed deadlines, unused reserved capacity, overbooking and starvation. No radio-performance claim is needed for the software phase.

## What requires real hardware

Use 6–10 boards and at least one laptop/Pi acting as a rich-bearer gateway.

Script two short physical meeting windows with the same backlog. Compare a baseline policy with a reservation policy. Measure the actual usable transfer interval and bytes completed.

Do not infer capacity from simulation; the physical trial must measure setup time and completed bytes.

## Messina teaching scenario

Students around Messina, Villafranca, Rometta/Venetico and Spadafora can nominate a few recurring **public/school checkpoints** rather than home locations.

A school node knows that one relay is expected near a checkpoint for a few minutes. Before that meeting, small reservation records circulate through PollicinoNet. When the relay arrives, the Wi-Fi handoff already has a bounded transfer plan.

This makes scheduled human mobility experimentally useful without turning the project into continuous student tracking.

## Privacy / security

Use coarse checkpoint IDs and experiment-scoped pseudonyms. Do not publish home addresses or detailed commuting histories. Reservations must expire, be cancellable, respect UC-095 volunteer budgets and never imply that a student is obligated to appear. Limit reservation spam and do not reveal private object names in clear metadata.

## Difficulty

Medium-high. Basic reservation is easy; useful admission under uncertainty, overbooking and fairness is the interesting part.

## Why this is distinct

UC-025 models recurring mobility; UC-045 prioritizes collection during an already-active short contact; UC-073 chooses a courier/checkpoint route; UC-108 exposes current queue pressure; UC-124 chooses the bearer. UC-128 allocates **future expected contact capacity before the encounter**.

## Research / implementation signal

DTN architecture explicitly recognizes scheduled contacts with known time windows, duration and possible capacity. A current 2026 DTN peering Internet-Draft also continues to include scheduled contact windows as a routing concern. PollicinoNet can explore a human-scale version using measured student-network contacts.

References:

- https://datatracker.ietf.org/doc/html/rfc4838
- https://datatracker.ietf.org/doc/draft-taylor-dtn-dpp/
