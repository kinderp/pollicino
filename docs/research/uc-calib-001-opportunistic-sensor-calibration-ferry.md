# UC-CALIB-001 — Opportunistic sensor calibration ferry

Status: PROTOTYPE / IoT and citizen-science field candidate

## Problem

Low-cost environmental sensors can drift, age or disagree. `UC-IOT-001` can successfully deliver every observation and still produce a poor dataset if the sensors themselves are biased.

The concrete question is:

> can freshly calibrated reference nodes, co-located sensors or student-carried reference measurements spread enough calibration evidence through opportunistic encounters to reduce sensor error without requiring every fixed node to have permanent Internet connectivity?

This is distinct from IOT data ferrying: CALIB measures **measurement quality and calibration-state convergence**, not merely delivery freshness.

## Actors / nodes

- fixed low-cost sensor nodes;
- one or more trusted/reference sensors or controlled calibration checkpoints;
- student-carried Pollicino nodes acting as calibration-evidence mules;
- school/home analysis node;
- optional citizen-science or laboratory supervisors.

## Why PollicinoNet fits

Calibration evidence is usually small: sensor identity/fingerprint, generation, reference value, local reading, time/freshness information, uncertainty and provenance. PollicinoNet can transport those compact exact records long before a rich raw dataset is uploaded.

Store-carry-forward is useful when a reference sensor and a fixed sensor are not simultaneously connected to the school hub. A student can carry a recent calibration observation from one location to another or return it to the hub later.

Existing Pollicino primitives that help include exact object identity, expiry, provenance-friendly manifests, persistent cache and the `UC-TIME-001` notion of explicit time uncertainty.

## Possible bearers

- BLE: short-range sensor/reference encounter and co-location exchange;
- LoRa: small calibration records/generations between fixed and carried nodes;
- Wi-Fi/LAN: upload raw histories and compute richer calibration models;
- physical carry: students move calibration evidence between isolated sensor clusters.

## What we can test immediately in software

Start with the simplest synthetic sensor model:

```text
true_value(t)
reading_i(t) = true_value(t) + bias_i + drift_i(t) + noise
```

Compare:

1. no recalibration;
2. periodic hub-only calibration when the sensor reaches/contacts the hub;
3. opportunistic one-reference offset correction;
4. only later, multi-peer/weighted calibration if the simple method fails.

Generate explicit co-location events and delayed evidence. Measure:

- absolute/relative calibration error over time;
- age of calibration state;
- number of calibration bytes transferred;
- stale calibration rejected;
- error after one or more reference encounters;
- effect of a faulty reference;
- convergence after sensor reboot or missed encounters.

Do not begin with a complex distributed estimator.

## Messina student-network scenario

A school maintains one reference checkpoint. Fixed sensors in several logical territorial clusters collect harmless measurements such as temperature/humidity. Student-carried nodes visit or pass supervised sensor locations and transport recent calibration records back to school or onward to another sensor.

A useful first field experiment can remain entirely within school/lab premises before any province-wide deployment. Later, public town names may label synthetic clusters, but no real environmental accuracy or LoRa connectivity between those places is assumed.

## What requires real hardware

A real calibration pilot requires:

- multiple identical low-cost sensors;
- at least one better reference instrument or controlled reference procedure;
- repeated co-location measurements;
- known timing/temperature/humidity conditions where relevant;
- measurement of sensor warm-up and drift;
- actual BLE/LoRa exchange latency and energy;
- restart/persistence tests;
- clear separation between sensor error and radio-delivery error.

HW-006 remains the prerequisite for any LoRa range/capacity claim, but CALIB also needs an independent metrology/data-quality gate.

## Privacy and security

Environmental calibration data can usually be low sensitivity, which makes this a good student pilot, but:

- avoid sensors that reveal occupancy or personal behavior in the first experiments;
- authenticate calibration generations and reference provenance;
- reject rollback to older calibration state;
- preserve the raw observation separately from the correction applied;
- record which reference produced a correction;
- never silently overwrite authoritative raw data.

## Difficulty

**Medium.** The initial offset/drift experiment is simple; trustworthy calibration of real heterogeneous sensors becomes substantially harder.

## Success / kill criteria

Continue if a simple opportunistic calibration baseline measurably reduces error or calibration age compared with hub-only/no-calibration approaches while adding bounded traffic and preserving provenance.

If calibration quality is dominated by uncontrolled environment differences or bad references rather than connectivity, keep the result as a negative finding and do not add network complexity.

## Related-work note

Opportunistic calibration has prior art. Gosangi, Chenji, Stoleru and Gutierrez-Osuna studied calibration of mobile chemical sensors using encounters and recent co-located measurements (arXiv `2006.12381`, 2020). Sensor-network self-calibration is also a broader established research area. These works motivate the use case but do not validate PollicinoNet.

## Physical evidence boundary

No real sensor-accuracy, drift, LoRa capacity or province-scale calibration claim follows from the software model. The frozen LoRa PHY remains unchanged.