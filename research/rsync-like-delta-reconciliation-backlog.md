# Rsync-like delta reconciliation — research backlog

Status: **BACKLOG / RESEARCH ONLY**

This item does **not** change the frozen LoRa PHY and does **not** assign a production wire format or capability bit.

## Motivation

PollicinoNet already studies receiver-side availability descriptions and sparse set reconciliation (including simple codecs and minisketch) for cases where peers share the same manifest/chunk namespace. A different regime appears when two peers hold **different versions of a large object** that are mostly identical but whose byte/chunk boundaries may have shifted after insertions or deletions.

Rsync-like delta transfer is relevant because it tries to discover reusable byte ranges already present at the receiver and send only literals/references needed to reconstruct the target version.

## Use-case gate

Candidate workload: `UC-DELTA-001 — Opportunistic version-delta synchronization`.

Examples:
- a dataset or document bundle changes by a few percent between generations;
- a generated artifact is rebuilt with a small insertion near the beginning;
- two home/school caches contain adjacent versions rather than partial copies of the exact same manifest.

This is intentionally distinct from current minisketch work:
- **minisketch / set reconciliation**: identify sparse differences inside a shared chunk-ID universe;
- **rsync-like delta**: discover reusable content across different versions even when offsets or fixed chunk boundaries moved.

## Simplest baselines first

Benchmark at least:
1. full-object transfer;
2. fixed-size chunk hashing;
3. rsync-like rolling-checksum + strong-hash delta;
4. content-defined chunking + strong hashes.

Where applicable, also compare with the existing Pollicino availability/minisketch path when both versions can be represented in a shared chunk namespace.

## Accounting

Count the complete cost, not only literal payload bytes:
- signatures/checksums sent to the source;
- requests/control metadata;
- literal bytes and block/chunk references;
- framing overhead;
- ACK/retry/control accounting used by the existing harness;
- CPU/RAM/flash cost as a separate host/embedded feasibility dimension.

## Hypothesis

An rsync-like or content-defined delta may beat full transfer and fixed-size chunking when the target object is a near-neighbor version with insertions/deletions that shift fixed chunk boundaries. It may lose badly for tiny objects, high-entropy unrelated versions, or when checksum metadata dominates the scarce bearer.

## Kill / adoption criteria

Do not adopt a new Pollicino wire primitive merely because rsync works well on normal networks.

Continue only if a concrete Pollicino workload shows a material end-to-end win after full control/metadata accounting. Prefer the simplest winning mechanism. If fixed chunks, existing availability codecs, minisketch, or rich-bearer transfer already solve the workload adequately, keep rsync-like delta as research/deferred.

## Bearer boundary

Likely role by bearer:
- **LoRa**: compact signatures/delta/control only when the measured budget justifies them;
- **BLE/Wi-Fi/Internet/LAN**: richer reconciliation or bulk byte transfer;
- **physical carry**: move the cache/version itself between contact opportunities.

No geographic/range/capacity claim follows from this backlog item. Physical validation remains behind the existing hardware evidence gate.
