# PX5 PN-D2R — exact PX3 surface audit

PX5 is based directly on PX3 final
`6dbc79e3cfff1a34a90d42e703bcc4124b9cf5ea`. The authoritative module is
`src/pollicino/net/catalog.py`; PX5 does not change it.

`BoundedReference` validates non-empty byte keys and opaque byte values against
the global 256/4096-byte ceilings. `CatalogLimits` can only narrow the key,
value, item, byte and 100-item exchange bounds. `BoundedReferenceCatalog`
provides atomic `add`/`add_many`, `get`, local advertisement-only `remove`,
sorted ID and full-reference pages, known/unknown comparison, selected pull,
canonical state decode/encode and a state digest. Exact duplicates return
`NOOP_DUPLICATE`; byte-distinct values under one key raise
`ReferenceConflictError`; quota failures raise `CatalogBoundsError` before
state publication.

The PX3 local canonical payload is `PRCS` version 1 with item count, payload
byte count, body digest and length-prefixed sorted entries. Its decoder rejects
bad magic/version, duplicate keys, truncation, trailing data, digest/count
mismatch and active-bound violations. `reconcile_and_pull` remains the only
semantic source for candidate/selection/pull reconciliation.
