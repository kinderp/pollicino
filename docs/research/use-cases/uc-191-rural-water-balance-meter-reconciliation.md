# UC-191 — Rural Water-Balance Discrepancy Reconciliation

## Problem to solve
Two cheap meters upstream/downstream of a classroom water loop arrive at different times. A raw difference may reflect clock drift, missing samples, counter rollover or calibration bias rather than water loss.

## Actors and practical Messina scenario
Two or three low-voltage flow sensors, 4–6 student LoRa relays, teacher, Raspberry Pi collector, volume reference; first a school bench, then optionally an authorized agricultural teaching site near Venetico.

## Why PollicinoNet fits
An interval ID, cumulative volume, calibration epoch and explicit time uncertainty survive store-and-forward. Output BALANCED, POSSIBLE_DISCREPANCY or INSUFFICIENT_EVIDENCE; never announce a real leak.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: counter/interval summary; BLE: inspection; Wi-Fi/LAN: full series; Internet: optional school dashboard; physical USB/SD: complete history.

## What can be tested immediately in software (proposed, not executed)
Synthetic known-volume streams; inject asynchronous clocks, sensor bias, rollover, duplicates and missing blocks. Compare naive subtraction to aligned uncertainty-bounded balances. Metrics: false discrepancy rate, unknown intervals, convergence delay, useful bytes.

## Physical hardware and required measurements
A safely contained manual water rig, measured reference volume, two flow sensors and 4–6 boards. Physically separate electronics from water; measure instrument error and actual delivery; no domestic/public pipeline installation.

## Privacy, security and implementation difficulty
MEDIUM. No household water-use profiling, names or fine home coordinates. Authenticate interval/calibration evidence; missing reading is not zero flow.

## Difference from existing use cases
Unlike UC-146 water allocation, UC-171 water quality, UC-125 stream joins and UC-131 missing-block repair, this tests conservation accounting from delayed meters.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
