# UC-131 — Time-Series Gap Detection and Missing-Interval Repair Courier

## Idea

Detect missing intervals in sensor histories, advertise the gaps compactly, and try to repair them from local buffers, overlapping sensors or delayed data mules before resorting to imputation.

The key distinction is:

> missing data is not automatically reconstructed data.

The system should preserve whether a value is original, recovered from another exact copy, reconstructed from another evidence source, imputed or still unknown.

## Problem solved

Rural and student IoT nodes can lose measurements because of reboot, storage faults, upload interruption, full buffers or intermittent connectivity.

A collector may receive apparently continuous files from several relays but still have holes in the actual observation timeline.

UC-117 can validate data quality; UC-131 adds a repair workflow for **which time intervals are missing and where another copy might exist**.

## Actors / nodes

Sensor/logger, student relay/data mule, overlapping sensor or backup cache, collector, optional imputation worker and reviewer.

## Why PollicinoNet fits

Gap summaries are tiny. A sensor can advertise a compact interval map such as:

```text
stream = temp-A
present = [08:00..08:17, 08:24..09:00]
missing = [08:17..08:24]
generation = 42
```

LoRa moves the gap/request metadata. BLE/Wi-Fi or physical carry moves actual sample blocks.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: stream ID, generation, missing interval/range request, compact completeness summary and repair status.
- BLE: small recovered sample blocks.
- Wi-Fi/LAN: full time-series segments and evidence.
- Internet: optional archive or imputation service.
- Physical transport: SD card/laptop containing historical raw data.

## What we can test now in software

Generate several synthetic sensor streams with known ground truth and deliberately remove intervals.

Test:

- local logger still has the exact missing block;
- a relay has a delayed duplicate;
- an overlapping sensor has related but not identical evidence;
- no exact copy exists;
- time base changed after reboot;
- duplicate/overlapping recovered blocks disagree;
- repair arrives after an imputed placeholder was already created.

Use explicit provenance states such as ORIGINAL, EXACT_RECOVERY, CROSS_SENSOR_DERIVED, IMPUTED and UNKNOWN.

Measure gap-detection precision, exact recovery fraction, bytes requested and whether provenance remains correct.

## What requires real hardware

Use 3–5 harmless environmental loggers and 4–6 LoRa boards.

Create controlled gaps by temporarily stopping one logger or withholding one storage segment, while another relay retains a copy. Then reconcile after delayed contacts.

Only after real tests should the project report recovery rate, contact delay or storage/energy cost.

## Messina teaching scenario

Place school-owned temperature/light loggers at controlled public/school checkpoints across a small Messina-area experiment. One logger deliberately withholds a seven-minute segment. Another student node later carries a duplicate segment or overlapping evidence.

The class can see the difference between exact recovery and statistical imputation instead of silently filling missing values.

## Privacy / security

Use non-sensitive environmental streams first. Avoid household occupancy or personal-behavior sensors. Keep precise locations coarse, authenticate stream/generation metadata, bound historical queries, and preserve provenance so imputed values never masquerade as original measurements.

## Difficulty

Medium. Detecting gaps is easy; reliable exact repair under clock resets, duplicate blocks and multiple evidence sources is the interesting part.

## Why this is distinct

UC-003 collects rural sensor data; UC-031 binds calibration provenance; UC-094 queries historical archives; UC-117 validates data quality; UC-125 joins several sensor archives. UC-131 focuses on **missing-interval discovery and provenance-preserving repair**.

## Research / implementation signal

Missing IoT time-series data remains an active 2026 topic. Recent work studies adaptive recovery/imputation under changing sensor subsets and resource availability. PollicinoNet should first recover exact delayed copies when possible and keep imputation explicitly separate.

References:

- https://arxiv.org/abs/2607.23503
- https://doi.org/10.1016/j.comnet.2026.112355
