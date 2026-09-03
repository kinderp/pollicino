# PX6-PN-D3 data model and preregistration

## Compared models

| Model | Finding |
|---|---|
| A — opaque query plus catalog-key results | Selected. It keeps meaning in the application while connecting directly to D2 selected pull. |
| B — opaque query plus opaque result bytes | Rejected for PX6. Every application would have to duplicate bounded key-list framing and validation. |
| C — query/result objects in the reference catalog | Rejected. Discovery intent is not durable reference knowledge. |

Decision: `OPAQUE_QUERY_PLUS_CATALOG_KEY_RESULTS`.

`QueryRecord` contains a caller-owned byte `query_id` and opaque query bytes. `ResultRecord` contains caller/responder-owned `(query_id, result_id)` and a sorted tuple of native catalog byte keys. Identity is not derived from query meaning.

Duplicate candidate keys are rejected. Empty results are valid and explicitly mean answered with no matches. A remote result may contain keys absent locally; a locally created result is checked against the responder's current D2 catalog.

Out-of-order results are accepted as bounded persistent orphans. They are not returned as actionable results until the matching query arrives. Correlation occurs automatically from the byte query ID; no catalog, trust, fetch or import mutation occurs.

## Bounds preregistered before the final validation matrix

| Bound | Value |
|---|---:|
| query ID | 128 bytes |
| opaque query payload | 4,096 bytes |
| result ID | 128 bytes |
| native catalog key | 256 bytes |
| keys per result | 100 |
| stored queries | 10,000 |
| stored results total | 10,000 |
| results per query | 100 |
| orphan results | 1,000 |
| aggregate application payload | 16 MiB |
| exchange page | 100 records |

The encoded-state ceiling additionally bounds deterministic framing overhead. No Python list in durable or exchange state is unbounded.
