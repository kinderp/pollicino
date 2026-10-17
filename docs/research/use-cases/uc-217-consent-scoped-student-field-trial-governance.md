# UC-217 — Voluntary Student Testbed Participation and Offline Stop

## Problem
A registered board is not automatically an active participant in every school experiment. The operator needs a simple local control to pause participation even while the device is disconnected.

## Roles
Teacher coordinator, laboratory supervisor, simulated volunteer roles, test boards, fixed authorized school checkpoints in Messina and Rometta, and a collector.

## PollicinoNet and bearers
Experiment-specific permit epochs and stop statuses fit a delay-tolerant network. LoRa transfers only compact experiment status; BLE/Wi-Fi transfers approved bench diagnostics; Internet is optional; USB or device return provides physical handoff. No personal routes are part of the protocol.

## Software tests
Create 10 synthetic actors, three study epochs and states `not_enrolled`, `active`, `paused`, `stopped`, `expired`. Test offline stop, reboot, delayed synchronization, old permits, duplicates and invalid signatures. A local stop immediately ends new study logging and new test transmissions. Unexpected old permits never reactivate the experiment. Retained test artifacts follow a versioned local retention rule. Distinguish an opt-out from device outage in aggregate reporting.

## Hardware tests
With 4–6 lab boards and fake identities, trigger stop while gateways are disconnected and verify restart behavior. For later school-field experiments, require institutional authorization, a privacy review and voluntary participation; avoid movement histories.

## Privacy/security and difficulty
Use minimal temporary study identifiers, short retention, signed configuration and no individual public measurements. **Difficulty: high** because human participation procedures must be reviewed independently of protocol code. Unlike UC-068 device enrollment or UC-201 hardware retirement, UC-217 manages **per-experiment active participation** and offline stop. No physical results claimed.
