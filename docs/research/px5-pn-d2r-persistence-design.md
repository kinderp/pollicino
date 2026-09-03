# PX5 PN-D2R persistence design

## Strategy comparison

| Strategy | Recovery | Complexity | Decision |
|---|---|---|---|
| A — single atomic snapshot | exact clean restart, but no fallback after current corruption | smallest | insufficient for preregistered fallback |
| B — dual-generation atomic snapshot | current plus immediately previous valid state | two fixed files, no log | selected |
| C — journal/database/WAL | richer history/concurrency | parser/state/compaction dependency | unjustified |

Each node directory contains `catalog.0.snapshot`, `catalog.1.snapshot` and
`catalog.lock`. A successful semantic mutation increments a node-local integer
generation and atomically replaces the parity slot. Thus at most two snapshots
exist. Generation is only local durability order; it is not catalog identity,
time, trust, publisher state or consensus.

The binary envelope is the local format
`pollicino.local-persistent-reference-catalog.v1`:

```text
8-byte magic | u8 version | u64 generation | u64 payload length
| SHA-256(prefix + payload) | PX3 canonical catalog payload
```

All integers are big-endian. The maximum envelope payload derives from active
native catalog limits. The SHA-256 value detects local corruption; it is not a
signature or trust statement. This is `LOCAL_PERSISTENCE_FORMAT`, never a
network wire format. Pickle is forbidden and unused.

Full-state rewrite amplification is a known local limit. Snapshots at 10, 100,
1000 and 10000 items restart exactly, but no throughput/latency benchmark was
run. WAL, SQLite, MVCC, compaction, replication logs and consensus remain
deferred.
