# UC-094 — Historical Sensor Query-to-Data Courier

## Idea

Send a small structured query **to disconnected sensor archives** instead of collecting all raw time series centrally first. Each node evaluates the query locally and returns a compact result plus exact evidence references; richer samples are retrieved only if needed later.

Examples:

- “Did temperature exceed threshold X during window W?”
- “Return min/max/count for this interval.”
- “Which local observations match property P and quality flag Q?”

## Problem solved

UC-053 lets us task a sensor to collect new observations. But many useful questions arise **after** data already exists on isolated nodes. Moving every raw time series to school is expensive, slow and privacy-unfriendly.

The problem is therefore:

> How can a requester ask several disconnected sensor histories a precise question and receive trustworthy, bounded answers without first centralizing all measurements?

## Actors / nodes

- requester at school or edge workstation;
- sensor/logger nodes with local historical observations;
- student relay/store-and-forward nodes;
- optional query aggregator;
- optional evidence consumer that later asks for exact raw samples.

## Why PollicinoNet fits

Structured queries and compact result envelopes are small. Bulk sensor history can stay where it was collected until a specific evidence request exists.

- **DISCOVERY:** node has a compatible archive for property/time range X;
- **EXACT:** query ID, query language/profile version, sensor/archive ID, calibration/provenance references, result set/hash and evidence references;
- **SEMANTIC:** human descriptions such as “threshold exceeded” must remain traceable to the exact query and observations.

This is a natural store-and-forward form of query-to-data.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** query envelope, archive capability, compact aggregate/result, evidence hashes and missing-result requests;
- **BLE:** nearby query/result exchange;
- **Wi-Fi/LAN:** raw time-series slices or larger result sets;
- **Internet:** optional fast path when available;
- **physical transport:** board/SD/laptop carries the archive or evidence batch.

## What we can test now in software

Define a deliberately small versioned query profile, for example:

```text
query_id
observed_property
time_window
predicate_optional
aggregate = NONE | COUNT | MIN | MAX | AVG
max_rows
result_schema_version
```

and a `SensorQueryResult`:

```text
query_id
archive_id
archive_version
sensor_provenance_ref
matched_count
aggregate_values
sample_refs[]
result_hash
status = COMPLETE | PARTIAL | NO_MATCH | UNSUPPORTED
```

Then test:

- exact time-window filtering;
- value predicates;
- aggregates;
- no-match versus no-data;
- unsupported query/operator;
- two archives returning overlapping observations;
- duplicate result delivery;
- archive updated after the query was issued;
- calibration metadata changing interpretation;
- delayed partial results from several sensor islands;
- requester asking for only the evidence samples behind one aggregate;
- malformed or intentionally expensive queries and hard resource caps.

Useful metrics include query/result bytes, raw bytes avoided, query-to-answer delay, number of archives reached, fraction of answers later requiring raw evidence and CPU/storage cost on constrained nodes.

A central semantic rule is:

> `NO_MATCH` means the archive was actually queried and found no matching observation; `UNKNOWN` or missing response means something different.

## What requires real hardware

A first experiment needs 3–5 sensor/logger nodes that retain local histories and 1–2 relays. We can use harmless temperature, humidity, light or air-pressure sensors.

Create a known ground-truth event, such as warming one sensor briefly or changing light level, then disconnect the logger from normal IP connectivity. Later issue a query from school, let it travel through student relays, and compare the compact returned answer with the actual stored series.

Only after that should we evaluate how much data transfer was avoided in practice.

## Messina teaching scenario

Place small environmental loggers at controlled school/public checkpoints in Messina, Villafranca, Rometta/Venetico and Spadafora. The school can later ask the same question to every local archive, for example:

```text
property = temperature
window = 14:00–16:00
aggregate = min,max,count
```

Replies can arrive hours apart. The aggregator shows `2/4 archives answered`, then `3/4`, rather than pretending the incomplete set is final.

This becomes a concrete lesson in distributed query processing, provenance and incomplete evidence.

## Privacy / security

- avoid precise home locations and personal environmental inference;
- use coarse deployment/checkpoint identifiers;
- authenticate query issuers when archives contain non-public data;
- cap query complexity, result rows, CPU time and evidence bytes;
- preserve sensor calibration/provenance references from UC-031;
- sign/hash result envelopes;
- distinguish `NO_MATCH`, `NO_DATA`, `UNSUPPORTED`, `PARTIAL` and no response;
- do not silently broaden a query when the local archive lacks the requested field or time precision.

## Difficulty

**Medium-high.** Basic filtering is easy; robust semantics around incomplete archives, provenance, resource limits and multi-source aggregation are the important parts.

## Why this is distinct from nearby use cases

- **UC-034:** queries Raiatea/document corpora; UC-094 targets structured historical sensor/time-series data.
- **UC-035:** computes predefined sketches/aggregates across sources; UC-094 supports an explicit bounded query issued later.
- **UC-053:** tasks future sensing; UC-094 asks questions about observations already stored.
- **UC-057:** moves an inference/model request to private data; UC-094 is a deterministic structured sensor query, not ML inference.

## Research / implementation signal

OGC SensorThings provides a mature reference model for querying sensor Observations, including filters on result values and time ranges. PollicinoNet does not need to implement the full OGC API on LoRa; the useful lesson is to define a small, versioned and exact query subset whose semantics remain clear across delayed execution.

References:

- https://docs.ogc.org/is/18-088/18-088.html
- https://ogcapi-workshop.ogc.org/api-deep-dive/sensorthings/
