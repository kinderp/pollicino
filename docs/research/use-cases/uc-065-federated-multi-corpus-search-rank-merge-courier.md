# UC-065 — Federated Multi-Corpus Search and Rank-Merge Courier

## Idea

Send one search intent to **several independent document/index nodes**, let each search only the corpus it actually owns, and merge the partial ranked results after they return through intermittent contacts.

This extends UC-034 in an important direction. UC-034 moves a query to a corpus node and gets a result back. UC-065 assumes **no single node has the complete knowledge base**: one school/laptop may hold course material, another Raiatea node project notes, another a technical manual archive. Results arrive at different times and must remain attributable to the corpus/version that produced them.

## Problem solved

A distributed/offline knowledge network should not require every corpus to be copied into one central search index.

Suppose a student asks:

```text
"Where is the handoff protocol documented?"
```

Three disconnected nodes may eventually answer:

```text
Corpus A -> results A1, A2
Corpus B -> results B1, B2, B3
Corpus C -> no match
```

The requester should be able to obtain a useful merged answer while preserving:

- which corpus produced each result;
- exact corpus/index version;
- ranking method/version;
- document hashes/evidence refs;
- explicit knowledge that some sources have not replied yet.

## Actors / nodes

- student/teacher requester;
- several Raiatea/document/search nodes with different corpora;
- student relay/store-and-forward nodes;
- optional school aggregator/merge node;
- optional local lexical/vector/reranking services;
- optional richer-bearer providers for selected documents.

## Why PollicinoNet fits

Federated search is naturally asynchronous when corpora are intermittently reachable.

- **DISCOVERY:** corpus/search capability, namespace/topic hint and query acceptance;
- **EXACT:** query ID, corpus ID/version, index version, result document/object hashes and merge-policy version;
- **SEMANTIC:** natural-language query, local ranking scores and merged relevance ordering.

The network can carry tiny query/result metadata first. Exact documents move only if the user selects them, via UC-024/UC-033.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** query ID, compact corpus capability, top result IDs/scores/ranks when encoded size permits, completion/partial-state flags;
- **BLE:** nearby result synchronization and short snippets;
- **Wi-Fi/LAN:** full result sets, selected documents, embeddings or index fragments;
- **Internet:** optional additional corpus provider;
- **physical transport:** a student node carries a query to multiple corpus islands and returns partial results later.

## What we can test now in software

Create three or more small, intentionally different versioned corpora and independent search indexes.

Test:

- broadcast/forward one canonical `FederatedQuery` to several providers;
- asynchronous result arrival in different orders;
- result envelopes bound to corpus/index version;
- duplicate documents existing in multiple corpora;
- source-specific score scales that cannot safely be compared directly;
- simple rank fusion such as Reciprocal Rank Fusion (RRF);
- source weighting only when explicitly configured;
- one corpus timing out or never replying;
- late result incorporation without silently changing an already displayed answer;
- query cancellation/expiry;
- stale-index detection;
- deterministic merge given the same exact set of result envelopes;
- exact evidence retrieval only for selected items;
- comparison with the UC-034 single-corpus baseline.

Useful metrics include time-to-first-result, time-to-k-source-result, bytes per provider, number of distinct useful documents found, duplicate-result rate, merge stability and final evidence-fetch bytes.

A key invariant is:

> partial search must remain visibly partial; absence of a reply from a corpus is not evidence that the corpus contains no match.

## What requires real hardware

- 4+ nodes: requester, at least two independent corpus/search providers and one moving relay;
- different document sets on the providers;
- real delayed delivery of the same query to multiple islands;
- LoRa exchange of compact query/result metadata;
- at least one rich-bearer retrieval of a chosen document;
- measured turnaround as the number/order of responding corpora changes.

Do not claim search-quality improvements from the network experiment without a separate relevance evaluation dataset. Network completeness and information-retrieval quality are different measurements.

## Messina teaching scenario

Place different teaching corpora on separate nodes: for example a school node in Messina with course notes, a laptop associated with a `Rometta/Venetico` group with project documentation, and another node in `Spadafora/Milazzo` with manuals/reference material.

A requester issues one question while none of the providers is directly reachable. Student relays carry the query during ordinary controlled movement. Partial result envelopes return independently. The requester first sees `1/3 sources answered`, later `2/3`, and finally merges the available ranked lists while keeping each evidence reference tied to its origin.

This creates a visible Raiatea experiment in which knowledge stays where it already lives.

## Privacy / security

Queries and corpus inventories can reveal sensitive interests or document holdings.

- encrypt queries for authorized providers when appropriate;
- keep discovery metadata coarse;
- do not expose private corpus titles in broadcast capability messages;
- authenticate provider/result identity;
- bind every result to exact corpus/index version;
- treat ranking as advisory, not authoritative;
- preserve source provenance after merging;
- define retention for query history and partial results;
- prevent a malicious provider from fabricating another provider's result envelope.

## Difficulty

**High.** Sending queries is easy. Correct asynchronous completeness semantics, heterogeneous ranking, duplicate-document reconciliation, provenance and privacy make the full experiment substantially richer than a single-corpus search courier.

## Research / deployment signal

Modern search systems routinely combine results from multiple indexes or retrieval methods and use rank-fusion techniques such as RRF to merge rankings without assuming directly comparable raw scores. Recent work also studies merging distributed approximate-nearest-neighbor indexes. UC-065 applies the result-merging idea to a delay-tolerant environment where the individual indexes may never be online at the same time.

References:

- https://docs.opensearch.org/latest/sql-and-ppl/ppl/commands/multisearch/
- https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/
- https://arxiv.org/abs/2603.21710
