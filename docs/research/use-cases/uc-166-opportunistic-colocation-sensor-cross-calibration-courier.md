# UC-166 — Opportunistic Co-Location Sensor Cross-Calibration Courier

## Problem solved
Low-cost sensors can drift, while only a few nodes can periodically reach a trusted reference device. A short co-location can create useful calibration evidence that is later ferried to disconnected sensor nodes.

## Actors / nodes
Low-cost sensors, trusted reference sensor or reference kit, optional mobile carrier, relay/store-and-forward nodes, calibration worker and collector.

## Why PollicinoNet fits
Reference identity, overlap window, coefficient/version, uncertainty and provenance are compact. LoRa can announce calibration opportunities and carry compact results; raw overlap windows can wait for BLE/Wi-Fi or physical retrieval. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: calibration opportunity, reference ID, coefficient/version and uncertainty.
- BLE: direct local comparison during co-location.
- Wi-Fi/LAN: raw overlapping time series and calibration report.
- Internet: optional reference database.
- Physical transport: moving the reference kit.

## Software test now
Generate synthetic sensors with known offset, gain error and slow drift. Compare no recalibration, one global correction, trusted co-location calibration and uncertainty-aware transfer. Inject stale coefficients, insufficient overlap and conflicting reference sessions.

## Real hardware
Start with 3–5 inexpensive temperature/humidity sensors plus one designated reference device in a controlled indoor setup. Move the reference between nodes, collect overlap windows and verify whether the software consistently detects offset or drift.

## Messina scenario
A portable reference kit can visit different school/public checkpoints while student relays return compact calibration evidence to sensors that lack permanent connectivity.

## Privacy / security
Use authorized test locations and avoid retaining fine movement history. Authenticate the reference identity and keep calibration provenance and uncertainty explicit.

## Difficulty
**Medium.**

## Distinct from existing cases
UC-031 preserves calibration provenance, UC-022 corroborates events and UC-037 collects mobile environmental transects. UC-166 creates new calibration evidence from opportunistic co-location with a reference.

## Research signal
Calibration transfer for low-cost environmental sensors remains an active 2026 topic, especially when only a subset of sensors can be co-located with reference-grade instruments. External accuracy values are not PollicinoNet claims.
