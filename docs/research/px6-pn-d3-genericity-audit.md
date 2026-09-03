# PX6-PN-D3 genericity audit

Core files audited:

- `src/pollicino/net/query.py`
- `src/pollicino/net/persistent_query.py`
- `src/pollicino/net/local_persistence.py`

Case-insensitive searches for `faro`, `registryquery`, `publisher`, `evidence`, `recommendation`, `content`, `torrent`, `magnet`, `dna`, and `topic` returned zero core occurrences. Application terms occur only in tests and research documents.

`APPLICATION_SPECIFIC_QUERY_CORE_BRANCHES = 0`.

The same records, store, persistence codec and reconcile/pull functions serve the FARO and synthetic lawful CONTENT-like fixtures. Core validation is limited to bytes, sizes, counts, uniqueness, ordering, correlation, local catalog membership when creating a local response, persistence integrity and conflicts.

No application callback is persisted. No PR #52 symbol, runtime, PNB1/PNC1, socket or bearer is imported. Query opacity is a semantic boundary only: `OPAQUE_TO_POLLICINO != ENCRYPTED`.
