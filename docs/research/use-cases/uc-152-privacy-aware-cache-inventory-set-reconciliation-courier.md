# UC-152 — Privacy-Aware Cache Inventory and Set-Reconciliation Courier

## Problem solved

Two PollicinoNet caches may each hold tens of thousands of object IDs but differ in only a few dozen. Sending the entire inventory during a short contact wastes control bandwidth.

UC-152 lets peers discover **which object IDs differ** using compact inventory summaries before they request the actual missing content.

## Actors / nodes

Student cache, school content cache, backup node, Raiatea store, AI model/dataset cache, relay and optional reconciliation coordinator.

## Why PollicinoNet fits

After long partitions, store-and-forward caches are often similar but not identical. A staged reconciliation exchange can carry:

1. namespace/epoch and object count;
2. a compact top-level digest or sketch;
3. a difference-size estimate;
4. exact IDs only for the symmetric difference;
5. later content requests over the best bearer.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** tiny namespace, epoch, counts and top-level digests.
- **BLE:** moderate sketches and short missing-ID lists.
- **Wi-Fi/LAN:** larger sketches, exact inventory fragments and requested content.
- **Internet:** optional coordination.
- **Physical transport:** complete cache snapshot when the difference is very large.

## What we can test now in software

Generate synthetic content-addressed inventories from 100 to 1,000,000 IDs with controlled overlap.

Compare:

- full inventory exchange;
- hierarchical/Merkle-style partitioning;
- Bloom-filter approximation;
- ordinary IBLT;
- rateless/self-sizing IBLT variants;
- fallback to “send full inventory” when the difference is too large.

Test unknown difference size, false positives, decode failure, stale epoch and namespace mismatch.

Measure bytes, CPU, memory, number of rounds and exact reconciliation success.

## What requires real hardware

Use 4–6 LoRa boards plus 2–3 cache hosts containing 10k–100k synthetic IDs. Start with only the smallest reconciliation metadata on LoRa and use BLE/Wi-Fi for larger sketches.

Interrupt contacts deliberately and compare against a naive full inventory dump. Any latency or energy benefit must be measured on the real devices.

## Messina teaching scenario

Caches in Messina, Villafranca and Rometta/Venetico-Spadafora hold overlapping course packs, Raiatea artifacts and public AI model chunks.

When two student nodes meet, they first learn how different their authorised cache namespaces are. If the difference is small, exact missing IDs are recovered and UC-124/UC-130 can schedule the bulk transfer.

## Privacy / security

Inventory membership can reveal what a node stores. Keep reconciliation scoped to an authorised namespace, avoid broadcasting full cache summaries, use synthetic/public inventories for the first experiments and treat probabilistic-filter matches as hints rather than proof of possession.

The protocol must have an explicit fallback when a sketch cannot be decoded.

## Difficulty

**High.**

## Why this is distinct

UC-100 exchanges demand sketches, UC-102 performs groupcast anti-entropy, UC-109 reasons about safe replica retirement and UC-130 deduplicates chunks during bulk transfer.

UC-152 solves the narrower problem of **efficiently discovering the symmetric difference between two large cache inventories after a partition**.

## Research signal

Set reconciliation is an established distributed-systems problem. Rateless IBLT work shows that compact reconciliation can remain efficient across widely varying set differences, while a 2026 preprint explores self-sizing IBLTs when the difference size is unknown. These are algorithms to benchmark in software, not physical-performance claims for PollicinoNet.
