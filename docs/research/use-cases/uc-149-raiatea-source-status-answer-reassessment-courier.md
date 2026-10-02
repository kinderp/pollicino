# UC-149 — Raiatea Source-Status and Answer-Reassessment Courier

## Problem solved

A cached source can stay available while its status changes: corrected, superseded, withdrawn by its publisher, placed under review, or challenged by later evidence. An offline Raiatea node should not silently serve an old answer as if nothing changed.

UC-149 carries a small source-status update and marks dependent cached answers for reassessment.

## Actors / nodes

Raiatea corpus node, metadata resolver, answer cache, reviewer, Internet gateway and student relay.

## Why PollicinoNet fits

The status update is tiny compared with the document or index. A compact capsule can contain source identifier, source hash when known, update class, update reference and epoch.

Useful states include `CURRENT`, `CORRECTED`, `UNDER_REVIEW`, `SUPERSEDED`, `CONTESTED` and `REASSESS_REQUIRED`.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** source-status and reassessment metadata.
- **BLE:** small metadata bundles.
- **Wi-Fi/LAN:** updated documents, rebuilt index shards and revised answer capsules.
- **Internet:** public metadata lookup when reachable.
- **Physical transport:** larger corpus snapshots.

## What we can test now in software

Build a small public corpus with explicit answer-to-citation links. Then simulate a correction, a publisher withdrawal, a later source that challenges an earlier claim, an unresolved review state and an old answer arriving after the status update.

Measure whether dependent answers become `REASSESS_REQUIRED` while their historical provenance remains visible.

Crossref/Crossmark metadata can supply real public update examples.

## What requires real hardware

Use 3–5 LoRa boards and 2–3 laptops/Pi holding different corpus subsets. Keep one corpus island offline while another learns a source-status change. Ferry the compact status first, then bring the replacement material later over Wi-Fi.

## Messina teaching scenario

Split a public-document collection across Messina, Villafranca and Rometta/Venetico-Spadafora. A group obtains a Raiatea answer from its local corpus. Later a relay brings a source-status update from another island, forcing the cached answer into reassessment.

## Privacy / security

Use public documents first. Accept formal source-status changes only from configured metadata sources. Preserve old source and answer hashes for audit instead of rewriting history. Keep query metadata minimal because topic interests can be sensitive.

A source-status change does not automatically prove that every claim in the source is false; keep those states separate.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-120 handles derived-artifact invalidation. UC-136 resolves missing references. UC-147 handles missing evidence. UC-149 handles a **later change in the status of evidence already present**.

## Research / standards signal

Crossref/Crossmark already exposes corrections and other significant publication updates as machine-readable metadata, making this a practical Raiatea workflow rather than a hypothetical one.
