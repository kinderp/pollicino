# UC-034 — Raiatea Query-to-Data Search Courier

## Idea

Move the **query to the node that already has the corpus**, rather than moving the whole corpus to the requester.

A student, teacher or field node sends a compact structured search request through PollicinoNet. A node that owns the relevant Raiatea/document index performs the search locally and returns a small ranked result set with exact document/object references. Only the selected document or evidence is fetched later if needed.

## Problem solved

Offline document collections can be large while a user's actual information need is small.

Example:

```text
corpus on school node: 20 GB
user need: "find the paragraph about Capability Resolver"
useful answer: 3 document/object references + snippets
```

Copying the whole corpus or vector index to every disconnected node wastes storage and bandwidth. The better question is: can the query travel to the data and can a compact, verifiable result travel back?

## Actors / nodes

- student/teacher requester;
- Raiatea/document corpus node;
- school server, NAS or edge search node;
- student relay/store-and-forward nodes;
- optional local embedding/search model;
- optional richer-bearer provider for selected result documents.

## Why PollicinoNet fits

This is naturally delay tolerant because a search request can wait in a queue until it reaches a node that owns the right index.

- **DISCOVERY:** which node/index may answer a corpus/query class;
- **EXACT:** corpus/index version, query ID, result object hashes, document IDs and exact evidence references;
- **SEMANTIC:** natural-language query, tags, embedding/search interpretation and ranking.

The semantic result is always tied back to exact versioned corpus/object identities so a later document retrieval cannot silently return a different version.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** compact query envelope, index/corpus version, status, top-result identifiers and small snippets when size permits;
- **BLE:** nearby result/evidence exchange;
- **Wi-Fi/LAN:** selected documents, larger result sets, embeddings or index fragments;
- **Internet:** optional fallback search/provider;
- **physical transport:** a student node carries queued queries to a school/home corpus and carries results back later.

## What we can test now in software

Create a small versioned Raiatea-like corpus and simulate a requester that cannot directly reach it.

Test:

- exact corpus/index version binding;
- lexical and/or small semantic search performed where the corpus lives;
- top-k result envelopes with exact object references;
- delayed query delivery and delayed result return;
- duplicate query suppression and idempotent result generation;
- stale index response after corpus version changes;
- query routed to two candidate corpus nodes and deterministic reconciliation of results;
- selective fetch of only one chosen document after result discovery;
- comparison of `move corpus/index to requester` vs `move query + result references`;
- integration with UC-024 `ContentNeed` for the final exact document fetch;
- optional local small-model reranking without making cloud AI mandatory.

Useful metrics include query-envelope size, result-envelope size, time-to-first-result, bytes avoided, stale-result rate and selected-document fetch bytes.

## What requires real hardware

- 3+ PollicinoNet nodes with one disconnected requester, one relay and one corpus/search node;
- real queue carry through at least one store-and-forward hop;
- optional LoRa return of a tiny result set;
- real BLE/Wi-Fi handoff for the selected document using UC-033;
- measured end-to-end query turnaround under controlled contacts.

No claim about LoRa carrying embeddings, full indexes or large snippets should be made before measuring actual encoded sizes and airtime.

## Messina teaching scenario

Place a small versioned educational corpus on a school/server node. A student node in another network island asks a question while the school node is unreachable.

A second student's PollicinoNet node later encounters the requester, carries the query, reaches the school/corpus node, receives a compact result envelope and eventually brings it back.

The requester can then choose one exact source document. Only that source is transferred on a richer bearer.

This makes a useful classroom demonstration because the visible result is not merely "a packet arrived": a real offline question gets answered without synchronizing the complete knowledge base first.

## Privacy / security

Queries can reveal interests, projects or sensitive topics even when the documents themselves are public.

Therefore:

- encrypt query envelopes for authorized search providers where appropriate;
- expose only the minimum corpus-discovery metadata;
- bind every result to corpus/index version and query ID;
- treat semantic ranking as non-authoritative;
- verify exact result/evidence object identity before use;
- avoid sending private full-document context to untrusted relay nodes;
- define retention for queued queries and returned search history.

A relay may carry encrypted queries/results without being authorized to inspect them.

## Difficulty

**Medium–High.** The first prototype is straightforward with a small corpus, but robust semantic search introduces versioning, privacy, index compatibility and ranking/provenance questions.

## Research signal

Offline/on-device RAG and edge retrieval continue to move retrieval closer to private data. Recent work demonstrates private local document search on edge devices and research on distributed/edge RAG scheduling. PollicinoNet's distinctive experiment is not the retriever itself but the delay-tolerant **query-to-data courier** around it.

References:

- https://github.com/VAGOsolutions/colgemma4-on-edge
- https://api.emergentmind.com/topics/coedge-rag
- https://www.microsoft.com/en-us/research/publication/revela-dense-retriever-learning-via-language-modeling/
