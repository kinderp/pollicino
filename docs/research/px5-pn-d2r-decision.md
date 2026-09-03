# PX5 PN-D2R decision

```text
PERSISTENCE_STRATEGY:
DUAL_GENERATION_ATOMIC_SNAPSHOT

CLASSIFICATION:
POLLICINO_PERSISTENT_BOUNDED_REFERENCE_CATALOG_READY_WITH_LIMITS

CONFIDENCE:
HIGH

NEXT_GATE:
PX6-PN-D3
```

The immediately previous valid generation is mandatory recovery evidence and
is always reported explicitly. No journal, SQLite, WAL, database dependency,
network protocol or application semantics is justified.

Known limits are one POSIX writer process per node directory, no concurrent
reader contract, full-state write amplification and filesystem guarantees
bounded to tested same-directory replace/fsync behavior. These limits do not
permit silent corruption or memory/disk ambiguity.
