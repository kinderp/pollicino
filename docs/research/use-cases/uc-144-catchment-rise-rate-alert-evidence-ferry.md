# UC-144 — Catchment Rise-Rate Alert and Evidence Ferry

## Idea

Use sparse rain/water-level sensors to send a **small early warning about a rapid rise or threshold crossing**, then retrieve the richer sensor history later through PollicinoNet.

This is a controlled teaching and civil-protection drill use case, not a certified flood-warning system.

## Problem solved

A stream, drainage channel or low point can change quickly while the sensor has no permanent Internet connection. Sending every measurement continuously is unnecessary and may be impossible. A compact event such as `RISING_FAST`, `LEVEL_HIGH` or `SENSOR_UNCERTAIN` can move first, while the detailed time series follows later.

## Actors / nodes

Rain or water-level sensor, local edge rule engine, student relay/store-and-forward nodes, school/lab collector, optional second witness sensor and exercise observer.

## Why PollicinoNet fits

The event capsule is small: sensor ID, calibration/provenance ID, event type, local time with uncertainty, coarse level/rate bucket, evidence hash and expiry. LoRa can carry the event quickly relative to the bulk log; BLE/Wi-Fi can move the history later.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: event capsule, acknowledgement, evidence request and compact status.
- BLE: nearby sensor maintenance or small evidence excerpt.
- Wi-Fi/LAN: full time series, plots and photos.
- Internet: optional downstream dashboard when a gateway reconnects.
- Physical transport: SD card, laptop or student-carried relay.

## What we can test now in software

Generate synthetic hydrographs and rainfall traces with known threshold crossings. Test delayed packets, reordered events, false spikes, sensor drift, missing samples, duplicate alerts, old events arriving after a clear condition and two sensors disagreeing.

Compare raw-periodic forwarding with event-first forwarding and record bytes moved, alert-capsule latency in the simulator, false/duplicate event count and evidence completeness.

## What requires real hardware

Build a harmless tabletop setup using an ultrasonic or pressure/water-level sensor, rain-gauge simulator or simply a potentiometer that produces known rising/falling patterns. Use 4–6 LoRa boards and deliberately separate the sensor from the collector.

Only after field measurements may the team discuss real contact reliability, range, PDR or latency. No physical warning performance is claimed from simulation.

## Messina teaching scenario

A school/public demonstration can emulate a drainage or catchment sensor in Rometta/Venetico while relay nodes move through Villafranca and Messina. The first object ferried is the compact rise-rate event; later contacts retrieve the detailed history for analysis.

A second sensor can act as a witness so students can study disagreement and corroboration without treating a single noisy reading as authoritative.

## Privacy / security

Use only public/school test sites or synthetic locations, avoid private-property tracking, authenticate event capsules, preserve calibration provenance and make uncertainty explicit. Exercises must be labelled `TEST/EXERCISE` and must not be presented as official public alerts.

## Difficulty

**Medium.**

## Why this is distinct

UC-003 is generic rural sensor collection. UC-027 carries post-event vibration evidence. UC-053 tasks sensors. UC-089 tracks alarm acknowledgement. UC-144 is specifically **event-first rise-rate/level monitoring with delayed evidence retrieval** for an intermittent environmental network.

## Research signal

LoRa/LoRaWAN environmental and water-monitoring systems remain active research areas. PollicinoNet's contribution to test is the event-first DTN workflow and its evidence lifecycle, not any claimed hydrological accuracy or radio coverage.

References:

- https://www.rfc-editor.org/rfc/rfc9171.html
- https://doi.org/10.65568/gujes.2026.020103
