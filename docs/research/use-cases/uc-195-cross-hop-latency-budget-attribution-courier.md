# UC-195 — Cross-Hop Delay Budget Attribution Courier

## Problem to solve
A bundle arrives six hours late: was it waiting for a person-carried relay, queued on a node, negotiating Wi-Fi/BLE, or retransmitting? End-to-end timestamps alone cannot reveal the bottleneck.

## Actors and practical Messina scenario
6–10 LoRa test boards, two or three authorized school checkpoints around Messina–Villafranca–Rometta, companion computers, evidence collector and teacher.

## Why PollicinoNet fits
Relays store bounded events for queued, contact opened, bearer ready, verified bytes, handed off and receipt seen. Local monotonic intervals and clock uncertainty prevent fake cross-node precision.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: phase-summary hashes; BLE/Wi-Fi: test data and signed traces; Internet: optional dashboard; physical media: raw evidence packs.

## What can be tested immediately in software (proposed, not executed)
Generate exact ground-truth delay budgets; inject skewed clocks, missing phase records, duplication, reordering and incomplete links. Emit bounded intervals or UNKNOWN. Evaluate incorrect-bottleneck rate, unattributed fraction and byte overhead.

## Physical hardware and required measurements
6–10 boards and 2–3 fixed test stations with known-size objects; log actual queue/contact/setup/transfer/verification times, verified bytes and receipt time. Distinguish observed time from inferred intervals.

## Privacy, security and implementation difficulty
MEDIUM–HIGH. Test IDs, no individual commute reconstruction, authenticated records, short retention and reported clock quality.

## Difference from existing use cases
UC-008 measures opportunities, UC-123 clock error, UC-173 reachability, UC-188 payload feasibility; UC-195 explains where observed end-to-end time was spent.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
