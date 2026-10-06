# UC-172 — Event-Log Snapshot and Compaction Courier

Study how an offline-first application can replace a very long event history with a verified state snapshot plus only the later event tail.

Actors are event producers, replicas, a snapshot worker, student relays and a verifier. LoRa carries snapshot ID, version and high-water metadata; BLE/Wi-Fi carries the snapshot and tail; physical transport can carry large archives.

Software tests compare full-log replay with snapshot-plus-tail under duplicate, delayed and concurrent events. Hardware tests use 4–6 boards and 2–3 storage hosts that generate events while separated and reconcile later.

This can support long-running checkpoint mailboxes, maintenance tickets and classroom ledgers across school/public islands in Messina.

Privacy/security: scope snapshots carefully, authenticate them and preserve an audit reference to the compacted history.

Difficulty: **Medium–High**. Distinct from causal-timeline reconstruction and computation checkpointing because it bounds a growing application event history.
