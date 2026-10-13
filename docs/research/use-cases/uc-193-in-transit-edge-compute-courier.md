# UC-193 — In-Transit Edge Compute Courier

## Problem to solve
A mobile storage/computing host has spare CPU time between two intermittent school contacts: can it transform a large public dataset and deliver a verified compact result?

## Actors and practical Messina scenario
Source lab, consenting adult operating a Pi/laptop carrier, 4–6 LoRa relays, destination school checkpoint and teacher evaluator; begin with a simulated journey in one building.

## Why PollicinoNet fits
A signed task names the exact input hash, approved transformation, runtime digest, resource budget, deadline and result hash. Store-carry-compute-forward can be compared to raw carriage.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: compact job ID/capability/result; BLE: session start/tiny output; Wi-Fi/LAN: datasets; Internet: optional trusted verifier; physical SSD: bulk.

## What can be tested immediately in software (proposed, not executed)
Three virtual islands with public CSV and scripted contacts. Compare compute at source, raw carry and in-transit transform. Inject power loss, restart, expiry, duplicate task, hash mismatch, missed contact. Measure byte reduction, correctness and time to usable result.

## Physical hardware and required measurements
4–6 LoRa boards, a Pi/laptop and two lab checkpoints; record actual runtime, verified bytes, device load and delivery. No autonomous vehicle/drone required.

## Privacy, security and implementation difficulty
HIGH. Only public/synthetic data initially. Host opt-in, sandbox, allowlisted deterministic transformations, no arbitrary remote execution, independent output replay.

## Difference from existing use cases
UC-045 harvests data, UC-078 offloads tasks, UC-079 checkpoints work and UC-129 orchestrates jobs; UC-193 studies specifically the otherwise idle carrying interval.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
