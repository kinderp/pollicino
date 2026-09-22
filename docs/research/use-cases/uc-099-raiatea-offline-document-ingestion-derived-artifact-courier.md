# UC-099 — Raiatea Offline Document Ingestion and Derived-Artifact Courier

## Idea

Let a document enter PollicinoNet at one disconnected node and let **different edge nodes progressively derive useful artifacts** from it — OCR text, normalized text, thumbnails, chunks, embeddings, indexes or metadata — while every derived object remains bound to the exact source hash and tool/version that produced it.

The key idea is:

> move the document only when necessary; move compact jobs, hashes and provenance first.

This is a Raiatea-oriented ingestion pipeline for places where no single always-online server can perform the whole workflow.

## Problem solved

A photographed page, scanned public document or local PDF may be available at a student node but not yet searchable in Raiatea. Converting it into useful searchable material can require capabilities that are scattered across devices:

- one phone can capture the source;
- one laptop can OCR it;
- another machine can normalize/chunk it;
- an edge GPU can compute embeddings;
- the school workstation can build an index;
- the final corpus may be offline while the processing steps happen.

If intermediate files are copied manually, provenance is easily lost: an embedding may no longer be clearly tied to the exact OCR text or source image that created it.

## Actors / nodes

- document capture/source node;
- student relay/store-and-forward nodes;
- OCR/text-extraction worker;
- normalization/chunking worker;
- optional embedding/index worker;
- Raiatea corpus/index node;
- provenance verifier.

## Why PollicinoNet fits

The control objects are tiny compared with page images, PDFs and vector/index artifacts.

- **DISCOVERY:** worker advertises capabilities such as `ocr`, `pdf-text`, `thumbnail`, `chunk`, `embed:model-X`, `index:format-Y`;
- **EXACT:** source content hash, derivation recipe/version, worker/runtime identity, derived-artifact hash, parent hash and schema;
- **SEMANTIC:** labels such as `ocr-complete`, `embedding-ready`, `indexable` or `failed-quality-check` are derived from the exact lineage.

LoRa is therefore useful for capability/job/result discovery, while the large bytes move over richer links or physically.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** source manifest digest, job request, capability advertisement, artifact-ready notice, hash and compact provenance edge;
- **BLE:** thumbnails, short text excerpts or bootstrap exchange;
- **Wi-Fi/LAN:** page images, PDFs, OCR text, embeddings and index shards;
- **Internet:** optional access to a cloud OCR/embedding worker when policy permits;
- **physical transport:** phone/laptop/SD carries original scans or large derived artifacts.

## What we can test now in software

Use only public-domain or synthetic documents initially.

Define a `DocumentSource`:

```text
source_id
source_hash
media_type
page_count_optional
capture_profile_optional
rights_policy_id
```

Each processing step produces a `DerivationRecord`:

```text
parent_hash
operation
recipe_version
tool_or_model_id
tool_or_model_hash_optional
runtime_profile
parameters_hash
output_hash
quality_summary
worker_pseudonym
status
```

Test a small DAG such as:

```text
PDF/image
   -> OCR text
      -> normalized text
         -> chunks
            -> embeddings
               -> Raiatea index shard
```

Inject failures and ambiguity:

- two OCR workers produce different text from the same page;
- one worker uses a different OCR model/version;
- derived artifact arrives before the parent artifact;
- duplicate job execution;
- corrupt artifact with a valid-looking filename but wrong hash;
- low OCR-confidence result that must not silently become authoritative;
- embedding generated from stale normalized text;
- requested model/runtime unavailable;
- rights/policy envelope forbids one transformation or redistribution step;
- index rebuild after one upstream artifact changes.

Useful metrics include bytes moved per stage, duplicate compute rate, derivation latency, provenance completeness, cache-hit rate and percentage of final index entries traceable back to an exact source hash.

## What requires real hardware

A first physical experiment can use ordinary equipment already available:

- 3–4 LoRa nodes;
- one phone or scanner;
- two laptops/Raspberry Pi class workers;
- optionally one more capable local AI machine;
- a Wi-Fi hotspot used only during rich-bearer handoff.

Suggested test:

1. capture a public document at one isolated node;
2. announce only its source manifest over LoRa;
3. let a second node discover and execute OCR;
4. let a third node receive the derived text later and build chunks/embeddings;
5. ingest the final exact artifacts into a local Raiatea test corpus;
6. verify the complete lineage back to the source hash.

Any throughput, transfer-time or energy claim must come from the measurements of that experiment.

## Messina teaching scenario

Different student groups hold different public local-history or school-created documents at checkpoints in Messina, Villafranca, Rometta/Venetico and Spadafora. A document does not need to travel immediately to the school server.

A relay can carry a compact request such as:

```text
source = sha256:...
need = ocr/it
recipe = ocr-profile-3
```

A capable laptop later produces the text, another node generates searchable chunks, and the school Raiatea node eventually receives only the verified derived artifacts it needs.

The class can inspect the derivation graph and learn the difference between **file name**, **content identity** and **provenance**.

## Privacy / security

- start with public-domain, synthetic or school-authored material;
- do not ingest personal/student documents without explicit authorization;
- content hashes can themselves reveal membership in a known corpus, so avoid broadcasting sensitive hashes globally;
- sandbox OCR/parsing/indexing workers because documents may be malicious inputs;
- strip active content/macros before processing where appropriate;
- bind every derived artifact to exact parent hashes and recipe/tool versions;
- never treat OCR confidence or an LLM-generated extraction as ground truth;
- enforce UC-076-style rights/policy checks before transformations or redistribution;
- preserve the original source separately so later processing can be audited;
- encrypt sensitive rich-bearer transfers end-to-end.

## Difficulty

**High.** Individual transforms are easy; reliable lineage, heterogeneous workers, partial arrival and safe document processing make the end-to-end pipeline substantial.

## Why this is distinct from nearby use cases

- **UC-006:** distributes already-known exact Raiatea documents; UC-099 creates and ferries *derived searchable artifacts* from a new source.
- **UC-034:** sends a query to an existing corpus; UC-099 builds the corpus/index inputs in the first place.
- **UC-046:** returns an answer capsule from indexed material; UC-099 concerns ingestion and derivation before question answering.
- **UC-057/078:** move generic inference/compute jobs; UC-099 defines a document-specific provenance DAG and Raiatea ingestion contract.
- **UC-076:** carries usage policy; UC-099 can consume that policy during every derivation step.

## Research / implementation signal

W3C PROV models entities, activities and derivations explicitly, including relationships such as an entity being derived from another entity. That maps naturally to a content-addressed offline document pipeline. PollicinoNet does not need to implement the full PROV stack initially, but the model is a useful reference for preserving exact lineage across asynchronous workers.

References:

- https://www.w3.org/TR/prov-overview/
- https://www.w3.org/TR/prov-primer/
- https://www.w3.org/TR/prov-n/
