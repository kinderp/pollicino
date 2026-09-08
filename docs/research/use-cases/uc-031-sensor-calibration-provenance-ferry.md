# UC-031 — Sensor Calibration and Provenance Ferry

## Idea

Let low-cost sensor nodes carry not only measurements but also **which calibration they used, when it was established and against which reference evidence**, then propagate new calibration state through PollicinoNet when nodes are intermittently connected.

The aim is not to claim laboratory accuracy from cheap sensors. The aim is to make calibration state explicit, versioned and testable.

## Problem solved

Low-cost environmental and IoT sensors can drift, differ from one another or become misleading when calibration/configuration changes silently.

In a rural/offline network, a sensor may operate for weeks without permanent backhaul. A reference instrument or calibration station may be visited only occasionally. Measurements are much more useful when downstream users can answer:

```text
which sensor produced this?
which calibration version was active?
what reference/campaign produced that calibration?
was the calibration already stale?
```

PollicinoNet can ferry calibration manifests and exact supporting evidence separately from the ordinary measurement stream.

## Actors / nodes

- low-cost temperature/humidity/air-quality/soil or other teaching sensors;
- one reference or better-characterized sensor/instrument;
- student relay/store-and-forward nodes;
- school/lab calibration-analysis node;
- optional rural/farm/garden sensor island;
- human reviewer responsible for accepting a calibration update.

## Why PollicinoNet fits

Calibration changes are infrequent and compact, while calibration datasets can be larger.

- **DISCOVERY:** sensor ID, active calibration version, freshness/expiry and availability of a newer calibration;
- **EXACT:** calibration manifest, coefficients/model hash, reference-instrument identity, exact calibration dataset hash and provenance;
- **SEMANTIC:** labels such as `calibration recommended` or `possible drift`, which must not overwrite the exact evidence.

LoRa can carry calibration version/freshness and small manifests. BLE/Wi-Fi/LAN or physical carry can move the raw co-location dataset or model artifact.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** active calibration ID, newer-version announcement, freshness, compact quality metadata and exact evidence hash;
- **BLE:** nearby maintenance/calibration exchange;
- **Wi-Fi/LAN:** raw calibration dataset and model transfer;
- **Internet:** optional external analysis/reference-data access;
- **physical transport:** student/reference node carries calibration evidence to disconnected sensor islands.

## What we can test now in software

- simulate several sensors with different offset/gain/drift models;
- create versioned calibration manifests tied to exact sensor/configuration IDs;
- co-locate synthetic sensor streams against a synthetic reference;
- fit a deliberately simple calibration model and content-address the result;
- reject a calibration produced for the wrong hardware/configuration version;
- propagate calibration `v2` through a partitioned network while some nodes remain on `v1`;
- expose measurement provenance as `sensor + firmware/config + calibration ID`;
- mark stale/unknown calibration state rather than silently treating old coefficients as current;
- use UC-020 for time/freshness uncertainty and UC-019 for trust/revocation of calibration authorities;
- compare downstream analysis with and without calibration provenance;
- inject bad reference data and prove that provenance allows the suspect calibration campaign to be identified later.

A core invariant is:

> a corrected number without calibration provenance is not equivalent to a calibrated measurement.

## What requires real hardware

- 2–3 inexpensive identical or similar sensors;
- one better-characterized reference sensor/instrument appropriate to the teaching experiment;
- a controlled co-location period;
- real drift/repeatability measurements;
- LoRa propagation of calibration version metadata;
- later BLE/Wi-Fi/physical retrieval of the supporting calibration dataset;
- repeated measurement after calibration to evaluate actual improvement.

Any accuracy claim must be limited to the tested sensors, reference, conditions and measured dataset.

## Messina teaching scenario

A practical school experiment could start with temperature/humidity or particulate sensors rather than safety-critical instrumentation. Place several low-cost nodes together at the school for a reference campaign, then move selected nodes to controlled locations in the Messina/Rometta/Villafranca area.

A student relay later carries a new signed calibration manifest from the school node to an offline sensor. The sensor continues logging locally and marks exactly when the new calibration became active. When measurements return, Raiatea or another analysis tool can distinguish data produced under `cal-v1` from `cal-v2`.

A later rural version could use garden/soil/weather sensors, still treating the reference campaign and hardware limitations explicitly.

## Privacy / security

Environmental calibration data is usually not highly personal, but precise sensor location and long-term environmental traces can reveal occupancy or property information. Use coarse/public test locations where possible.

Calibration manifests need authenticated provenance. A malicious or accidental calibration update can make every subsequent measurement misleading, so acceptance should be explicit and rollback/history preserved.

Private signing keys must stay off ordinary relay nodes.

## Difficulty

**Medium.** The distributed-system side is modest; the important discipline is version/provenance tracking and separating software-simulated calibration from real sensor accuracy claims.

## Research signal

Distributed sensor calibration and calibration of low-cost LoRaWAN sensing nodes remain active research topics. Recent work studies distributed calibration algorithms and reference-based calibration of low-cost LoRaWAN air-quality monitors, supporting the value of treating calibration as a first-class data/provenance problem.

References:

- https://doi.org/10.3390/s25082505
- https://www.mdpi.com/1424-8220/25/5/1614
