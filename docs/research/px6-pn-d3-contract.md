# PX6-PN-D3 contract

This is a validated local experimental primitive, not a stable network API.

## Records and identity

- IDs, query payloads and catalog keys are non-empty `bytes`.
- Query identity is caller-owned. Same ID and same payload is `NOOP_DUPLICATE`; same ID and different payload is `QUERY_CONFLICT`.
- Result identity is caller/responder-owned and scoped by query ID. Same identity and same canonical key tuple is `NOOP_DUPLICATE`; different keys is `RESULT_CONFLICT`.
- Candidate keys are sorted, unique, bounded native D2 logical keys. Empty is valid.
- A result is a candidate statement, not truth, trust, evidence or recommendation.

## Mutation and application boundary

Batch operations stage and commit atomically. Failed validation, conflict, quota or persistence leaves the prior authoritative state unchanged. Application handlers receive opaque bytes and return keys; handler objects are never persisted. Re-execution can occur, so the guarantee is duplicate-safe state, not exactly-once execution.

Receiving a query executes nothing. Receiving a result neither pulls a reference nor fetches/imports content. Local result construction verifies that the responder currently owns each returned catalog key; remote receipt deliberately permits locally unknown keys.

## State and exchange

`pollicino.local-query-result-state.v1` is a deterministic, digest-protected `LOCAL_QUERY_STATE_FORMAT`. Query/result identifier reconciliation and selected record pull use bounded local method calls. The encodings are not a stable network wire protocol.

Equivalent logical state canonicalizes byte-identically regardless of insertion, delivery, restart, persistence generation or path. Catalog and query/result stores are separately durable and are not one ACID transaction.

No TTL, garbage collection, distributed cancellation, ranking, authentication, routing, bearer or network execution is included.
