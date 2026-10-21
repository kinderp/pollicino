# UC-SHARD-001 — Diversity-coded multipath object carriage

Status: RESEARCH / SOFTWARE PROTOTYPE

## Problem

Replication is simple but can waste scarce storage and contact capacity. At the other extreme, a single-copy object can fail if its one carrier misses the destination. A distinct middle ground is to split an authorized exact object into **redundant coded shards** so that the destination can reconstruct it after receiving any sufficient subset.

Example research shape:

```text
object -> encrypt -> encode k-of-n shards
                 |-> carrier A
                 |-> carrier B
                 |-> carrier C
                 |-> carrier D

later: any k valid shards -> decode -> decrypt -> verify authoritative SHA-256
```

The goal is not to invent a new codec for every bundle. The question is whether coded diversity can improve deadline delivery or reduce total replicated bytes for a concrete student-mobility workload with finite storage and uncertain carriers.

Initial objects should be small synthetic/public fixtures. Large media still belongs on rich links/reference workflows unless measured evidence justifies otherwise.

## Actors / nodes

- source/school gateway;
- several student-carried relay nodes;
- destination/home/school sink;
- encoder/decoder application layer;
- Pollicino exact store-and-forward for each shard;
- optional reference to the authoritative full object.

## Messina educational scenario

At the morning school mixing phase, an exact 2–8 KiB synthetic dataset/config fixture is encoded into a small number of shards. Different pseudonymous carriers associated with Rometta-like, Spadafora-like, Saponara-like and Villafranca-like logical cohorts receive different shards.

The afternoon synthetic topology deliberately removes one or two carriers. The sink succeeds only if enough independent shard paths arrive before the usefulness deadline.

This is a diversity experiment, not a claim that LoRa can efficiently carry arbitrary files between those towns.

## Why PollicinoNet fits

PollicinoNet already provides:

- exact content verification;
- chunk/content-addressed stores;
- intermittent multi-hop delivery;
- finite contact schedules;
- custody and duplicate suppression;
- routing baselines and deadline experiments;
- a dense school phase where shards can be placed on multiple carriers.

Coded shards can therefore be represented as ordinary exact objects above the core. The final reconstruction must still verify the authoritative object hash.

## Possible bearers

- school Wi-Fi/LAN for seeding larger shards in a controlled experiment;
- LoRa for very small shard fixtures when within the frozen/validated protocol budget;
- BLE for local seeding if enabled later;
- opportunistic LoRa for shard forwarding;
- physical carry by independent student nodes;
- rich link for final payload/reference resolution if the coded object is only metadata.

No PHY change is required.

## What can be tested now in software

1. direct single-copy baseline;
2. full replication to `r` carriers;
3. simple Reed-Solomon-style `k-of-n` research fixture using an existing trusted library only if needed;
4. carrier absence/dropout;
5. correlated carrier routes versus independent routes;
6. unequal storage quotas;
7. deadlines shorter than TTL;
8. shard placement at school followed by opportunistic delivery;
9. duplicate shard suppression;
10. corrupted shard rejection;
11. insufficient-shard failure that remains explicit, never reconstructed approximately;
12. total source bytes and total wire bytes versus ordinary replication;
13. compare coding with `UC-PREFETCH-001` placement decisions;
14. encrypted-before-coding versus plaintext test fixture accounting.

Do not implement a custom erasure-code primitive unless a standard library/prototype is unavailable. The first gate is workload value, not coding novelty.

## Minimal measurable hypotheses

- H1: there exists a carrier-dropout regime where bounded coded diversity improves reconstruction-before-deadline over one-copy delivery.
- H2: there exists a regime where coded diversity achieves similar reliability to full replication with fewer total stored/source bytes.
- H3: mobility/path correlation can erase the expected coding benefit, so placement diversity matters at least as much as `k` and `n`.

## Metrics

- exact reconstruction ratio before deadline;
- number of independent carriers used;
- total source/shard bytes created;
- total scarce-link wire bytes;
- storage bytes per carrier;
- redundant/duplicate shard deliveries;
- decode success/failure;
- corrupted shard rejections;
- delivery gain versus full replication;
- sensitivity to correlated carrier failures;
- CPU/memory cost of encoding/decoding in host prototype.

## What requires real hardware

Real boards are required before claiming:

- practical shard size/count on the embedded target;
- encode/decode memory/CPU feasibility if done on-device;
- real LoRa cost of shard control/transfer;
- energy impact versus replication;
- whether independent student mobility actually provides useful path diversity;
- storage pressure and restart behavior on the physical nodes.

HW-006 remains the first RF evidence gate. A separate embedded coding-feasibility gate is required before making the algorithm mandatory.

## Privacy / security

Erasure coding is **not encryption**.

Requirements:

- private content must be encrypted before shard generation;
- do not assume that possession of fewer than `k` plaintext-coded shards gives acceptable confidentiality;
- integrity must be checked per shard and again on the reconstructed authoritative object;
- provenance/access policy remains attached to the parent object;
- prevent shard IDs from leaking sensitive filenames/topics where unnecessary;
- rate/storage quotas to avoid amplification abuse;
- start with public/synthetic fixtures only.

## Implementation difficulty

**Medium-high.** The host experiment is straightforward with an existing coding library; deciding whether coding is worth its control/compute/storage complexity is the real research challenge.

## Relationship to existing use cases

- Not `UC-BACKUP-001`: BACKUP asks how to keep safe copies; SHARD specifically tests coded redundancy and path diversity under deadline/storage constraints.
- Not `UC-CONTENT-001`: CONTENT transports/retrieves known objects/references; SHARD changes how redundancy is distributed across multiple carriers.
- Not `UC-PREFETCH-001`: PREFETCH chooses placement before separation; SHARD chooses the redundancy representation. The two can be combined later.
- Not network/PHY coding: this is an application/object-layer research experiment and does not change the frozen LoRa PHY.

## Success / kill criterion

**Continue** only if preregistered synthetic carrier-dropout/storage scenarios show a meaningful regime where coded diversity beats both one-copy and simple replication baselines after accounting for all shard/control bytes.

**Defer/reject** if simple bounded replication provides equivalent delivery with lower complexity on the actual Pollicino workloads.

## Gate decision

**RESEARCH / PROTOTYPE.** Interesting but not a near-term production feature. The use-case gate explicitly requires it to beat simple replication before any deeper integration.

## Related precedent

Coding/erasure techniques have long been studied in DTNs as a way to trade replication overhead against delivery probability under mobile contacts. This motivates the baseline comparison but is not evidence that coding will help PollicinoNet.

- https://arxiv.org/abs/0907.5430
