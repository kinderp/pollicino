# PX6-PN-D3 model accounting

Label: `MODEL_PROTOCOL_ACCOUNTING_ONLY`. Benchmark: `NOT_RUN_BY_DESIGN`.

A deterministic sparse-interest model uses 1,000 catalog entries, 32-byte keys, 512-byte references, a 16-byte query ID, 96 opaque query bytes, a 16-byte result ID and 10 selected keys.

| Component | Modeled bytes |
|---|---:|
| full catalog transfer | 550,049 |
| bounded query record | 118 |
| bounded result record | 378 |
| ten selected D2 references | 5,500 |
| query + result + selected pull | 5,996 |

Modeled reduction versus full transfer: 98.91%. This supports the sparse-discovery architecture but is not a network, storage, latency, energy or throughput benchmark.

Advanced reconciliation remains `DEFERRED_NOT_JUSTIFIED`: exact sorted identifier comparison and bounded selected pull are sufficient for the correctness Gate.
