# UC-020 — Trusted Time Checkpoint Ferry

## Idea

Distribute small **signed time checkpoints** to isolated nodes that may lack GNSS, Internet or a permanently reachable time server. The goal is not precise radio time synchronization: it is to give applications a safer notion of freshness for TTLs, expiries, logs, leases and signed messages when connectivity is intermittent.

A checkpoint can bind an authority identity, issuance time, monotonic sequence/epoch, validity policy and signature. Nodes combine that evidence with their local monotonic clock and explicitly track uncertainty/staleness.

## Problem solved

Many PollicinoNet use cases depend on statements such as:

- "this bulletin is still valid";
- "this mission expired";
- "this trust update is newer";
- "this reservation is stale";
- "this sensor sample belongs to this time window".

An isolated low-cost node can have clock drift, a reset RTC or no trustworthy wall-clock source. Simply carrying a timestamp through a data mule does not magically reveal the exact current time because transport delay may be unknown. The system therefore needs **bounded, inspectable time evidence**, not fake precision.

## Actors / nodes

- trusted time-source/authority node, potentially disciplined by GNSS/NTP or a trusted RTC;
- school/server gateway issuing signed checkpoints;
- isolated sensors/robots/relay nodes;
- student data-mule nodes carrying checkpoints;
- applications consuming freshness/expiry decisions.

## Why PollicinoNet fits

Time checkpoints are tiny, exact and useful even when delayed. PollicinoNet can distribute checkpoint IDs, epochs and signatures over LoRa and store them while disconnected. `EXACT` is required because time evidence and signatures must not be semantically reconstructed.

This is deliberately an **application-layer freshness service**. It does not alter LoRa timing, MAC behavior or the frozen PHY, and it must not be described as precise LoRa synchronization without dedicated measurements.

## Possible bearers

- **LoRa:** signed checkpoint/epoch, freshness metadata, requests for newer checkpoints;
- **BLE/Wi-Fi/LAN:** full audit history or richer time-attestation data;
- **Internet:** authority obtains external time when available;
- **physical transport:** a moving relay ferries checkpoint updates to isolated nodes.

## What we can test now in software

- simulate nodes with configurable oscillator drift, reboots and missing RTC state;
- issue signed checkpoints with monotonic sequence numbers;
- deliver checkpoints with unknown and variable delays;
- distinguish `trusted recent checkpoint`, `stale checkpoint`, `time unknown` and `clock inconsistent` states;
- test replay of old but correctly signed checkpoints;
- test local monotonic-clock rollback/reset after reboot;
- verify that TTL/expiry decisions widen or fail safely when time uncertainty grows;
- compare applications that require exact wall-clock time with those that only need ordering/freshness;
- measure simulated error bounds and stale-time duration without turning those into physical claims.

A key invariant is:

> a delayed signed checkpoint may prove that time has advanced past a known point, but must not be treated as proof of an exact current wall-clock value unless the delay/error assumptions are independently justified.

## What requires real hardware

- several boards with their actual local clocks/RTCs logged over hours or days;
- controlled reboot/power-loss tests;
- checkpoint propagation through one or more real relay contacts;
- measurement of actual clock drift, receive delay and uncertainty growth;
- comparison with a trusted reference clock.

Only these measurements can support statements about achievable timing accuracy on the chosen hardware.

## Messina teaching scenario

Place one trusted time-authority node at school and isolate one or more student sensor nodes from Internet access. A relay carries signed checkpoints between groups. Students can then observe the difference between:

```text
"I know checkpoint 52 is newer than checkpoint 51"
```

and:

```text
"I know the current UTC time to within X ms"
```

The first can often be demonstrated safely before the second. That distinction is the main educational value of the experiment.

## Privacy / security

Time is security-sensitive because replay, certificate validity, reservation expiry and log ordering can depend on it. Checkpoints require authenticated origin, anti-replay, monotonic sequencing and explicit trust roots. A malicious node must not be able to move peers backwards in time by replaying an older checkpoint.

Do not expose stable student identifiers merely to distribute time. Avoid allowing one untrusted relay to become a time authority; the relay transports signed evidence but does not create it.

## Difficulty

**Medium–High.** The message format is small. The conceptual challenge is resisting false precision and propagating uncertainty correctly across delay, reboot and clock drift.

## Research signal

Time synchronization and timestamp compensation over LoRa/LoRaWAN remain active topics. A 2026 study evaluates LoRaWAN frame timestamping and beacon-based synchronization, while current LoRa Alliance guidance stresses periodic validation of network time. Those works motivate careful measurement, but PollicinoNet's checkpoint experiment is intentionally narrower and does not inherit LoRaWAN synchronization results.