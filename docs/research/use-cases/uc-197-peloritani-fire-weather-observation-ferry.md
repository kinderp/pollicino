# UC-197 — Peloritani Fire-Weather Observation Ferry

## Problem to solve
Fixed hill-area instruments may lose Internet. Temperature, humidity, rainfall and wind are useful for studying environmental conditions related to fire weather, but school sensors do not issue reliable wildfire predictions or alerts.

## Actors and practical Messina scenario
Two school-owned low-cost stations, reference instrument, 4–6 student relay boards and teacher data reviewer. First indoor benign temperature/humidity tests, then only authorized mounted fixed sites around the Peloritani.

## Why PollicinoNet fits
Relays ferry compact sample window, quality flags, calibration ID and latest reading before historical blocks; later reference review may revise provisional flags while retaining source provenance.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: tiny observation/quality flags; BLE: calibration; Wi-Fi: full series; Internet: optional official public weather reference; physical SD/USB: raw time series.

## What can be tested immediately in software (proposed, not executed)
Synthetic/public weather series with stuck sensors, drift, missing windows, late relay arrival and time skew. Compare latest-first vs quality-gated delivery. Metrics: reviewed coverage, false anomaly flags, staleness, correction latency, bytes.

## Physical hardware and required measurements
4–6 boards, safe tabletop sensors and reference unit, optional properly mounted weather station with consent. Measure real sensor uncertainty/contact windows; never claim fire detection or official hazard prediction.

## Privacy, security and implementation difficulty
MEDIUM. No risky field visits, active-fire operations or real public warning channels. Fixed coarse site aliases, authenticated data, teacher verification and bounded logs.

## Difference from existing use cases
UC-003 is generic rural IoT, UC-144 floods, UC-158 slopes and UC-171 coastal water quality. UC-197 is a *fire-weather-oriented observational and delayed data-quality exercise*, never an alert service.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
