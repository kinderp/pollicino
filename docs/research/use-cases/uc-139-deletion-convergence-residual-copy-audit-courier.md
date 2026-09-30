# UC-139 — Deletion-Convergence and Residual-Copy Audit Courier

## Idea

After a deletion tombstone has been issued, determine which cooperating replicas are known to have applied it, which are still unknown, and where a stale copy might still reappear.

UC-139 does not claim remote secure erasure. It adds bounded audit evidence around UC-077 so deletion convergence can be measured honestly across long offline periods.

## Problem solved

UC-077 prevents stale resurrection after a replica learns the tombstone, but an operator may still need to distinguish caches that accepted the tombstone, caches no longer serving the object, caches reporting local purge, nodes that remain offline/unknown, and backups or partial caches that still advertise the deleted version.

## Actors / nodes

Authorized deletion issuer, content caches, backup nodes, student relay/store-and-forward nodes, optional Raiatea lineage store, audit collector and optional storage owner responsible for actual media sanitization.

## Why PollicinoNet fits

Audit receipts are compact and delay tolerant. Useful states include TOMBSTONE_NOT_SEEN, TOMBSTONE_ACCEPTED, NOT_SERVED, LOCAL_PURGE_REPORTED, REPLICA_REAPPEARED, NODE_UNKNOWN and SANITIZATION_EXTERNAL.

LOCAL_PURGE_REPORTED is only a protocol statement by a cooperating node; it is not proof that data is unrecoverable from physical media. The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: tombstone ID/hash, replica pseudonym, compact acknowledgement state and audit epoch.
- BLE: nearby replica reconciliation.
- Wi-Fi/LAN: full inventory, backup manifest and audit evidence.
- Internet: optional authoritative deletion/retention policy.
- Physical transport: an offline cache or storage device can later return with its audit state.

## What we can test now in software

Test an offline replica during deletion, a returning stale replica, a node that accepts the tombstone but still advertises the object, lost local tombstone state after reinstall, backup restore trying to reintroduce content, residual UC-130 chunks, derived Raiatea references, forged/duplicate audit receipts, premature tombstone garbage collection and legitimate recreation as a new exact version.

Measure acknowledgement coverage, time to convergence among reachable cooperating nodes, zombie-resurrection attempts, UNKNOWN replicas and the difference between logical deletion, local purge report and separately validated media sanitization.

## What requires real hardware

Use 5–8 boards paired with small caches containing disposable public test files. Isolate one node, issue a tombstone, let the other nodes acknowledge it, then reintroduce the isolated node. Verify that the stale object is not accepted as live and that the audit state moves from UNKNOWN to an observed state.

## Messina teaching scenario

Replicate one harmless document across test caches representing Messina, Villafranca, Rometta/Venetico and Spadafora. Disconnect the Spadafora replica and issue a deletion. The dashboard should show observed acknowledgements plus one UNKNOWN, not "100% erased". When the cache later returns, it learns the tombstone and reports bounded audit state.

## Privacy / security

Use opaque object IDs, minimize replica lists, use experiment-scoped pseudonyms, authenticate tombstones/acknowledgements, avoid per-student possession histories, distinguish logical deletion from physical sanitization and retain audit evidence only as long as needed.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-077 propagates deletion and prevents resurrection; UC-139 measures where deletion state is known, unknown or contradicted. UC-091 audits wanted backups; UC-139 audits the opposite lifecycle goal. UC-109 protects desired durability during GC.

## Research / standards signal

NIST SP 800-88 Rev. 2 distinguishes media sanitization from ordinary deletion and emphasizes validation. A PollicinoNet network receipt must therefore never be mislabeled as verified physical sanitization.

References:

- https://csrc.nist.gov/pubs/sp/800/88/r2/final
- https://cassandra.apache.org/doc/stable/cassandra/managing/operating/compaction/tombstones.html
