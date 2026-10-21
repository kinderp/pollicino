# UC-SENSORQ-001 — Delay-tolerant sensor query and aggregation ferry

Status: PRIMARY / PROTOTYPE-DRIVING, software-first

## Problem

`UC-IOT-001` asks how to collect many tiny observations from disconnected sensors. A different problem appears when the raw history is much larger than what the requester actually needs.

Instead of ferrying everything, a user may ask:

```text
mean temperature from 06:00 to 12:00
maximum humidity since last visit
count samples above threshold T
return only anomalies
return hashes/references for the five newest records
```

The concrete question is:

> can a small query travel toward a disconnected sensor/cache, execute later near the data, and return an exact compact result or reference, reducing scarce-link bytes compared with pushing the whole history?

This is distinct from `UC-QUERY-001`, which searches distributed metadata indexes/Raiatea-like catalogs. SENSORQ executes a bounded query against sensor/time-series state and may trigger local aggregation.

## Actors / nodes

- teacher/student/research requester;
- fixed low-cost sensor/logger;
- student-carried Pollicino data mule;
- school/home gateway;
- optional BLE-connected sensor companion;
- query/result cache and provenance verifier.

## Why PollicinoNet fits

Both request and result can be extremely small, but they may be separated by hours and multiple carriers.

Pollicino already provides the useful transport primitives:

- exact object identity;
- store-carry-forward;
- TTL/hop/deadline governance;
- duplicate suppression;
- later rich-link resolution for larger payloads.

The application can keep query semantics above the network core. A simple first format may contain only:

```text
sensor_scope
query_id
field
operation = mean|max|min|count|latest|anomaly
start/end logical time
threshold (optional)
result_deadline
```

No generic distributed SQL engine is required to test the use case.

## Possible bearers

- LoRa: compact query and compact aggregate/result;
- BLE: direct student-node to sensor/logger handoff;
- Wi-Fi/LAN: full raw-history retrieval when needed;
- Internet: later publication/analysis;
- physical carry: students move pending queries/results between school and territorial clusters.

## What we can test immediately in software

Generate deterministic time series with 10,000–100,000 samples and compare:

1. push all unseen samples;
2. push only a fixed recent window;
3. carry query, compute aggregate at the sensor/cache, return compact result;
4. anomaly-only result;
5. aggregate plus references to the raw records that justified the answer.

Inject:

- duplicate queries;
- expired queries;
- node restart after query execution but before result delivery;
- late result after the usefulness deadline;
- sensor history truncated by retention;
- same query answered from two replicas with different freshness;
- query that cannot be answered exactly because required samples are missing.

Metrics:

- total scarce-link bytes including the query itself;
- result usefulness before deadline;
- exactness of aggregate against ground truth;
- number of raw samples avoided on LoRa;
- local compute operations/energy proxy;
- duplicate query executions suppressed;
- freshness/coverage reported with the result;
- number of requests that correctly fail closed because the requested interval is incomplete.

## Messina student-network scenario

A practical educational pilot can use harmless temperature/humidity/light sensors placed at authorized school/home/lab locations.

Example synthetic daily flow:

```text
morning school:
request "mean temperature 06:00-12:00 from sensor S3"
        |
        v
student carries query toward afternoon logical cluster
        |
        v
BLE/LoRa contact with S3
        |
        v
S3 computes compact result + provenance/coverage
        |
        v
student carries result back next morning
```

Logical labels may use Rometta-like, Spadafora-like, Saponara-like or Villafranca-like clusters. No synthetic contact implies real RF coverage between those places.

## What requires real hardware

After HW-006:

- actual sensor/logger storage limits;
- local aggregation CPU and energy cost;
- BLE/LoRa query handoff time;
- real sample-loss and clock uncertainty;
- actual byte/airtime break-even versus pushing raw measurements;
- battery effect of waking a sensor to answer a query.

The first hardware experiment should use environmental sensors only and a deliberately small query vocabulary.

## Privacy and security

- start with non-sensitive environmental data;
- authenticate query origin if the query can consume scarce energy or reveal restricted measurements;
- apply quotas/rate limits to prevent query-based battery exhaustion;
- results must carry sensor/data-generation provenance and coverage/freshness metadata;
- do not infer occupancy or personal behavior from environmental sensing without a separate privacy process;
- larger/private raw data should remain on authorized rich links.

## Difficulty

**Medium.** A safe fixed query vocabulary is easy to prototype; general distributed query planning would be unnecessary complexity at this stage.

## Success / kill criteria

Continue if a small bounded query/aggregate regime materially reduces total scarce-link bytes or delivery time while preserving exact aggregate semantics and explicit coverage/freshness.

Defer richer query languages if a handful of fixed operations already covers the real educational/sensor workloads.

## Related-work note

Sensor-network systems such as TinyDB established the idea of acquisitional query processing: request only the measurements needed and use local filtering/aggregation to reduce communication and energy. PollicinoNet's discriminating feature is the **delay-tolerant, physically carried query/result path** rather than a continuously connected sensor-routing tree.

## Physical evidence boundary

No claim about sensor-query energy savings, LoRa break-even, contact latency or battery life is valid before real hardware measurements. HW-006 and the frozen 42-byte / 2 dBm first campaign remain unchanged.