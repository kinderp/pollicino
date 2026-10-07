# UC-176 — Event-Triggered Cooperative Burst-Capture Courier

## Problem solved
High-rate sensing everywhere, all the time, wastes storage/energy and creates large privacy and transport costs. But a rare transient event may be missed if only the detecting sensor records it.

UC-176 studies a cooperative pattern: one low-rate scout detects an event, sends a small authenticated trigger, nearby witness nodes temporarily switch to a bounded high-rate capture window, and the resulting evidence is ferried later.

## Actors / nodes
Scout sensor, 2–5 witness sensors, relay/store-and-forward nodes, collector and optional event verifier.

## Why PollicinoNet fits
The urgent object is tiny: event ID, type, trigger time, requested window, policy and uncertainty. Rich sensor evidence can remain local until a later BLE/Wi-Fi or physical contact. The pattern therefore matches LoRa control plus delayed bulk evidence.

## Bearers
- LoRa: trigger, capture acknowledgement, event ID and compact status.
- BLE/Wi-Fi/LAN: burst samples and diagnostics.
- Internet: optional final archive.
- Physical transport: SD/card/laptop evidence when bulk radio is unavailable.

## Software test now
Simulate 4–6 sensors with a known transient event and compare continuous high-rate capture, independent low-rate sensors and event-triggered cooperative burst capture. Inject false/duplicate/late triggers, trigger storms, overlapping events, clock drift, storage full and offline witnesses.

Metrics: fraction of event window captured, trigger-to-capture delay, evidence overlap, bytes generated, false-burst cost and unresolved timing uncertainty.

## Real hardware
Start on a tabletop with 4–6 boards and IMU/light/vibration sensors. Generate a harmless repeatable event such as a tap, vibration or light pulse. Avoid microphones/cameras in the first experiment. Measure actual trigger arrival, capture-window alignment, bytes and storage.

## Messina / provincial teaching scenario
A distributed environmental/structural exercise uses low-rate scouts at school/public sites. When one node detects a controlled vibration or environmental threshold crossing, nearby nodes record a short higher-rate evidence window. Students later ferry the richer evidence to a lab/collector.

## Privacy / security
Authenticate triggers and rate-limit them. Bound capture duration and sensor modalities. Do not activate microphone/camera capture without a separate explicit privacy design and consent. Preserve event ID, calibration version and timing uncertainty. A trigger is a request to capture evidence, not proof that a hazardous event occurred.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-053 distributes planned sensor tasks/campaigns; UC-027 retrieves a post-event vibration log; UC-022 corroborates multiple observations; UC-144 carries a compact catchment rise-rate alert. UC-176 adds **event-triggered, temporary multi-node high-rate capture** followed by delayed evidence ferrying.

## Validation boundary
Software can validate state-machine behavior and alignment logic. Real radio/sensor tests are required for trigger latency, capture synchronization, energy/storage cost and field usefulness.