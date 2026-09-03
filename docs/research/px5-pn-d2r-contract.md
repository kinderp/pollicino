# PX5 PN-D2R persistence contract

## Preregistered requirements

Before final execution, Strategy A was required to satisfy clean exact restart,
atomic commits, unchanged disk and memory after rejected native mutations or
pre-replace failures, fail-closed malformed/version/bounds handling, native
canonical payload preservation, and zero application/network dependencies.

Automatic recovery was preregistered as required: when the newest snapshot is
corrupt and the immediately previous known-good generation exists, open must
load it with `RECOVERED_PREVIOUS_GENERATION`. This requirement makes one
snapshot insufficient and justifies exactly two bounded generations.

## Public contract

`PersistentBoundedReferenceCatalog` subclasses the native catalog so existing
native/FARO type checks and APIs continue to apply. It stages each mutation in
a catalog reconstructed by `BoundedReferenceCatalog.from_canonical_state`,
uses native mutation validation, commits the candidate snapshot, and only then
publishes the same mutation in memory. Duplicate no-ops do not write or advance
generation. Conflict/quota failures touch neither disk nor live state.

Opening an absent directory yields an empty catalog and
`NO_DURABLE_STATE`. Opening valid state yields `LOADED_CURRENT_GENERATION` or
explicit recovery. Corrupt-only or ambiguous state fails closed.

The validated concurrency scope is one authoritative writer process per node
directory. A nonblocking POSIX advisory lock rejects a second writer; process
exit releases the lock even though the harmless lock file remains. Concurrent
readers and multi-writer operation are not supported.
