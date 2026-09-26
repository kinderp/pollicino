# UC-120 — Derived-Artifact Invalidation and Recompute Courier

## Idea

When a source document, dataset, model or policy changes, propagate a compact invalidation through PollicinoNet so disconnected caches know which derived artifacts are now stale and which jobs must be recomputed. The frozen LoRa PHY is unchanged.

## Problem solved

Raiatea and AI pipelines create many derived objects, for example source PDF -> OCR -> normalized text -> chunks -> embeddings -> index -> summary. If the source changes, old downstream artifacts can remain on disconnected nodes for days. Lineage tells us where an artifact came from; UC-120 uses that lineage to mark dependents stale and schedule exact recomputation.

## Actors / nodes

Source publisher, lineage catalog, cache/replica holders, transform workers, relay/store-and-forward nodes, reviewer.

## Why PollicinoNet fits

Invalidation metadata is tiny compared with the objects it affects.

- **DISCOVERY:** source/artifact family, current generation, stale/recompute-needed flag.
- **EXACT:** source hash, old/new version hashes, derivation edge IDs, transform/tool version, invalidation event ID and replacement references.
- **SEMANTIC:** human labels such as "OCR stale" or "embedding requires rebuild".

LoRa can carry invalidation and dependency identifiers. BLE/Wi-Fi/LAN carries recomputed artifacts. Physical transport can move large replacement packs.

## Possible bearers

- **LoRa:** invalidation event, lineage edge summary, recompute request/status;
- **BLE:** small replacement metadata or chunks;
- **Wi-Fi/LAN:** new OCR, embeddings, indexes or model artifacts;
- **Internet:** optional source retrieval or cloud recomputation;
- **physical transport:** large rebuilt artifact set.

## What we can test now in software

Create a deterministic mini-pipeline with content-addressed outputs and explicit lineage. Test source revision, tool-version change, transform-parameter change, late arrival of an old derivative, partial invalidation, two successive source revisions while recomputation is in flight, retry producing the same output, and a worker using the wrong dependency version.

Measure stale-artifact lifetime, unnecessary recomputation, bytes moved and whether every final artifact records the exact inputs that produced it.

## What requires real hardware

Use 3–5 boards plus 2–3 laptops/Pi. Keep one cache intentionally disconnected while a source document changes. Relay only the invalidation over LoRa; later move the rebuilt output over Wi-Fi and verify that the old derivative stays visibly stale until replaced.

## Messina teaching scenario

Different student groups hold separate Raiatea caches. A teacher corrects one source handout or replaces a dataset version at school. The invalidation reaches remote caches through student relays before the replacement bulk artifact does, so their local UI can show "stale — replacement pending" rather than serving the old result as current.

## Privacy / security

- use opaque content IDs when filenames or corpus structure are sensitive;
- authenticate invalidation events;
- bind recomputation to exact input hashes and transform versions;
- preserve old derivatives for audit only when retention policy allows;
- do not treat a missing replacement as permission to silently reuse stale output.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-077 propagates deletion tombstones; UC-099 records document-ingestion lineage; UC-107 handles cache freshness. UC-120 propagates **dependency-aware invalidation and recomputation across a derivation graph**.

## Research / implementation signal

W3C PROV and OpenLineage model explicit input/output derivation relationships that can support a practical dependency graph.

References:

- https://www.w3.org/TR/prov-dm/
- https://openlineage.io/docs/spec/facets/job-facets/lineage/
- https://openlineage.io/blog/explicit-lineage/
