# PX6-PN-D3 decision

```text
GATE:
PX6-PN-D3

CLASSIFICATION:
POLLICINO_ASYNC_QUERY_RESULT_LOCAL_PERSISTENT_READY_WITH_LIMITS

CONFIDENCE:
HIGH

QUERY_MODEL:
OPAQUE_QUERY_PLUS_CATALOG_KEY_RESULTS

FARO_CONFORMANCE:
FARO_D3_CONFORMANCE_READY_TEST_ADAPTER_ONLY

NEXT_GATE:
RG3-PX7 — FARO RegistryQuery over Native Pollicino Persistent Async Query/Result
```

The WITH_LIMITS result records inherited PX5 POSIX/single-writer/full-snapshot limits, no TTL/GC/authentication, local method-call exchange, and the lack of a production FARO D3 adapter. It does not conceal a correctness, bounds, persistence or genericity failure.

Product frontier: bounded persistent application-neutral asynchronous intent and candidate-key discovery are locally validated. DTN, routing, custody, PNB1/PNC1, bearers, public search, Internet P2P, automatic fetch/import/trust/recommendation and query authentication remain blocked.
