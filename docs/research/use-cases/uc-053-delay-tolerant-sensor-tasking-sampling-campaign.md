# UC-053 — Delay-Tolerant Sensor Tasking and Sampling Campaign

## Idea

Let a disconnected operator ask remote sensor nodes to **collect a new observation or run a bounded sampling campaign**, even when there is no live end-to-end path.

UC-003 already covers sensors that accumulate data and wait for a courier. UC-053 adds the opposite direction: the question itself travels first.

Example:

```text
"Sensor group C:
measure temperature + humidity every 5 minutes
for 60 minutes
starting after campaign epoch 812"
```

A student relay can carry that request to the sensor island. The sensor validates it locally, performs the safe measurement campaign, and a later relay brings back the result summary and, if needed, the exact data batch.

## Problem solved

A fixed sensing policy is often wasteful. We may discover later that one location, time window or phenomenon deserves more detail, but the sensor has no Internet connection.

A cloud-only design assumes the operator can immediately push a new command. PollicinoNet can instead make a sampling request a small delay-tolerant object that may arrive minutes or hours later while preserving expiry and safety limits.

Useful examples include:

- ask a rural sensor for a denser one-hour sample after an interesting event;
- request one diagnostic measurement from a school IoT node;
- ask several environmental nodes for the same short comparison campaign;
- request a fresh calibration observation after UC-031 indicates stale provenance;
- ask a robot/sensor platform for a harmless observation without opening an interactive control channel.

## Actors / nodes

- teacher/research coordinator node;
- fixed environmental/IoT sensor nodes;
- student relay/store-and-forward nodes;
- optional school server collecting exact results;
- optional mobile gateway, bicycle or vehicle;
- optional UC-020 time-checkpoint source and UC-019 trust-state source.

## Why PollicinoNet fits

The control object is tiny while the resulting dataset may be larger.

- **DISCOVERY:** `sensor/task capability available`, `campaign pending`, `result ready`;
- **EXACT:** campaign ID, target sensor/group, requested observable, bounded rate/duration, start rule, expiry, authorization and result hash;
- **SEMANTIC:** human labels such as `microclimate follow-up`, never a replacement for the exact campaign contract.

Store-carry-forward is useful because the coordinator, relay and sensor do not need to be connected at the same time. Rich bearers can move full time-series data later.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact campaign request, acceptance/rejection state, progress/result-ready summary and small aggregate results;
- **BLE:** nearby configuration and moderate-size result retrieval;
- **Wi-Fi/LAN:** complete time-series batches, logs and firmware-independent diagnostics;
- **Internet:** optional fast path when present;
- **physical transport:** a student node carries the pending campaign and later the result batch between disconnected islands.

## What we can test now in software

Implement a canonical `SamplingCampaign` and deterministic sensor emulator.

Test:

- one-shot measurement versus bounded periodic sampling;
- delayed arrival after the requested start time;
- explicit `accepted`, `rejected`, `expired`, `completed`, `partial` states;
- duplicate/reordered campaign delivery without duplicate execution;
- local rate and duration ceilings that remote requests cannot override;
- campaign cancellation arriving before or after execution starts;
- node reboot with crash-safe campaign state;
- stale authorization/trust state from UC-019;
- uncertain time/freshness from UC-020;
- result summary over scarce bearer and exact batch retrieval over UC-033;
- several sensors receiving the same campaign at different times;
- metrics: request-to-accept delay, request-to-first-sample, campaign completion, duplicate-execution count, bytes per bearer and result age.

A key invariant is:

> remote tasking can request observations only inside locally enforced safe resource limits; a delayed network command never overrides local hardware protection.

## What requires real hardware

- 3–5 LoRa boards;
- at least 2 harmless sensors, for example temperature/humidity/light;
- one deliberately disconnected sensor island;
- one moving student relay;
- real measurement of request propagation, execution start, result return and contact duration;
- repeated campaigns with known delays and missed contacts.

Do not use the first prototype for safety-critical actuation, medical sensing or any claim that requires calibrated accuracy before UC-031-style validation.

## Messina teaching scenario

Place two sensor nodes in controlled school/community locations representing, for example, `Rometta/Venetico` and `Spadafora`, while the coordinator node remains at school.

The class notices an interesting synthetic event and creates a one-hour sampling campaign. No direct route exists. A student's Pollicino node carries the request during normal movement, the remote sensor executes it, and another later contact returns the compact result summary. The full CSV is retrieved only when Wi-Fi/BLE becomes available.

A second experiment can compare how quickly the same campaign reaches several nodes along a coarse `Messina -> Villafranca -> Rometta -> Spadafora` teaching topology without collecting students' continuous trajectories.

## Privacy / security

Tasking is more sensitive than passive sensing because it can change device behavior.

- authenticate and authorize every campaign;
- allow-list observable types, sample-rate ceilings and maximum duration locally;
- include expiry and anti-replay identifiers;
- separate permission to request data from permission to reconfigure firmware or actuators;
- do not expose private location/identity in LoRa broadcast metadata;
- keep precise sensor location protected when it could reveal a home or sensitive site;
- make partial/failed execution explicit rather than fabricating complete data.

## Difficulty

**Medium–High.** The message format is small, but idempotent execution, time uncertainty, bounded remote control and delayed result correlation make it a useful distributed-systems experiment.

## Research signal

The OGC SensorThings API explicitly separates **Sensing** from **Tasking**. Its Part 2 Tasking Core provides a standard way to parameterize IoT devices to carry out observations or other bounded functions. PollicinoNet can study what happens when this tasking model is carried over long disruptions rather than assuming a continuously reachable Web API.

References:

- https://www.ogc.org/standards/sensorthings/
- https://ogcapi-workshop.ogc.org/api-deep-dive/sensorthings/
