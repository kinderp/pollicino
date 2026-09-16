# Durable exact-session persistence

PollicinoNet exact transfer is resumable at verified chunk boundaries. This note defines the first durable persistence layer that lets the same session survive process restart without changing PNF1, PCM1 or PNA1.

## Scope

The durable layer persists two different things:

1. **verified chunk bytes** in a content-addressed directory store;
2. **session coordination/accounting state** in an atomic checksummed JSON checkpoint.

The source object itself, transport credentials, authorization decisions and application policy are deliberately outside this checkpoint.

## DirectoryPollicinoStore

A chunk is addressed only by its SHA-256 digest:

```text
<root>/chunks/<first 2 hex>/<remaining 62 hex>
```

The filename is an address, not proof. Before a chunk is advertised by PNA1 or returned to the reconstruction layer, the file contents are read and hashed again.

Rules:

- a missing file is unavailable;
- a regular file whose SHA-256 does not match its address is unavailable for `has()` and fails `get()`;
- a later verified `put()` may atomically repair a corrupt ordinary file;
- a symlink at a chunk address is never followed or overwritten;
- writes use a temporary file in the target directory, file `fsync`, then `os.replace`;
- directory `fsync` is attempted where the platform supports it.

This is a minimal research store, not yet a multi-user database or a garbage-collected cache.

## Session checkpoint

Checkpoint schema:

```text
pollicino-exact-session-checkpoint-v1
```

The envelope contains:

```text
schema
state
state_sha256
```

`state` is the existing `ExactSyncSessionState.to_dict()` representation. `state_sha256` is computed over canonical JSON for that state.

The loader verifies:

- checkpoint schema;
- exact-session state schema;
- boolean and integer field types;
- 64-hex-character manifest fingerprint;
- optional wire-accounting type;
- SHA-256 checksum of canonical state JSON;
- all invariants already enforced by `ExactSyncSessionState`.

The checksum is corruption detection, not authentication. A future adversarial persistence model would require an authenticated/MACed or signed checkpoint under an appropriate key-management policy.

## Atomic update contract

A checkpoint update is:

```text
new state
  -> write same-directory temporary file
  -> flush + fsync temporary file
  -> os.replace(temp, checkpoint)
  -> best-effort directory fsync
```

The intended crash property is that the canonical checkpoint path contains either the previously committed state or the newly committed state, never a partially written JSON document. A failed replace is tested to leave the old checkpoint readable.

Temporary files are not authoritative and may be removed after a failed write.

## Restart flow

```text
process A
  |
  |-- receive chunk 0 -> verify SHA-256 -> durable store
  |-- receive chunk 1 -> verify SHA-256 -> durable store
  |-- atomically save session checkpoint
  X  process stops

process B
  |
  |-- reopen sender/receiver DirectoryPollicinoStore
  |-- load + verify session checkpoint
  |-- recompute PNA1 availability from durable verified chunks
  |-- receiver advertises chunk 0 and 1 already present
  |-- transmit only remaining chunks
  |-- reconstruct complete object
  `-- verify final object SHA-256
```

The session state does not blindly claim that a chunk exists. Availability is recomputed from the reopened store. This means a chunk that disappeared or became corrupt while the process was down is not advertised and will be transferred again.

## Scientific accounting boundary

Persistence changes **when** bytes need to be retransmitted, not the meaning of TRC.

A successful restart should reduce later scarce-link traffic because verified chunks survive. The normal session accounting still records manifest/control/chunk/ACK/retry bytes. Physical RF replay continues to preserve lower-bound return-path accounting for untethered failures.

Do not count disk bytes as radio TRC. Disk footprint and I/O durability are separate system metrics.

## Current validation

The test suite covers:

- reopen of a durable chunk store;
- detection and repair of a corrupt chunk file;
- checkpoint round-trip;
- checkpoint checksum tamper detection;
- simulated failure before atomic `os.replace`, preserving the previous checkpoint;
- a fresh-process-style restart where sender store, receiver store and session state are recreated from disk;
- verification that already durable chunks are not retransmitted;
- final byte-identical reconstruction and idempotent completed-session resume.

## Next persistence questions

The current implementation intentionally leaves these for later experiments:

- garbage collection and retention policy;
- reference tracking across multiple manifests;
- disk quota and eviction;
- concurrent multi-process writers/readers;
- store-and-forward ownership/lifecycle across peers;
- authenticated checkpoints for hostile local storage;
- encrypted-at-rest private chunk stores where application policy requires them.
