# UC-TIME-001 — Signed time-anchor and clock-drift ferry

Status: RESEARCH / INFRASTRUCTURE PROTOTYPE

## Problem

A disruption-tolerant network still needs a defensible notion of time. Pollicino uses time for TTL/expiration, application usefulness deadlines, freshness, encounter history, logs and security-generation validity. Student-carried nodes may reboot, sleep for long periods or spend hours without Internet/NTP/GNSS.

The goal is not sub-millisecond synchronization. The goal is a bounded, auditable estimate such as “this node's current time is within ±N seconds of signed anchor generation G”, with explicit uncertainty that grows while disconnected.

An authoritative school/home gateway can issue signed time anchors. Nodes can carry and forward those anchors, plus local drift evidence, across disconnected clusters.

## Actors / nodes

- school time-authority gateway;
- optional trusted home/Internet gateway;
- student-carried Pollicino nodes;
- fixed sensors/relays;
- simulator/evidence collector.

## Messina educational scenario

At school, nodes refresh an authenticated time anchor. During the afternoon they operate disconnected and may exchange newer anchors opportunistically. The next morning the school gateway measures accumulated offset/drift and can evaluate whether each node stayed within an allowed uncertainty budget.

```text
school authority -> signed anchor G42
       |                 |
       v                 v
 student A           student B
       |                 |
       +--- carry / opportunistic exchange ---+
                                             |
                                             v
                                      disconnected sensors
```

No peer is automatically trusted as a new time authority merely because it has a fresher local clock.

## Why PollicinoNet fits

The anchor is tiny, cacheable, versioned and delay-tolerant. Pollicino can provide:

- exact object identity;
- store-carry-forward;
- signed generation/freshness state;
- anti-replay rules;
- bounded propagation across multiple bearers;
- explicit evidence labels.

This use case also improves the quality of future TRACE, sensor and deadline experiments because their timestamps can carry a known uncertainty rather than pretending every node has perfect time.

## Possible bearers

- LoRa for compact signed anchors and uncertainty summaries;
- BLE for local refresh/exchange;
- Wi-Fi/LAN for direct authoritative refresh;
- Internet/NTP/GNSS only at trusted gateway endpoints if chosen by the deployment;
- physical movement as the carry mechanism.

## What can be tested now in software

Without boards we can model:

1. independent clock offset and ppm drift per node;
2. sleep/reboot events;
3. signed anchor generations;
4. stale-anchor propagation;
5. monotonic anti-rollback rules;
6. uncertainty growth while disconnected;
7. comparison of strict absolute timestamps versus uncertainty intervals;
8. impact of clock error on TTL, deadline and encounter-history decisions;
9. malicious or faulty peer proposing an older or implausible time.

The key software gate is whether downstream logic can remain fail-closed when time uncertainty becomes too large.

## What requires real hardware

Boards are required before claiming:

- actual oscillator/RTC drift;
- drift while deep-sleeping;
- reboot persistence behavior;
- temperature effects on clock drift;
- real signature-verification cost and energy;
- achievable time uncertainty after real LoRa/BLE/Wi-Fi contacts.

HW-006 still comes first for RF claims; a separate clock campaign can then measure real drift over hours/days.

## Privacy / security

Requirements:

- only designated authorities sign authoritative anchors;
- monotonic generation counters and anti-rollback;
- explicit uncertainty/error bound, never hidden “perfect time” assumptions;
- reject anchors outside configured plausibility bounds unless manual recovery is invoked;
- isolate time authority keys from ordinary routing identity keys where practical;
- do not infer a student's location from when/where an anchor was refreshed.

## Implementation difficulty

**Medium-high.** The wire payload is simple. Correct recovery, uncertainty propagation and interactions with TTL/security state require careful design.

## Minimal measurable hypotheses

- H1: signed anchor ferrying keeps most disconnected nodes within a useful coarse time bound without continuous Internet.
- H2: explicit uncertainty prevents incorrect TTL/deadline conclusions that would arise from assuming synchronized clocks.
- H3: generation-based anti-rollback blocks stale time-anchor replay across partitions.

## Metrics

- estimated versus true simulated clock error;
- uncertainty width over disconnection time;
- stale anchors rejected;
- TTL/deadline misclassification count;
- bytes of time-control traffic;
- refresh latency by cohort;
- nodes exceeding configured uncertainty budget.

## Gate decision

**RESEARCH / PROTOTYPE.** Not a flashy application, but it is potentially foundational for trustworthy real traces, deadlines and security-state convergence.

## Related standards/research precedent

RFC 4838 explicitly notes that DTN architecture depends on time synchronization for bundle identification, scheduled/predicted contacts and expiration computations: https://www.rfc-editor.org/rfc/rfc4838.html .

An IETF problem statement specifically addressed time synchronization in intermittently connected DTNs: https://datatracker.ietf.org/doc/html/draft-templin-dtntsync-00 .
