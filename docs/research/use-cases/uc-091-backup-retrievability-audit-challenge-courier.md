# UC-091 — Backup Retrievability Audit Challenge Courier

## Idea

Do not wait for disaster day to discover that an offline backup is incomplete or corrupted. A backup owner periodically sends a **small unpredictable audit challenge** to a remote/cache node; that node proves it still possesses selected authenticated parts of the exact backup version, and the proof/result comes back later through PollicinoNet.

The first implementation can use Merkle-authenticated sampled blocks rather than claiming a full formal Proof-of-Retrievability scheme.

## Problem solved

UC-012 can restore from opportunistic backups and UC-036 can scrub/repair known content. A separate operational question remains:

> “Does this remote backup node still appear able to retrieve the exact backup I think it stores, even though I cannot contact it continuously?”

Downloading the whole backup just to check it wastes bandwidth and may be impossible across sparse links. Small challenge/response audits can give earlier warning that a replica is missing, stale or corrupted.

## Actors / nodes

- backup owner/auditor;
- storage/cache node;
- student relay/store-and-forward nodes;
- optional second verifier;
- optional repair source if an audit fails.

## Why PollicinoNet fits

Audit traffic can be compact and tolerate long round trips.

- **DISCOVERY:** advertise storage/audit capability and backup manifest IDs;
- **EXACT:** backup/version hash, manifest root, challenge nonce, sampled block indexes, response/proof hash and audit result;
- **SEMANTIC:** labels such as `course-backup` or `project-archive` help humans but never identify the exact version being audited.

The challenge may leave the owner on one relay path and the proof return on another hours later.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** backup ID/root hash, challenge nonce, small sample indexes, compact audit result and proof hash;
- **BLE:** nearby challenge/proof exchange;
- **Wi-Fi/LAN:** Merkle proofs, sampled chunks, manifests and any repair data;
- **Internet:** optional fast path between reachable peers;
- **physical transport:** student-carried node transports challenge and later proof/repair material.

## What we can test now in software

Create a backup object split into authenticated chunks with a Merkle root stored in an exact manifest.

Define `AuditChallenge`:

```text
audit_id
backup_manifest_hash
challenge_nonce
sample_indexes
created_epoch
expiry
auditor_id
```

and `AuditResponse`:

```text
audit_id
storage_node_id
manifest_hash
proof_refs
response_hash
created_epoch
status = PASS | FAIL | INDETERMINATE
```

Then test:

- intact backup passes sampled audit;
- one sampled block deleted;
- corruption outside the sampled set remains undetected in that round;
- challenge repeated/replayed;
- storage node answers for the wrong backup version;
- stale proof arrives after a newer challenge;
- manifest root mismatch;
- response body available only over a later rich-bearer contact;
- node claims `PASS` without a valid proof;
- audit failure triggers UC-036 repair workflow;
- several rounds gradually increase sampled coverage.

Useful metrics: audit round-trip time, proof bytes, fraction of backup sampled over time, detected corruption rate under injected faults, false-pass rate in the test harness, and repair latency after a failed audit.

A crucial limitation must remain visible:

> passing a sampled audit does not prove every byte is intact unless the selected audit construction provides that guarantee; report exactly what was checked.

## What requires real hardware

A first experiment needs:

- 4–6 LoRa nodes;
- two laptop/Raspberry Pi storage nodes;
- one backup/archive of harmless test data;
- relays between auditor and storage node;
- one intentionally corrupted/deleted chunk.

Use LoRa for challenge/result metadata and Wi-Fi for proof/chunk transfer. Measure actual round-trip time and bytes before making efficiency claims.

## Messina teaching scenario

Keep two test backups on separate student/school islands, for example school and Rometta/Venetico. The auditor at school emits challenges that travel through student relays. One remote replica is deliberately damaged. The class observes when the fault is first detected and how many audit rounds/contacts were required.

This can later compose with UC-040 replica placement and UC-036 scrub/repair.

## Privacy / security

- challenge nonces must be unpredictable enough to prevent simple canned replay responses;
- bind every response to one exact backup manifest/version;
- do not expose filenames or private content labels in LoRa metadata;
- encrypt proofs/chunks if the backup is confidential;
- rate-limit audits so they cannot become a denial-of-service tool;
- avoid revealing enough sampled data to reconstruct sensitive content;
- authenticate auditor and storage-node identities where policy requires it;
- distinguish `FAIL` from `INDETERMINATE` when evidence is missing or stale;
- do not market the basic prototype as a formally proven PoR scheme.

## Difficulty

**Medium-high.** A Merkle-sampled prototype is accessible; designing or adopting a formal retrievability proof with strong adversarial guarantees is substantially harder.

## Why this is distinct from nearby use cases

- **UC-012:** performs backup/restore.
- **UC-036:** proactively scrubs and repairs known content corruption.
- **UC-061:** caches deterministic computation results.
- **UC-091:** performs a **remote delayed audit challenge** to gain evidence that an exact backup replica still retains retrievable authenticated content without downloading the whole object.

## Research / implementation signal

Remote storage auditing and proofs of retrievability remain active research topics. A 2026 open-access paper in *Peer-to-Peer Networking and Applications* studies outsourced-data auditing with probabilistic guarantees and hash-based constructions. PollicinoNet should start with a transparent sampled-audit prototype and only claim the guarantees it actually implements.

References:

- https://doi.org/10.1007/s12083-026-02243-5
- https://link.springer.com/article/10.1007/s12083-026-02243-5
