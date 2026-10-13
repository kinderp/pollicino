# UC-198 — Expiring Offline Actuation Intent with Safe Default

## Problem to solve
A signed command to run a motor/valve may arrive long after its useful interval. Authentication alone does not establish that an action is safe to execute now.

## Actors and practical Messina scenario
Teacher operator, 4–6 student relays, lab LED or low-voltage servo, local safety cutoff and school reviewer. No public water controls, real emergency equipment or unsupervised mobile machines.

## Why PollicinoNet fits
Intent includes command ID, authority, monotonic epoch, expiry, maximum duration, expected state hash, allowed effect and clock-quality requirement. Unknown clock validity or stale state means reject/quarantine, not execute.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: tiny signed intent and outcome; BLE: technician check; Wi-Fi: diagnostic log; Internet: optional authorization; physical: manual reset. Frozen PHY unchanged.

## What can be tested immediately in software (proposed, not executed)
Deterministic actuator simulator with delayed, duplicated and reordered commands; stale state, drift, replay, reboot and lost receipt. Invariants: no effect after proven expiry, no duplicate effect, unknown time fails closed, physical override wins.

## Physical hardware and required measurements
4–6 boards with LED/low-voltage servo and physical disconnect. Intentionally delay commands and cycle power; measure command arrival, gated decisions and effect count. Retain independent mechanical/electrical cutoff.

## Privacy, security and implementation difficulty
MEDIUM–HIGH. Signed narrow authority, anti-replay, fenced epoch, bounded duration and local fail-safe. Not for life-critical actuation or unattended robots.

## Difference from existing use cases
UC-026 action tickets, UC-133 ownership fencing and UC-175 idempotence exist; UC-198 tests *time validity and safe default* even for correctly authenticated action tickets.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
