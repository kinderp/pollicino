# UC-130 — Cross-Artifact Content-Defined Chunk Deduplication Ferry

## Idea

Split large artifacts into content-defined chunks and transfer only chunks the receiving side does not already possess, even when those chunks came from different files or older artifact versions.

This is broader than a version-to-version delta.

## Problem solved

Student nodes may repeatedly carry course packs, VM/container images, datasets, AI models, backups, map bundles and Raiatea corpora. Many objects share byte regions. Re-sending every whole file wastes rich-bearer contact time and relay storage.

UC-104 helps when a receiver has one exact base artifact. UC-130 asks which exact chunks are already present anywhere in the local cache regardless of which original artifact supplied them.

## Actors / nodes

Artifact publisher, requester, student relay/store-and-forward node, deduplicating chunk cache, optional inventory provider and integrity verifier.

## Why PollicinoNet fits

Chunk identities and object manifests are small enough to advertise compactly. Chunk bytes move over rich bearers.

An object manifest can contain object hash, chunking-profile ID, ordered chunk hashes, expected length and optional Merkle root. A node first learns which chunks are missing, then transfers only those.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: object ID/hash, chunking profile, manifest root, compact missing-set or inventory summary.
- BLE: manifests and a limited number of chunks.
- Wi-Fi/LAN: bulk missing chunks.
- Internet: optional origin/cache.
- Physical transport: SSD/laptop/phone carrying a large chunk store.

## What we can test now in software

Create a reproducible corpus with overlapping course packs, edited archives, model/dataset bundles and backup snapshots.

Compare whole-object transfer, fixed-size chunks, content-defined chunks and UC-104-style exact-base delta where applicable.

Measure source bytes, unique chunk bytes, manifest/control bytes, missing chunk count, bytes transferred, chunking CPU time and final reconstruction correctness.

Inject a corrupted cached chunk, incompatible chunking profile, missing chunk, inventory false positive, interrupted transfer and GC race.

The receiver must always verify the final exact object hash.

## What requires real hardware

Use 4–6 boards plus two or three laptops/Pi-class hosts with intentionally overlapping stores.

Preload different chunk subsets, advertise a target object, exchange compact control through LoRa, open a short Wi-Fi/BLE contact, transfer missing chunks, interrupt the contact, resume later and verify the final object.

Any bandwidth/time saving must be reported only for the measured corpus and hardware.

## Messina teaching scenario

A school publishes a large updated course or AI pack. Students in Villafranca, Rometta/Venetico and Spadafora already carry different older packs. Useful chunks may exist on several devices even though no one has the exact expected base version.

PollicinoNet advertises the target manifest while rich-bearer contacts move only verified missing chunks.

## Privacy / security

Chunk hashes can reveal possession of known content. Do not broadcast full private inventories over LoRa. Preserve usage-policy/license constraints from UC-076, authenticate executable/model publishers, verify every chunk and final object, cap inventory probing, and separate deduplication identity from authorization.

## Difficulty

Medium-high. Chunking itself is established; privacy-aware inventory exchange, cache races and intermittent reconstruction are the challenging parts.

## Why this is distinct

UC-012 provides backup/restore semantics; UC-018 uses erasure-coded shards; UC-104 transfers a delta from one exact base; UC-112 resumes one transfer. UC-130 reuses identical chunks across many cached artifacts and versions.

## Research / implementation signal

Content-defined chunking is widely used for deduplication because chunk boundaries can re-align after local insertions/deletions. Current Borg documentation supports content-defined chunkers including FastCDC-style chunking, making the idea easy to prototype without inventing a new low-level algorithm.

References:

- https://borgbackup.readthedocs.io/en/master/internals/chunker.html
- https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia
