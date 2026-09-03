# PX6-PN-D3 persistence

PX6 extracted the already-proven PX5 file mechanics into `pollicino.net.local_persistence.DualGenerationSnapshotStore`. Both `PersistentBoundedReferenceCatalog` and `PersistentQueryResultStore` use that helper with distinct magic values, codecs, paths, locks and snapshots. PX5's on-disk format, file names and public behavior remain unchanged.

Inherited guarantees:

- two bounded generations;
- same-directory temporary file, mode `0600`;
- complete write, file `fsync`, atomic `os.replace`, directory `fsync`;
- explicit previous-generation recovery;
- ambiguity and both-generation corruption fail closed;
- failures before replace preserve old memory/disk authority;
- failures after replace fail-stop the instance and require reopen;
- POSIX nonblocking single-writer lock.

Query/result persistence uses `pollicino.local-persistent-query-result.v1`, a `LOCAL_QUERY_STATE_FORMAT` envelope containing only a local generation, length, SHA-256 integrity digest and canonical query/result payload. SHA-256 detects corruption; it authenticates nobody and implies no trust.

The application reattaches its handler after restart. No callback, function path or application object is serialized.

Limitations inherited from PX5 are POSIX-tested behavior, one authoritative writer, no concurrent-reader contract, full-snapshot write amplification and no physical power-loss claim. SQLite, WAL and journals were unnecessary.
