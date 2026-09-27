# UC-123 — Opportunistic Clock Offset/Drift Calibration Ferry

## Idea

Let PollicinoNet nodes estimate and exchange coarse relative clock offset, drift and time-quality evidence when they meet, then carry that calibration evidence through the network.

This is not a claim of precise radio synchronization and it does not change the frozen LoRa PHY. The first goal is to improve the quality of timestamps used by contact traces, sensor correlation and event reconstruction while preserving explicit uncertainty.

## Problem solved

Low-cost boards can disagree about time because of oscillator drift, reboot, RTC loss, sleep and long periods without GNSS/NTP. That can make the same encounter appear at different times, misalign sensor events, confuse causal reconstruction, and hide uncertainty after reboot.

The useful question is not only "what time does node A report?" but "how uncertain is A relative to B or to a trusted anchor, and how quickly is that uncertainty growing?"

## Actors / nodes

- PollicinoNet student boards with local clocks;
- optional trusted anchor with GNSS/NTP/good RTC;
- student relay/store-and-forward nodes;
- school collector/analysis host;
- sensor/robot applications consuming time-quality metadata.

## Why PollicinoNet fits

Clock-calibration records are tiny and survive long partitions.

- DISCOVERY: peer supports calibration profile/version and has a current time-quality class.
- EXACT: local monotonic counters, exchange IDs, offset/drift estimate, uncertainty bound, reference identity and calibration epoch.
- SEMANTIC: labels such as GOOD / DEGRADED / UNKNOWN, never a substitute for the numeric estimate and provenance.

LoRa can carry coarse calibration probes and compact results. BLE/Wi-Fi can run richer repeated timestamp exchanges when peers are nearby. An Internet/GNSS anchor is optional rather than required for every node.

## Possible bearers

- LoRa: coarse timestamp exchange, calibration epoch, offset/drift summary and uncertainty class;
- BLE: repeated short-range exchanges for better local estimation;
- Wi-Fi/LAN: richer calibration bursts and trace upload;
- Internet/GNSS: optional authoritative anchor;
- physical transport: carry trace/calibration evidence between disconnected islands.

## What we can test now in software

Simulate clocks with fixed offset, positive/negative drift, reboot, asymmetric message delay, outliers and stale calibration records. Fit a simple affine relation such as t_B ~= a*t_A + b and track confidence/uncertainty.

Compare raw local timestamps, offset-only correction, offset+drift correction, and uncertainty-aware correction. Include disconnected groups with no common anchor and a later trusted anchor encounter.

Useful software metrics include timestamp residual error against synthetic truth, uncertainty calibration, false event-order inversions and how often the system must return TIME_UNCERTAIN.

A key invariant is: no algorithm may convert an unmeasured variable-delay radio exchange into a claim of sub-millisecond synchronization.

## What requires real hardware

Start with 4–6 boards and one reference clock/logger. Run repeated controlled encounters over hours and after deliberate reboot/sleep. Record the real local clocks and compare estimated offset/drift with the reference.

Any accuracy number must come from measurements on the actual boards and bearers.

## Messina teaching scenario

Use nodes in controlled checkpoints across Messina, Villafranca, Rometta/Venetico and Spadafora. Each group keeps its own local clock. Student relays periodically meet another group and exchange compact calibration records.

At school, students compare the raw encounter timeline, the corrected timeline and the uncertainty that remains.

## Privacy / security

- use rotating/pseudonymous experiment identities;
- do not attach calibration records to student names or home addresses;
- authenticate calibration evidence where it affects trust decisions;
- reject old calibration epochs;
- preserve reboot/reset provenance;
- treat peer-derived time as evidence, not authority;
- avoid exposing high-resolution encounter timing longer than the experiment needs.

## Difficulty

High. The arithmetic is simple; robust uncertainty accounting under delay asymmetry, reboot and stale evidence is the hard part.

## Why this is distinct

- UC-020 ferries signed checkpoints from a trusted time authority.
- UC-093 reconstructs causal ordering from distributed events.
- UC-123 estimates relative clock offset/drift quality between intermittently meeting nodes and can feed both.

## Research / implementation signal

Clock offset/skew estimation and multi-protocol wireless synchronization remain active research areas in 2026. Those results motivate the experiment but do not predict PollicinoNet accuracy.

References:

- https://doi.org/10.1109/TCOMM.2026.3653119
- https://arxiv.org/abs/2604.07199
- https://arxiv.org/abs/2601.23147
