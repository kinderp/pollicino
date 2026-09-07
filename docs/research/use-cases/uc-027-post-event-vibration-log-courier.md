# UC-027 — Post-Event Vibration / Structural Log Courier

## Idea

Let isolated accelerometer/vibration nodes keep high-rate local evidence, announce only a **compact event summary** over the scarce bearer, and retrieve the exact waveform later through a student/data-mule or richer local link.

This is a post-event evidence and teaching scenario, **not earthquake early warning** and not a structural-safety certification system.

## Problem solved

Vibration/accelerometer data can be sampled much faster than is sensible to stream continuously over LoRa. Yet short high-rate windows may be useful after a controlled event: a vibration on a model structure, machine movement, impact or synthetic seismic waveform.

A node can therefore retain the raw window locally and send only:

```text
event ID
coarse time/epoch + uncertainty
peak/summary values
evidence hash
priority
```

A later contact retrieves the exact waveform if it is worth analysing.

## Actors / nodes

- stationary accelerometer/vibration sensor nodes;
- student relay/store-and-forward nodes;
- optional edge-AI/event classifier;
- school/lab analysis node;
- optional mobile robot/vehicle acting as evidence collector;
- human reviewer.

## Why PollicinoNet fits

The scenario maps naturally onto the three information contracts:

- **DISCOVERY:** "sensor X has event window E in coarse zone/time";
- **EXACT:** raw waveform/object hash, sensor configuration, calibration metadata and immutable event record;
- **SEMANTIC:** `impact`, `abnormal_vibration`, `test_waveform`, etc., kept separate from the exact evidence.

LoRa carries the compact event announcement. BLE/Wi-Fi/LAN or physical carry retrieves the high-rate waveform later.

Store-and-forward matters because the sensor may have no permanent backhaul and the evidence collector may visit only occasionally.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** event ID, time uncertainty, peak/summary metrics, sensor/config version, evidence hash and priority;
- **BLE:** nearby raw-window retrieval and maintenance/configuration;
- **Wi-Fi/LAN:** bulk waveform retrieval and analysis;
- **Internet:** optional upload after the data reaches a gateway;
- **physical transport:** student/robot/vehicle carries exact event windows from isolated sensors.

## What we can test now in software

- generate synthetic accelerometer waveforms with ordinary noise plus controlled events;
- define deterministic trigger/pre-trigger/post-trigger windows;
- package each raw window as an exact content-addressed object;
- emit a compact signed `VibrationEventSummary` referencing the exact evidence hash;
- simulate sensor storage limits and priority-based retention;
- retrieve selected evidence later through UC-024-style content needs;
- correlate multiple sensors through UC-022 without merging away their independent provenance;
- inject wrong sensor config/calibration IDs and reject incompatible comparisons;
- model UC-020 time uncertainty when correlating event windows;
- compare "stream everything" against "summary now, exact evidence later" by bytes moved, evidence availability and retrieval delay;
- test missing/corrupted event windows and exact hash failure.

A core invariant is:

> the compact event summary is an index into evidence, not a substitute for the evidence.

## What requires real hardware

- 2–3 inexpensive accelerometer/IMU nodes;
- controlled repeatable vibration/impact source on a harmless test object or bench;
- local high-rate storage sufficient for short event windows;
- real LoRa event-announcement measurements;
- later BLE/Wi-Fi/physical retrieval of exact waveforms;
- calibration/configuration recording for every sensor used in comparisons.

Claims about buildings, landslides, earthquakes or infrastructure safety require specialist instrumentation and domain validation and must not come from this teaching setup.

## Messina teaching scenario

Messina's seismic history makes vibration sensing educationally meaningful, but the classroom framing must stay disciplined. Build a small model structure or instrument a lab bench with two or three IMU nodes. Apply a controlled repeatable vibration. Each node stores its own raw waveform and sends only the event summary/hash through the student LoRa network.

A moving student relay later visits the sensor island, retrieves one selected waveform via BLE/Wi-Fi and carries it to the school analysis node. The exercise demonstrates scarce-link prioritization, exact evidence retrieval and multi-witness provenance without pretending to predict earthquakes.

## Privacy / security

Raw vibration data is usually less personal than audio/video but can still reveal occupancy/activity patterns when tied to a location. Use coarse zones, short retention and test structures rather than homes. Sensor identity/configuration must be authenticated so evidence cannot silently be attributed to the wrong instrument.

Any emergency/safety label in the UI must clearly say `synthetic/test`.

## Difficulty

**Medium–High.** The networking pattern is straightforward; the challenges are sampling/storage, event-window discipline, calibration metadata, timing uncertainty and keeping semantic interpretation separate from exact measurements.

## Research signal

LoRa is actively used in multi-node vibration/geotechnical monitoring systems where edge processing summarizes events and raw/high-rate sensing must be managed locally. A 2026 paper describes a low-power LoRa-based multi-nodal network for rockfall monitoring, and current commercial systems combine MEMS vibration/tilt sensing with LoRa backhaul. These examples justify the experiment category, not any physical performance claim for PollicinoNet.

References:

- https://www.mdpi.com/2079-9268/16/1/7
- https://www.ackcio.com/products/nodes/tiltmeter-lora/
