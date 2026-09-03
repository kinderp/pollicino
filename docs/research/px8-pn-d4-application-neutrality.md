# PX8-PN-D4 application-neutrality audit

`src/pollicino/net/contact.py` refers only to native D2/D3 records, stores,
reconciliation, persistence errors, budgets, interruption, and diagnostics.
Automated source inspection rejects FARO, RegistryQuery, EvidenceGrade,
publisher, Recommendation, DNA, torrent, magnet, and CONTENT vocabulary.

The core never calls `evaluate_query`, a registry search callback, selected-key
policy, exact package retrieval, verification, trust, recommendation, or
import. The FARO and synthetic-content tests both wrap the same unmodified
contact entry point.

```text
APPLICATION_SPECIFIC_CONTACT_CORE_BRANCHES: 0
AUTO_QUERY_EVALUATION: NONE
AUTO_REFERENCE_PULL: NONE
AUTO_FETCH: NONE
AUTO_IMPORT: NONE
```
