# UC-136 — Raiatea Citation-Graph Resolution and Missing-Reference Courier

## Idea

Let an offline Raiatea corpus identify unresolved citations or references, emit compact resolution jobs, and receive normalized bibliographic metadata or an open-access locator later when a gateway or richer corpus becomes reachable.

The source document stays local; the network first moves the missing-reference question.

## Problem solved

A document collection may contain DOI strings, titles, author-year references or broken URLs that cannot be resolved while the node is offline.

Without an explicit workflow, a local index can silently lose citation edges, duplicate the same work under different names, or treat an unresolved reference as if it did not exist.

UC-136 turns missing references into small versioned jobs and keeps the resulting citation edge bound to the exact source document and resolver evidence.

## Actors / nodes

Raiatea corpus/index node, citation extractor, student relay/store-and-forward nodes, optional Internet gateway, bibliographic metadata cache, reviewer and provenance collector.

## Why PollicinoNet fits

A citation-resolution request is tiny compared with the source PDF or corpus. LoRa can carry reference fingerprints, DOI/title hints, status and result-ready metadata while richer bearers return complete metadata or public documents when appropriate.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: source-document hash, local reference ID, DOI or compact fingerprint, resolution status and result hash.
- BLE: nearby bibliographic-cache exchange.
- Wi-Fi/LAN: full metadata records, citation-graph fragments and open documents.
- Internet: Crossref, OpenAlex or another approved public resolver.
- Physical transport: a laptop or removable cache can carry larger metadata snapshots.

## What we can test now in software

Create a public mini-corpus with known references and deliberately remove some metadata.

Test exact DOI lookup, title/author fuzzy candidate generation, duplicate references, conflicting metadata sources, retracted or updated works, unresolved references, stale metadata and one resolver going offline.

Use explicit states such as RESOLVED_EXACT, CANDIDATE_REVIEW, CONFLICT, NOT_FOUND, SOURCE_UNAVAILABLE and STALE.

Measure recovered citation edges, false matches, unresolved references and bytes moved.

## What requires real hardware

Use 3–5 boards and two or three laptops or Pi nodes holding different metadata caches. Keep one group disconnected from Internet and let a student relay carry citation jobs toward a gateway or richer cache, then bring results back.

The physical experiment measures delay and successful job/result movement only. It does not claim completeness of external bibliographic databases.

## Messina teaching scenario

Different student groups index public teaching papers or technical documents in Messina, Villafranca and Rometta/Venetico. One corpus contains references that its local cache cannot resolve.

The unresolved reference capsules travel through the student relay network. A later gateway contact resolves some identifiers, and the normalized results return to the originating Raiatea node without moving the whole source corpus.

## Privacy / security

Use public documents in first experiments. Treat titles, authors and DOI queries as potentially revealing reading interests; minimize broadcast metadata, prefer opaque job IDs on LoRa, authenticate result provenance, and require review for fuzzy matches.

A bibliographic match must never silently rewrite the original citation text.

## Difficulty

Medium. Exact DOI resolution is simple; fuzzy candidate handling, conflict provenance and offline cache freshness make the full workflow more interesting.

## Why this is distinct

UC-034 moves semantic queries to corpora, UC-065 merges multi-corpus search results, UC-088 fetches a bounded Web/API resource and UC-099 tracks document-ingestion lineage. UC-136 maintains the citation graph itself by resolving missing references as first-class delayed jobs.

## Research / implementation signal

Crossref exposes public bibliographic metadata through its REST API, while OpenAlex models works and citation relationships as a connected graph. These are useful external resolvers, but PollicinoNet should preserve source provenance and explicit unresolved or conflicting states.

References:

- https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- https://help.openalex.org/data/works/
