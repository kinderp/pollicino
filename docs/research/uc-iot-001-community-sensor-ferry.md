# UC-IOT-001 — Community sensor ferry for sparse environmental telemetry

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Problem

Small fixed sensors may be useful in places where continuous Internet access is absent, undesirable or too expensive. Their measurements are usually tiny, delay-tolerant and naturally batchable, so keeping a permanent end-to-end network alive can cost more than the data deserves.

A mobile Pollicino node can periodically collect buffered observations, carry them physically and deliver them later to a school/home gateway.

Candidate educational measurements include:

- temperature and humidity;
- rainfall or water-level laboratory fixtures;
- air-quality classroom experiments;
- soil moisture or greenhouse/garden observations;
- power/energy-lab measurements;
- simple device-health counters.

Real environmental, agricultural or infrastructure monitoring would require separate installation, calibration and safety review.

## Actors / nodes

- fixed low-power sensor node;
- student-carried Pollicino node;
- school/lab gateway;
- optional home gateway;
- optional territorial fixed relay;
- data consumer/dashboard.

## Messina educational scenario

Create several pseudonymous sensor clusters representing different local contexts: `school-lab`, `coastal-cluster`, `hill-cluster`, `garden-cluster`. Students who naturally move between school and their area periodically collect observations and bring them back to the dense school mesh or an Internet-connected gateway.

```text
sensor cluster A --short contact--> student A
                                     |
sensor cluster B --short contact--> student B
                                     |
                         physical carry to school
                                     |
                                     v
                           school sync / gateway
```

No scenario name implies measured radio reach between actual locations.

## Why PollicinoNet fits

Sensor traffic creates a different optimization problem from file distribution:

- many very small records;
- monotonic time-series state;
- duplicates are common and wasteful;
- older samples may be summarized once a newer aggregate exists;
- some observations are urgent while most are delay-tolerant;
- the receiver may already own most of the series.

PollicinoNet can provide store-carry-forward, exact object identity, reconciliation, prioritization and byte accounting while allowing richer upload later.

## Possible bearers

- LoRa for sensor-to-mule or relay contacts;
- BLE for very local collection/configuration;
- Wi-Fi for bulk drain at school/home;
- Internet for final ingestion;
- physical movement for the carry phase.

## What can be tested now in software

Without boards we can model:

1. sensors generating timestamped observations at different rates;
2. finite buffers and overwrite/retention policy;
3. student contact schedules with missed encounters;
4. raw record transfer versus batched/delta/summary representations;
5. duplicate suppression and inventory reconciliation;
6. urgent anomaly samples versus normal telemetry;
7. intermittent school/home gateways.

Useful comparisons:

```text
send every raw observation
vs
batch records
vs
delta-coded batch
vs
summary + exceptions
```

The experiment should measure both **information freshness** and scarce-link bytes, not compression ratio alone.

## What requires real hardware

Hardware is required before claiming:

- sensor-to-board range;
- real collection time or contact capacity;
- duty-cycle behavior;
- sensor battery life;
- environmental robustness;
- real measurement accuracy;
- physical coverage of any Messina-area deployment.

HW-006 remains the first radio evidence gate; later sensor-specific campaigns can add power and installation measurements.

## Privacy / security

Even apparently harmless telemetry can reveal location or household routines.

Requirements:

- pseudonymous sensor IDs where possible;
- coarse logical area rather than exact home address;
- explicit distinction between public environmental data and private household telemetry;
- integrity/authentication for observations used operationally;
- anti-replay and sequence/freshness checks;
- retention limits for raw observations.

## Implementation difficulty

**Medium.** Most networking primitives already exist. New work is mainly the time-series object model, freshness/aggregation policy and simulator workload.

## Minimal measurable hypotheses

- H1: batching/reconciliation reduces scarce-link bytes materially compared with forwarding every record independently.
- H2: mobile collection allows useful eventual delivery with fewer always-on assumptions than a permanently connected topology.
- H3: freshness-aware scheduling gives recent/anomalous samples better timeliness without starving ordinary telemetry.

## Metrics

- delivered observation ratio;
- age-of-information / sample freshness at gateway;
- bytes per useful observation;
- duplicate observations suppressed;
- dropped samples due to finite storage;
- urgent anomaly delivery latency;
- forwarding actions;
- per-bearer TRC;
- storage pressure.

## Gate decision

**PROTOTYPE.** This is a distinct high-value workload because freshness, batching and many-to-one collection differ materially from generic content mule and DNA topic dissemination.

## Related research precedent

The classic Data MULE architecture explicitly studies mobile entities that collect buffered data from sparse sensors and later deliver it to access points: https://doi.org/10.1016/S1570-8705(03)00003-9 .