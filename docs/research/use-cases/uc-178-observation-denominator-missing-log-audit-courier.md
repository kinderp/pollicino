# UC-178 — Experiment Evidence Completeness and Denominator Audit

## Problem
An experiment is biased when analysis uses only successfully returned logs. Lost logs must be counted as unknown, not silently excluded.

## Proposed experiment
Keep the declared number of planned application tests, observed application attempts, confirmed receptions and missing evidence in separate categories. An application attempt does not prove an on-air radio frame.

## Roles and bearers
Coordinator, participating lab boards, mobile relays, evidence collector. LoRa carries compact experiment IDs and receipt counts; BLE or Wi-Fi moves logs; Internet and removable media are optional alternatives.

## Software-only tests
Simulate 12 nodes and 100 test windows, with failures correlated to lost logs. Compare observed-only reporting with bounded uncertainty estimates. Inject reboots, late logs, duplicates and evidence corruption.

## Hardware tests
Run a controlled exercise with 6–10 boards at authorized educational locations. Reconcile logs after deliberate node outages. Measure real packet events only with instrumentation available above the frozen LoRa PHY.

## Data protection
Use temporary experiment IDs, minimal retained telemetry and authenticated results. No human movement data is necessary.

## Difficulty
Medium–high.

## Difference from existing cases
UC-008 observes contacts; UC-097 coordinates experiments. This case specifically measures missing evidence, the meaning of denominators and uncertainty bounds.

## Constraints
Do not alter the frozen PHY. Never infer physical reliability, energy, range or coverage from synthetic outcomes.
