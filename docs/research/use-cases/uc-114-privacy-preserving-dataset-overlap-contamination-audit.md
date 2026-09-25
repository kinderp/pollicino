# UC-114 — Privacy-Preserving Dataset Overlap and Contamination Audit

## Idea

Let disconnected dataset holders estimate whether corpora overlap without first copying complete datasets to one place. Compact fingerprints or sketches move first; exact records move only when policy permits and evidence is needed.

## Problem solved

AI evaluation can be misleading when evaluation examples or near-duplicates already appear in training data. Distributed projects make this harder because datasets may live on different laptops, school machines or offline caches.

## Actors / nodes

- dataset holders;
- benchmark/evaluation holder;
- optional coordinator;
- relay/store-and-forward nodes;
- local fingerprint worker;
- reviewer who may authorize selected evidence disclosure.

## Why PollicinoNet fits

- **DISCOVERY:** dataset ID/version, approximate record count, method/version and willingness to compare;
- **EXACT:** dataset manifest hash, normalization rule, exact-record hashes, sketch parameters, audit request ID and evidence IDs;
- **SEMANTIC:** labels such as `train`, `eval`, `benchmark` or `RAG corpus` aid interpretation only.

LoRa carries small audit requests/results; BLE/Wi-Fi/LAN or physical transport carries larger sketches and selected evidence. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** audit request, dataset/version IDs, compact result/status;
- **BLE:** small fingerprint batches;
- **Wi-Fi/LAN:** larger sketches, embeddings and authorized examples;
- **Internet:** optional public benchmark retrieval;
- **physical transport:** encrypted dataset/sketch packs where policy permits.

## What we can test now in software

Use public or synthetic datasets with known injected overlap. Compare:

1. exact cryptographic hash after deterministic normalization;
2. token n-gram overlap;
3. MinHash/LSH for approximate set similarity;
4. perceptual hash for media where appropriate;
5. embedding similarity as a higher-cost semantic signal.

Inject exact duplicates, formatting changes, excerpts, paraphrases, image transformations, version drift and incomplete evidence.

Measure false positive/negative rates, bytes moved, disclosure surface and the difference between `NO_OVERLAP_FOUND` and `AUDIT_INCOMPLETE`.

> A compact sketch is screening evidence, not proof that two private datasets are clean.

## What requires real hardware

A first experiment can use 4–6 board nodes and 2–3 laptops/Pi holding distinct public or synthetic dataset partitions. Only audit metadata crosses LoRa; selected evidence can later cross BLE/Wi-Fi.

## Messina teaching scenario

Split a synthetic/public classroom dataset among disconnected groups. Secretly inject exact and near-duplicate evaluation samples into one training partition. Each group keeps raw data local and exchanges only audit manifests/fingerprints first.

## Privacy / security

- do not assume Bloom filters, MinHash or hashes are anonymous;
- use keyed/salted fingerprints when cross-epoch linkability is unnecessary;
- authorize membership-style queries;
- rate-limit repeated probing;
- use public/synthetic personal-data-free corpora initially;
- preserve consent and usage-policy metadata;
- distinguish overlap evidence from legal conclusions.

## Difficulty

**Medium–High.**

## Why this is distinct

- **UC-056:** consent-bound data donation.
- **UC-100:** demand sketches for caching.
- **UC-110:** near-duplicate visual evidence for transfer efficiency.
- **UC-114:** cross-dataset train/eval/benchmark overlap auditing while full datasets stay distributed.

## Research / implementation signal

Benchmark contamination remains an active 2026 concern. ACL 2026 work studies contamination detection and statistically controlled filtering.

References:

- https://aclanthology.org/2026.acl-long.1390/
- https://aclanthology.org/2026.acl-long.926/
- https://aclanthology.org/2026.findings-acl.252/
