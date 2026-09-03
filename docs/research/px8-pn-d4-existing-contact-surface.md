# PX8-PN-D4 existing contact surface

Audit base: exact PX6 closure `3d574773035677d30eb566dc1fa7c0f0ecb9c051`.

PX6 contains no contact-session, encounter, custody, routing, data-mule, retry,
or per-peer progress implementation. `ROADMAP.md` and PollicinoNet research
notes mention offline/store-and-forward only as future use-case work. Existing
link and delivery modules model exact payload fragmentation/delivery; they are
not used by D4 because fragmentation and a bearer contract remain deferred.

The canonical reusable surfaces are:

| Concern | Existing authority | D4 use |
|---|---|---|
| D2 identifier pages and known/unknown comparison | `pollicino.net.catalog.BoundedReferenceCatalog` | inspect selected reference work |
| D2 selected pull and conflict/quota mutation | `reconcile_and_pull` / `persist_reconcile_and_pull` | apply one caller-selected reference atomically |
| D2 restart | `PersistentBoundedReferenceCatalog` | durable store/carry/forward state |
| D3 query identifier reconciliation and pull | `reconcile_queries` | apply one missing query atomically |
| D3 result identifier reconciliation and pull | `reconcile_results` | apply one missing result atomically |
| D3 conflict, duplicate, quota and orphan behavior | `QueryResultStore` | authoritative record semantics |
| D3 restart | `PersistentQueryResultStore` | durable store/carry/forward state |
| durable commit | `DualGenerationSnapshotStore` | POSIX-tested atomic snapshot commit |

Query receipt does not call `evaluate_query`. Result receipt does not pull D2
references. Both facts are preserved by making D4 an orchestrator over the
existing reconciliation functions.

The D2 and D3 local canonical formats remain unchanged. D4 adds no hop, path,
contact, peer, acknowledgement, or session field to any record.

