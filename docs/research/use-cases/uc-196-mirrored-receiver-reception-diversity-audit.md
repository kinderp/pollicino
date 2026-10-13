# UC-196 — Mirrored Receiver Reception Diversity Audit

## Problem to solve
When receiver A misses a test frame, was it never transmitted, lost at A, heard by B or merely absent from A's collected log? A second fixed receiver separates some of these hypotheses without changing radio firmware.

## Actors and practical Messina scenario
One fixed test sender, two independent receivers at authorized checkpoints, 4–6 relay boards, school collector and teacher; start in one school lab, then controlled public-school sites in the Milazzo–Rometta corridor.

## Why PollicinoNet fits
An authenticated trial/sequence sender ledger and independent receiver observed-sequence sets move by store-and-forward. The result distinguishes verified transmitted, heard at A, B, both, unknown sender and missing observation logs. Reception at a relay is not end-to-end bundle delivery.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: existing application test frames and compact sequence summaries; BLE/Wi-Fi: raw receiver logs; Internet: optional school collector; physical SD/USB: immutable evidence.

## What can be tested immediately in software (proposed, not executed)
Simulate 200 known trial frames, independent and correlated losses, missing sender evidence, receiver reboot, delayed logs and duplicate packets. Compare A, B and union only against actual known transmissions; metrics include union gain, unclassifiable trials and correlated loss.

## Physical hardware and required measurements
1 sender, 2 independent fixed receivers and 4–6 relays; controlled known-position trials with existing firmware. Record actual logged transmissions, reception and RSSI/SNR if available; replicate trials before reporting PDR. No PHY edits.

## Privacy, security and implementation difficulty
MEDIUM–HIGH. No passive interception of others, RF localization of students or personal routes. Authenticate trial records, short retention and explicit unknown denominators; check radio rules.

## Difference from existing use cases
UC-008 observes contacts, UC-063 RF environment, UC-178 missing experiment logs and UC-188 end-to-end payload feasibility. UC-196 measures *independently witnessed reception of the same verified test emission*.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
