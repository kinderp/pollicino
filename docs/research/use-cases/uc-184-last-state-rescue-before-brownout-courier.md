# UC-184 — Last-State Rescue Before Brownout Courier

## The problem
A remote battery-powered sensor can lose power before its backlog reaches a gateway. A generic “battery low” notification is insufficient: its most valuable *last measurement, calibration epoch and pending alarm state* might disappear, and a relay may not know which data to rescue first.

## Actors and Messina experiment
A school-owned environmental sensor in a safe demonstration fixture, an energy monitor/firmware application, a nearby relay or mobile student-carried board, a collector and a replacement sensor. Start at a desk, then at approved school/rural checkpoints—not at unattended hazards.

## Why PollicinoNet
The network tolerates a delayed contact and can prioritize a **small survival capsule** before a richer log export. Proposed application states are `NORMAL -> ENERGY_RISK -> RESCUE_OFFERED -> RESCUE_CONFIRMED / UNCONFIRMED -> SAFE_SLEEP / POWER_LOST`. `RESCUE_CONFIRMED` requires receiver evidence, not merely a queued send.

## Bearers
- **LoRa:** tiny bounded state capsule: device pseudonym, sample sequence/watermark, time uncertainty, sensor health, exact latest-sample hash/value when approved, remaining backlog count and energy-risk flag.
- **BLE/Wi-Fi:** time-series blocks and signed diagnostic evidence during a usable encounter.
- **Internet:** optional later backhaul.
- **Physical:** SD card or school-owned device ferried after power returns.

## Software-only test now
Simulate discharging voltage and uncertain remaining life, cyclic storage, a small emergency-write budget and intermittent contact opportunities. Compare FIFO, UC-153 freshness priority and a survival-capsule-first policy. Inject power cut *between* metadata commit and payload save, duplicate offers, corrupted checkpoints, stale timestamps and a sensor that reboots with old state. Validate crash-consistent storage with a journal or atomic record replacement; reserve writes and avoid flash-wear assumptions without data.

Metrics: last valid sample recovered, fraction of critical state recoverable, capsule bytes, recovery correctness after reboot, number of unconfirmed rescues and bounded sacrificed backlog. Software power models do **not** establish battery life.

## Hardware experiment required
Use 4–6 boards, a safe current-limited USB supply or protected bench fixture with controlled low-voltage cutoffs, and local logging. Compare recovery with and without the capsule while reproducing identical synthetic sensor workloads; measure actual current/power and whether the state survives unexpected power loss. Do not bypass battery protection, brownout safety, or modify the frozen LoRa PHY/MAC.

## Privacy/security
Avoid personal/environmental observations tied to homes. Sign/authenticate exact device and capsule epochs, protect sensitive records at rest, use pseudonyms, validate anti-replay, and enforce bounded queue preemption. A relay is not entitled to read private samples just because it carries them.

## Difficulty and distinctness
**Medium–high.** UC-074 adjusts sampling for energy; UC-079 checkpoints *computation*; UC-045 prioritizes harvesting and UC-159 preempts bulk. **UC-184 handles at-risk device state during an imminent energy loss and records whether rescue actually succeeded.**

## Acceptance gates
1. No false `RESCUE_CONFIRMED` without receiver evidence.
2. Atomic capsule survives injected power cuts.
3. Stale restored state is detectable by epoch/watermark.
4. Any energy-saving claim is backed by real measurements.
