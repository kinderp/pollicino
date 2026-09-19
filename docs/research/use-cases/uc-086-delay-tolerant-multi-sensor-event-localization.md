# UC-086 — Delay-Tolerant Multi-Sensor Event Localization

## Idea

Let several distributed sensor nodes observe the same harmless event — for example a buzzer, light pulse or vibration source — and ferry only compact detections and uncertainty metadata until a later node can combine them to estimate a **coarse event location**.

The sensors do not need a live connection to a central solver when the event happens. PollicinoNet carries the observations later. LoRa is not used as a ranging technology here.

## Problem solved

UC-022 asks whether several independent witnesses corroborate an event. UC-027 carries vibration-event evidence. A further question is:

> if multiple nodes observed the event from known locations, can their delayed observations jointly tell us where it probably happened?

Examples that can be studied safely include:

- locating a buzzer in a school courtyard;
- locating a light flash using photodiodes;
- locating a vibration impulse on a controlled test table/floor model;
- later, research-only environmental or structural event localization with appropriate sensors.

The difficult part is that observations arrive late, clocks are imperfect and some detections may be missing or wrong.

## Actors / nodes

- 3+ fixed sensor nodes with known coarse positions;
- student relay/store-and-forward nodes;
- optional trusted time/checkpoint source from UC-020;
- solver node at school/lab;
- optional UC-022 corroboration layer;
- optional UC-031 calibration/provenance records.

## Why PollicinoNet fits

Each local detection can be small while raw waveforms may be large.

- **DISCOVERY:** event/detection available, sensor class, coarse area and confidence hint;
- **EXACT:** sensor ID, calibration version, timestamp/checkpoint plus uncertainty, event signature/features, observation hash;
- **SEMANTIC:** labels such as `buzzer-test`, `vibration-test` or `light-pulse`, useful for grouping but not sufficient for physical localization.

Nodes can capture evidence locally at event time and exchange it later. Rich bearers can retrieve raw evidence only when needed.

Nothing changes the frozen LoRa PHY, and LoRa RSSI must not be confused with source-localization measurements unless a separate experiment explicitly validates such a method.

## Possible bearers

- **LoRa:** event ID, sensor ID, timestamp/uncertainty, compact arrival-time or signal-feature summary, calibration hash, result request;
- **BLE:** nearby sensor synchronization/configuration and small evidence batches;
- **Wi-Fi/LAN:** raw waveform, high-rate sensor series and calibration records;
- **Internet:** optional transfer to a larger analysis service;
- **physical transport:** student carries buffered evidence from isolated sensors.

## What we can test now in software

Start with a synthetic geometry and controllable clock error.

Define an `EventObservation`:

```text
event_id
sensor_id
sensor_position_or_checkpoint
sensor_position_uncertainty
measurement_type
measurement_value
time_checkpoint
time_uncertainty
calibration_hash
feature_hash
raw_evidence_hash
```

Then test:

- three clean observations of one event;
- one missing observation;
- one false detection;
- delayed and reordered delivery;
- two events close in time that can be incorrectly associated;
- clock offset and clock drift;
- sensor-position uncertainty;
- calibration mismatch;
- observations that are individually plausible but geometrically inconsistent;
- solver returns a region/uncertainty rather than a false precise point;
- raw evidence requested only after compact observations suggest a useful solution.

Useful metrics include localization error on synthetic ground truth, estimated uncertainty, false association rate, minimum witness count, evidence bytes requested and time-to-solution after observations begin to arrive.

A key rule is:

> if timing/geometry evidence is insufficient, the correct result is `LOCALIZATION_UNCERTAIN`, not a precise-looking coordinate.

## What requires real hardware

A first physical experiment can remain small and safe:

- 3–5 LoRa sensor nodes at measured positions in a school lab/courtyard;
- a harmless buzzer, LED flash or vibration source;
- simple sensors appropriate to the chosen signal;
- one solver laptop;
- deliberate network partitions so observations must be ferried later.

Begin with a large, controlled geometry and no claims about centimetre-level precision. The experiment should measure actual clock uncertainty, sensor latency and localization error.

For acoustic experiments, avoid continuous audio recording. Prefer event-time/feature extraction on-device and discard raw audio unless an explicitly approved test requires it.

## Messina teaching scenario

Place four sensor nodes around a controlled school courtyard or gym. A teacher triggers a buzzer/light pulse from one of several known test positions while the sensor nodes have no end-to-end route to the solver.

Each node stores its compact observation. Students later act as relay nodes and bring those observations to the lab. The class compares:

```text
single observation -> no localization
2 observations     -> weak/ambiguous region
3+ observations    -> constrained region, subject to measured uncertainty
```

A later exercise can deliberately introduce one bad timestamp and ask whether the solver exposes the conflict rather than hiding it.

## Privacy / security

Localization systems can become surveillance systems if designed carelessly.

- use only synthetic/harmless event sources in teaching experiments;
- do not localize people, phones or private conversations;
- avoid continuous microphones and retain only minimal derived features where possible;
- store coarse sensor locations if exact deployment coordinates are sensitive;
- authenticate sensor observations;
- preserve calibration/time provenance;
- explicitly model uncertainty and conflicting evidence;
- never present the prototype as emergency-grade locating equipment without independent validation.

## Difficulty

**High.** Transport is easy; trustworthy event association, timing, calibration and uncertainty-aware localization are the difficult parts.

## Why this is distinct from nearby use cases

- **UC-022:** asks whether witnesses agree that an event occurred.
- **UC-027:** moves event summaries and exact vibration evidence later.
- **UC-037:** samples an environmental transect while mobile.
- **UC-086:** combines delayed observations from known sensors to estimate **where one event originated**, with explicit uncertainty.

## Research / implementation signal

Multi-sensor source localization remains an active 2026 research problem precisely because clutter, timing uncertainty, missed detections and multiple possible sources complicate naïve triangulation. PollicinoNet adds a different systems constraint: the sensor observations may only meet at the solver long after the event.

References:

- https://doi.org/10.1109/TSP.2026.3685137
- https://doi.org/10.1186/s13634-026-01337-9
