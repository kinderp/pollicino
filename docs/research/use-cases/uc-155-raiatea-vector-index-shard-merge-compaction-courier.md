# UC-155 — Raiatea Vector-Index Shard Merge and Compaction Courier

## Problem solved

Disconnected Raiatea nodes may independently build vector-index shards from different public document subsets. Later, keeping many separate indexes can make query execution more expensive, while rebuilding everything from the original corpus may be unnecessary.

UC-155 studies how to advertise compatible shards, move them to a suitable worker, merge or compact them, and preserve exact document/vector lineage.

## Actors / nodes

Raiatea corpus/index nodes, embedding workers, shard builders, a merge worker, student relay/store-and-forward nodes, query nodes and a provenance verifier.

## Why PollicinoNet fits

The index files are large, while the control state is compact: shard identity, source snapshot, embedding-model version, metric, dimensionality, vector count, build profile, compatibility state, merge job and output identity.

LoRa carries compact manifests and job state. BLE/Wi-Fi/LAN or school-managed physical storage carries vector/index files. The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** shard manifest digest, compatibility summary and merge status.
- **BLE:** small manifests.
- **Wi-Fi/LAN:** vector shards, index files and evaluation data.
- **Internet:** optional artifact or compute source.
- **Physical transport:** school-managed storage for large shards.

## What we can test now in software

Build 3–5 independent indexes from partitions of a public corpus and compare:

1. search every shard separately and merge rankings;
2. rebuild one unified index;
3. merge compatible existing indexes where the selected library or algorithm supports it;
4. reject incompatible shards produced with a different embedding model, metric or dimensionality.

Also test duplicate documents, stale shards, interrupted merge, late shard arrival and output validation.

Measure merge bytes, compute time, storage overhead, query latency and retrieval quality on a fixed public evaluation set. External paper results are design references only, not PollicinoNet measurements.

## What requires real hardware

Use 4–6 LoRa boards and at least three laptops/Pi/workstations holding different public index shards. LoRa advertises manifests and merge state; larger files move over a rich bearer. Transfer time and energy require physical measurement.

## Messina teaching scenario

Groups in Messina, Villafranca and Rometta/Venetico-Spadafora build compatible Raiatea shards from different parts of one open corpus. Student relays move only the compact manifests. A capable workstation consolidates compatible shards, after which the class compares search before and after compaction.

## Privacy / security

Use public corpora first. Treat embeddings and indexes according to the sensitivity of the source corpus. Preserve source-shard lineage, tool versions and policy references in every merged artifact.

## Difficulty

**High.**

## Why this is distinct

UC-065 federates search across several corpora. UC-099 builds document-derived artifacts and index shards. UC-155 focuses on consolidating already-built compatible vector-index shards.

## Research signal

Efficient vector-index merging is an active database topic in 2026. A concrete reference is L. Jing et al., “Multiple Index Merge for Approximate Nearest Neighbor Search,” arXiv:2602.17099 (2026).
