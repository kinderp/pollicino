# UC-125 — Delay-Tolerant Cross-Sensor Correlation and Join Query

## Idea

Ask a question that requires combining observations held by different disconnected sensor archives, while moving only compact candidate results first.

Example: find vibration events in one zone that occurred within a bounded time of a temperature or light event reported by another zone.

Each archive is queried locally. PollicinoNet carries candidate keys and time windows, then a later stage joins the partial answers. Raw evidence moves only if needed.

## Problem solved

UC-094 can query one historical sensor archive at a time. Many real questions need two or more sources:

- did two different sensors observe compatible evidence near the same period?
- did an environmental change coincide with a robot or vibration event?
- do measurements from two areas overlap in a requested interval?
- can a class correlate observations without first centralizing every raw time series?

## Actors / nodes

Query issuer/aggregator, two or more sensor/logger archives, student relay/store-and-forward nodes, optional time-quality service from UC-123, and an optional reviewer that later requests raw evidence.

## Why PollicinoNet fits

A distributed join can be staged:

1. discover which archives can answer each subquery;
2. send small subqueries to the data;
3. return candidate keys/time ranges;
4. join candidates at an aggregator or intermediate node;
5. retrieve raw evidence only for surviving matches.

- DISCOVERY: archive capability and property/time coverage.
- EXACT: query ID, subquery ID, archive version, key/time interval, uncertainty, result hash and join profile.
- SEMANTIC: labels such as possible-correlated-event, never a replacement for exact predicates.

## Possible bearers

- LoRa: query plan, subquery, candidate IDs/time windows and compact join result;
- BLE: nearby candidate/evidence exchange;
- Wi-Fi/LAN: time-series slices and larger join outputs;
- Internet: optional remote archive access;
- physical transport: SD/laptop/board carrying local archives.

## What we can test now in software

Start with two synthetic time-series archives and a small join profile containing left/right property, predicates, maximum time distance, optional join key and maximum candidates.

Test:
- exact timestamp match;
- interval overlap;
- bounded nearest-event match;
- no match versus missing archive;
- one late archive changing a previous partial result;
- duplicate observations;
- clock uncertainty from UC-123 widening the join window;
- calibration/provenance mismatch;
- candidate explosion and hard limits;
- three-source joins;
- raw evidence retrieval only after a candidate survives.

Result states should include COMPLETE, PARTIAL, NO_MATCH, UNKNOWN and TOO_BROAD.

Useful software metrics include candidate bytes, raw bytes avoided, join completeness and false matches against synthetic ground truth.

## What requires real hardware

Use 3–5 sensor/logging nodes with at least two harmless measurements, for example temperature, light and vibration.

Create a controlled event sequence with known ground truth, disconnect the archives, then issue the cross-sensor query later through student relays.

Any claim about timing or correlation accuracy requires real clock-quality measurements first.

## Messina teaching scenario

Student groups operate simple environmental loggers at controlled school/public checkpoints in Messina, Villafranca, Rometta/Venetico and Spadafora.

A class later asks which light-change events were within ten minutes of a temperature excursion at another checkpoint. Replies arrive independently. The aggregator first shows a partial result, then revises it when another island answers.

## Privacy / security

Use coarse deployment identifiers rather than home coordinates, authorize non-public archives, limit query complexity and candidate counts, preserve sensor calibration/provenance, and keep incomplete or uncertain answers visibly incomplete.

## Difficulty

High. Query decomposition is manageable; correct joins under late or missing data, clock uncertainty and bounded resources are the hard part.

## Why this is distinct

UC-094 asks a structured question of one historical sensor archive. UC-022 corroborates a specific event claim across witnesses. UC-125 evaluates a general bounded cross-source correlation/join query over multiple disconnected archives.

## Research / implementation signal

Modern stream and federated-query systems treat event-time watermarks, temporal joins and source federation as explicit semantics. PollicinoNet adapts those ideas to delayed, intermittently connected archives.

References:

- https://nightlies.apache.org/flink/flink-docs-master/docs/sql/reference/queries/joins/
- https://www.w3.org/TR/sparql12-federated-query/
- https://doi.org/10.3390/app16189102
