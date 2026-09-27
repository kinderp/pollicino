# UC-126 — Distributed Dataset Snapshot and Watermark Barrier Courier

## Idea

Create a reproducible logical snapshot from several changing, intermittently connected data holders without pretending that "latest from each node" is one coherent dataset.

A snapshot manifest pins exactly which version or watermark from each source belongs to one dataset cut.

## Problem solved

AI and Raiatea workflows may assemble data from multiple student or edge nodes. If each source keeps changing, a naive collection can silently combine one source from Monday, another from Tuesday, a third after a correction, and a fourth from an older schema.

The resulting dataset may be impossible to reproduce later even though every individual file has a hash.

The useful question is: which exact source versions together define dataset snapshot S, and which sources were missing or uncertain?

## Actors / nodes

Dataset snapshot coordinator, two or more dataset/corpus holders, student relay/store-and-forward nodes, optional validator from UC-117, optional AI trainer/evaluator, and optional Raiatea catalog.

## Why PollicinoNet fits

A snapshot barrier is mostly metadata.

Each holder can publish an immutable local cut containing source ID, schema ID, local snapshot ID, watermark or closed interval, manifest hash and status.

The coordinator then seals a global DatasetSnapshotManifest referencing those exact local cuts.

- DISCOVERY: source family and schema capability.
- EXACT: source snapshot IDs, hashes, schema versions, watermark/boundary and global manifest hash.
- SEMANTIC: labels such as training-2026-09 are convenient names only.

## Possible bearers

- LoRa: snapshot request, local snapshot ID/hash and completion/partial status;
- BLE: small manifests;
- Wi-Fi/LAN: dataset shards and validation reports;
- Internet: optional remote source synchronization;
- physical transport: SSD/laptop carrying frozen dataset shards.

## What we can test now in software

Create 3–5 local stores that mutate while a snapshot round runs.

Test:
- one source updates during collection;
- one source is late;
- one source cannot freeze and returns a watermark only;
- schema change mid-round;
- a correction invalidates an earlier local cut;
- two snapshot rounds overlap;
- coordinator restart;
- exact retry producing the same sealed manifest;
- snapshot declared PARTIAL because one source never answered.

Compare naive "copy whatever is latest", timestamp-labelled copies, content-addressed local snapshots, and an explicit global manifest with per-source snapshot IDs or watermarks.

The key invariant is: a global snapshot is complete only when its declared source set and each source version are explicit. Missing data must never be silently replaced by whatever happened to arrive.

## What requires real hardware

Use 4–6 PollicinoNet nodes paired with laptops or Raspberry Pi-class hosts holding small changing datasets or sensor logs.

Start a snapshot round while one holder is disconnected and another continues appending data. Carry only snapshot metadata over LoRa, then move selected shards over Wi-Fi or physical transport.

Verify later that every consumer can reconstruct the exact same declared cut.

## Messina teaching scenario

Different student groups maintain small public or synthetic datasets in Messina, Villafranca, Rometta/Venetico and Spadafora.

The school requests a reproducible "September experiment dataset". Each group seals its local portion when reached. A relay carries the local snapshot IDs back to the coordinator.

If one group does not answer in time, the result is visibly PARTIAL; it is not silently relabelled as complete.

## Privacy / security

Use opaque source IDs when dataset ownership or location is sensitive, authenticate snapshot manifests, keep record-level contents off LoRa, preserve usage-policy and consent references, and avoid exposing sensitive record counts when they reveal participation.

## Difficulty

High. Creating hashes is easy; defining a coherent cut under asynchronous updates and partial participation is the difficult part.

## Why this is distinct

UC-099 records lineage while deriving artifacts. UC-114 audits overlap between datasets. UC-120 invalidates derived artifacts when inputs change. UC-126 defines an exact multi-source snapshot boundary so a distributed dataset can be reproduced later.

## Research / implementation signal

Current data and ML formats emphasize immutable snapshots, checksums, provenance and explicit handling of live datasets. These provide useful design patterns for PollicinoNet without requiring those storage systems themselves.

References:

- https://iceberg.apache.org/spec/
- https://docs.mlcommons.org/croissant/docs/croissant-spec-1.1.html
- https://mlcommons.org/2026/02/croissant-1-1-standard/
