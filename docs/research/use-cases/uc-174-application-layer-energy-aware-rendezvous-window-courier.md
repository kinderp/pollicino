# UC-174 — Application-Layer Energy-Aware Rendezvous Window Courier

## Problem solved
Battery-powered relay nodes cannot be assumed to expose every service continuously. UC-174 studies coarse application-layer rendezvous windows: when should a node make itself available so that useful intermittent contacts are captured without keeping every rich-bearer service active all the time?

## Actors / nodes
Student relay boards, fixed school/public checkpoints, mobile carriers and an optional measurement collector.

## Why PollicinoNet fits
PollicinoNet already models recurring contacts, future-contact reservations and clock uncertainty. Small availability metadata can travel as control state, while BLE or Wi-Fi can be enabled only during useful transfer windows. This use case stays above the frozen LoRa PHY/MAC.

## Bearers
- LoRa: coarse availability window, wake epoch, tolerance and rendezvous status.
- BLE/Wi-Fi: bulk transfer during an agreed short window.
- Internet: optional configuration distribution.
- Physical transport: fallback when no radio rendezvous completes.

## Software test now
Replay synthetic or UC-008 contact traces and compare always-available, fixed periodic windows, schedule-informed windows and adaptive windows based only on previous public/checkpoint contacts. Inject clock drift, late contacts, schedule changes and reboot.

Metrics: useful contacts captured, application awake-time, missed-contact rate, fairness across flows and sensitivity to clock error.

## Real hardware
Use 6–10 boards and 2–3 fixed public/school checkpoints. Run the same contact script under always-on and rendezvous-window policies. Any energy claim requires actual current or energy measurement; awake-time alone is only a proxy.

## Messina / provincial teaching scenario
A school checkpoint exposes broad public arrival/departure rendezvous windows rather than tracking individual student routines. Student-carried relays can attempt a short control exchange and then use BLE/Wi-Fi for bulk transfer when available.

## Privacy / security
Use only coarse public/school windows, avoid per-student schedules, use pseudonymous experiment identifiers, authenticate schedule changes and bound remote requests that extend availability.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-074 adapts sensor sampling/duty cycle; UC-025 exploits scheduled mobility; UC-128 reserves future-contact capacity; UC-143 models liveness; UC-169 chooses forwarding based on encounters. UC-174 focuses on application availability and rendezvous timing for energy-constrained relay nodes.

## Validation boundary
Simulation can compare policies. Real boards are required before claiming reduced energy use, improved delivery probability or acceptable rendezvous timing.