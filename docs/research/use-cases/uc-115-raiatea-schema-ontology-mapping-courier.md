# UC-115 — Raiatea Schema and Ontology Mapping Courier

## Idea
Allow disconnected Raiatea corpora that use different metadata schemas or vocabularies to exchange compact, versioned mappings so a query or document can be interpreted consistently without centralizing all content.

## Problem solved
Two offline collections may describe the same concept differently: `author` vs `creator`, different subject taxonomies, old/new field names, or local codes. Search may fail even though the relevant document exists.

## Actors / nodes
Corpus/index nodes, mapping publisher, query requester, relay/store-and-forward nodes, optional reviewer.

## Why PollicinoNet fits
- **DISCOVERY:** schema/ontology ID and version, supported mapping pairs.
- **EXACT:** source schema hash, target schema hash, mapping version, rule IDs, provenance and review state.
- **SEMANTIC:** human-readable labels/examples.

LoRa carries mapping IDs and capability summaries; BLE/Wi-Fi/LAN carries full mapping bundles or affected index fragments.

## What we can test now in software
Create three small corpora with intentionally different metadata schemas. Test direct mappings, chained mappings, conflicting rules, unknown fields, stale mappings and one corpus offline. Measure recovered search hits, false mappings and bytes moved.

## What requires real hardware
Use 3–5 board nodes and 2–3 laptops/Pi holding separate Raiatea corpora. Keep documents local and ferry only mapping/control state first.

## Messina teaching scenario
Different student groups can index separate school document collections with slightly different schemas, then reconnect indirectly and test whether one query can find equivalent material across all corpora.

## Privacy / security
Mappings may reveal internal vocabulary; use opaque schema IDs where needed, authenticate reviewed mappings, and never let an unreviewed semantic guess overwrite exact source metadata.

## Difficulty
**Medium–High.**

## Why this is distinct
UC-065 merges results from multiple corpora and UC-099 tracks ingestion lineage; UC-115 solves **schema/ontology interoperability between disconnected corpora**.
