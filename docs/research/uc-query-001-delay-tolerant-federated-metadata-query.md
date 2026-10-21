# UC-QUERY-001 — Delay-tolerant federated metadata query

Status: PRIMARY / PROTOTYPE-DRIVING integration

## Problem

`UC-CONTENT-002` lets a node discover references from peer catalogs it encounters. A different problem is **active asynchronous search**: a user asks a question now, no relevant provider is currently reachable, the query is carried through the network, several disconnected indexes answer later, and compact result references eventually return along different paths.

Example: a student or teacher asks for "documents about LoRa link budgeting", "the latest authorized lab worksheet for topic X", or "which local Raiatea index knows this hash?". PollicinoNet should not move the full documents over LoRa; it should move the query identity, bounded search terms/fingerprints and later compact result references.

## Actors / nodes

- query-origin node;
- student-carried relay nodes;
- school mixing hub;
- home/school Raiatea or document-index node;
- optional NAS/local library index;
- optional Internet-connected resolver;
- result consumer.

## Why PollicinoNet fits

This workload is naturally asynchronous and disruption-tolerant:

- request and response may take different physical paths;
- providers may answer hours later;
- duplicate queries must not trigger unbounded repeated work;
- responses can be partial and arrive out of order;
- only references/metadata should cross scarce links;
- rich content is retrieved later on Wi-Fi/LAN/Internet.

It also creates a concrete integration point between PollicinoNet and Raiatea without coupling the network core to a document-search implementation.

## Possible bearers

- LoRa: compact query envelope, provider hit summaries, object/reference IDs and receipts;
- BLE: local query handoff to a nearby companion/index node;
- Wi-Fi/LAN: execute full-text/vector/metadata search on local indexes and retrieve documents;
- Internet: optional remote search/resolution when authorized;
- physical carry: student nodes ferry query and result state between school/home/territorial clusters.

## Minimal application model

A first fixture can use:

```text
query_id
query_class
terms_or_fingerprint
scope/topic
created_at
usefulness_deadline
max_results
result_reference_type
privacy_class
```

Responses can contain only:

```text
query_id
provider_pseudonym
result_generation
rank_hint
reference/hash/coordinate
small public metadata
```

No production query wire format is authorized by this use case.

## What we can test immediately in software

Create 4 disconnected metadata indexes with deliberately overlapping catalogs.

Experiments:

1. query starts in one territorial cluster and no provider is directly reachable;
2. two student mules carry the same query to different providers;
3. providers return overlapping hits through different paths;
4. one response arrives after the usefulness deadline;
5. one provider is offline until the next morning school mixing phase;
6. query is replayed and must not trigger unbounded duplicate work;
7. result limit is 5 while providers collectively know 100 matching references;
8. compare direct-only, flood-query, bounded replication and simple provider/capability-guided forwarding.

Measure:

- time to first useful hit;
- time to top-k convergence;
- query/result wire bytes;
- duplicate provider work;
- duplicate results;
- stale results;
- useful references returned per scarce-link byte;
- later exact rich-link resolution success.

## Messina student-network scenario

Use logical clusters labelled Rometta-like, Spadafora-like, Saponara-like and school-hub. A query created in one cluster can be carried to a home Raiatea/NAS index in another area, with results returning during the next school mixing phase.

Town labels are scenario names only; they do not imply LoRa reachability between towns.

## What requires real hardware

After HW-006:

- real request/result latency under student mobility;
- real number of query/result envelopes per encounter;
- interaction with the node bearer runtime across school mesh -> carry -> home Wi-Fi;
- restart/persistence behavior on boards;
- UI usability for deferred results.

Actual Raiatea integration requires its rights/provenance policy to remain authoritative for document access.

## Privacy and security

Queries can reveal interests. Therefore:

- start with public course topics and synthetic queries;
- avoid student names or sensitive personal interests;
- support coarse topic classes before arbitrary plaintext search text on LoRa;
- authenticate providers before trusting result provenance;
- keep authorization separate from discovery: finding a reference does not grant access;
- apply TTL/deadline and bounded result counts;
- retain query logs only as needed for the experiment.

## Difficulty

**Medium.** The transport model already fits; the main work is query deduplication, asynchronous result merging and a clean adapter to Raiatea/local indexes.

## Success / kill criteria

Continue if active query propagation returns useful references in regimes where passive encountered-catalog discovery cannot, with bounded duplicate work and substantially fewer scarce-link bytes than moving full catalogs or documents.

If passive `UC-CONTENT-002` discovery performs equivalently with much less application state, keep QUERY as a deferred specialization rather than a core feature.

## Physical evidence boundary

All initial results are `MODEL_SYNTHETIC`. No real Messina coverage/contact-capacity claim is permitted before HW-006. The frozen LoRa PHY and 42-byte / 2 dBm first campaign remain unchanged.