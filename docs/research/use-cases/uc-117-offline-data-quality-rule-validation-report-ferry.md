# UC-117 — Offline Data-Quality Rule and Validation-Report Ferry

## Idea
Distribute compact, versioned data-quality rules to disconnected sensors, document pipelines and dataset holders, then return validation summaries and selected evidence without centralizing all raw data.

## Problem solved
Bad units, impossible values, missing fields, schema drift and malformed records can silently spread through an offline network. The validator may be far away from the data source, and different nodes may apply different rule versions.

## Actors / nodes
Rule publisher, sensor or dataset holder, local validator, relay/store-and-forward nodes, reviewer/collector.

## Why PollicinoNet fits
- **DISCOVERY:** ruleset ID/version, supported data schema and summary status.
- **EXACT:** ruleset hash, schema hash, validation-run ID, pass/fail/unknown counts and evidence references.
- **SEMANTIC:** human descriptions of failed checks.

LoRa carries ruleset/version status and compact reports; BLE/Wi-Fi/LAN carries rule bundles and selected failing samples.

## What we can test now in software
Create synthetic sensor tables and document metadata with known faults: wrong unit, missing field, out-of-range value, timestamp reversal, duplicate ID and schema mismatch. Test stale rules, partial datasets and two rulesets disagreeing.

Metrics include faults detected, false positives, report size, bytes avoided by local validation and unresolved `UNKNOWN` cases.

## What requires real hardware
Use 4–6 board nodes and a few harmless sensors/loggers. Deliberately inject safe data faults and verify that compact reports propagate while raw histories remain local unless requested.

## Messina teaching scenario
Different groups can host small environmental or school-lab datasets. A new validation ruleset travels through the mesh; each node evaluates locally and later returns only a summary plus evidence for selected failures.

## Privacy / security
Authenticate rulesets; bind every report to an exact schema/ruleset version; minimize failing-record disclosure; do not treat `PASS` as proof that data is true, only that it passed the declared checks.

## Difficulty
**Medium.**

## Why this is distinct
UC-031 tracks sensor calibration, UC-094 queries historical data and UC-099 tracks derivation; UC-117 distributes **reusable data-quality rules and local validation evidence** across disconnected holders.
