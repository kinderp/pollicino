# UC-MAP-001 — Offline geospatial and local-hazard delta exchange

Status: PROTOTYPE / EMERGENCY-ADJACENT RESEARCH

## Summary

PollicinoNet nodes can carry compact, versioned references and deltas for geospatial information when continuous network access is unavailable. Instead of moving complete maps over LoRa, nodes advertise which geographic layers/tiles or local observations have changed and allow receivers to pull only relevant, unknown updates. Full maps, imagery and large layers remain on Wi-Fi/LAN/Internet whenever possible.

This is a situational-awareness and data-synchronization experiment, not a certified navigation or warning system.

## Problem solved

Map and local-status data become stale during disconnected operation. A mobile user may need to know that a small part of a shared dataset changed — for example:

- a public road/service status layer;
- a local observation point;
- a school/community meeting point;
- a connectivity-outage observation;
- an authorized civil-protection/public hazard layer version;
- a changed map tile or vector feature.

Sending a full regional map to every node is wasteful when only a few features changed.

## Actors / nodes

- public-data or school mapping gateway;
- student-carried mobile nodes;
- optional fixed observation/sensor nodes;
- home/school Wi-Fi gateways;
- optional authorized protection-civil/public-data adapter.

## Messina educational scenario

Use a synthetic map divided into coarse public areas labelled with towns or grid cells, never student addresses. A school gateway publishes map generation `M20`; only cells 12 and 18 changed. Student nodes carry compact changed-cell identifiers and signed/public metadata to other clusters. A receiver interested in its coarse region pulls only the changed references and later downloads the rich vector/raster payload over Wi-Fi.

A second, non-operational exercise can combine public/synthetic hazard layers with the existing `UC-EMERG-001` bulletin workload to study how map context and time-sensitive notices interact.

## Why PollicinoNet fits

The use case reuses several established concepts:

- reference/catalog pull from `UC-CONTENT-002`;
- content-addressed manifests and exact verification;
- topic/geo relevance when supplied by DNA or an application;
- store-carry-forward;
- expiry and provenance;
- multi-bearer handover;
- scarce-link byte accounting.

The key value is **delta/reference movement**, not map rendering inside PollicinoNet.

## Bearers

- LoRa: changed-cell IDs, small vector deltas, version summaries, provenance;
- BLE: nearby device-to-device local map exchange;
- Wi-Fi/LAN: map tiles, larger vector layers, images;
- Internet: authoritative public mapping provider;
- physical carry: students/vehicles move map-change knowledge between clusters.

## What we can test now in software

Generate a synthetic map universe and per-node geographic interests. Compare:

1. push full map-generation manifest;
2. push all changed IDs;
3. receiver requests region then pulls changed IDs;
4. interest filtering + reconciliation of known map items;
5. small delta versus full-object rich-link retrieval.

Metrics:

- bytes per useful map update;
- irrelevant geographic updates received;
- stale generations;
- duplicate suppression;
- time-to-useful-update;
- eventual rich-path retrieval success;
- privacy exposure from geographic interests.

No real hazard dataset is required for the initial experiment.

## Hardware required later

Real boards are needed to measure:

- how many version/delta references fit into measured encounters;
- contact timing while users/vehicles move;
- power cost;
- practical LoRa-to-Wi-Fi handover;
- field usability of the local map client.

Any operational emergency-map claim would additionally require authoritative data integration, provenance validation and domain/agency review. HW-006 remains the first radio evidence gate.

## Privacy and security

Geospatial interests can reveal where a person lives or travels.

Initial rules:

- use coarse public grid/area IDs, not home coordinates;
- do not transmit student GPS traces in the standard experiment;
- avoid broadcasting full interest lists;
- public layers should preserve source/provenance and version;
- private/team layers require access control and end-to-end confidentiality where appropriate;
- reject unsigned or untrusted updates when the application policy requires authoritative data;
- distinguish observations from verified official information.

## Difficulty

**Medium.**

The transport work is modest because references/reconciliation already fit Pollicino concepts. The difficult part becomes authoritative-data semantics and privacy if the prototype moves beyond synthetic/public datasets.

## Research context

DTN MapEx studied disaster-area map generation and sharing over DTN, while Geo-DMP demonstrated opportunistic exchange of named geospatial content. ITU also uses geospatial connectivity mapping for disaster-response decision support. These precedents make geospatial deltas a credible challenged-network workload, but they do not provide physical evidence for PollicinoNet or Messina.

## Success criteria

Continue if region filtering + reconciliation materially reduces scarce-link map traffic compared with full-generation distribution while preserving deterministic version/provenance semantics.

## Decision

**PROTOTYPE / EMERGENCY-ADJACENT RESEARCH.**

Useful as a distinct geospatial workload and a composition point with emergency/sensor data. It does not authorize safety-critical navigation, official warning claims or a new map-specific wire protocol.
