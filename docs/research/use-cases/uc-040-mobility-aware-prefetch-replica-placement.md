# UC-040 — Mobility-Aware Prefetch and Replica Placement

## Idea

Use the real contact graph learned by UC-008 to decide **which useful objects should be copied to which student/relay nodes before they are requested or before a likely future contact**.

Instead of treating every relay as an empty courier, some nodes become small opportunistic caches chosen because their measured mobility makes them good places to pre-position content.

## Problem solved

A content request may arrive too late if the only copy is far away and contacts are rare. Blindly replicating everything everywhere wastes storage and transfer opportunities.

UC-040 asks a concrete question:

```text
Given measured contacts, storage limits and predicted demand,
where should we place the next few replicas/chunks?
```

This differs from UC-024, which discovers content after a need appears. UC-040 tries to make likely future needs cheaper by preparing the network in advance.

## Actors / nodes

- student LoRa relay/store-and-forward nodes;
- school cache/NAS/server;
- home/lab caches;
- requester nodes;
- UC-008 observatory producing privacy-safe contact traces;
- optional planner that computes replica/prefetch suggestions.

## Why PollicinoNet fits

PollicinoNet already separates compact control from bulk transfer and already has content-addressed objects.

- **DISCOVERY:** cache capacity, approximate future contact opportunity, object-family demand hint;
- **EXACT:** object/chunk root, replica assignment, cache epoch, placement plan identity;
- **SEMANTIC:** labels such as `tomorrow's lesson pack` or `Milazzo map tiles`, never a replacement for exact object hashes.

The planner can exploit physical student movement as a network resource while still using Wi-Fi/LAN/Internet/physical carry for large bytes.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** compact cache inventory, need/demand hints, placement assignment, completion status;
- **BLE:** opportunistic nearby chunk exchange;
- **Wi-Fi/LAN:** normal prefetch/bulk replication;
- **Internet:** seed content at connected nodes;
- **physical transport:** student-carried storage or devices move prefetched objects between disconnected areas.

## What we can test now in software

Reuse synthetic or later measured UC-008 contact traces and implement several placement policies:

```text
A. no prefetch
B. replicate to most-connected node
C. replicate near predicted requester
D. diversity-aware placement
E. storage/energy-budget-aware placement
```

Then compare them under the same trace and workload.

Test:

- storage quotas;
- stale demand prediction;
- missed predicted contacts;
- repeated/duplicate objects;
- object popularity changing over time;
- one relay becoming unavailable;
- placement of whole objects vs selected chunks/shards;
- combination with UC-018 erasure-coded shards;
- combination with UC-029 dependency closures and UC-017 map tiles;
- policy that forbids sensitive objects on selected nodes even when they are topologically useful.

Useful metrics include request satisfaction delay, cache hit rate, completed-object rate, extra bytes introduced by prefetch, wasted prefetch bytes, storage occupancy and fairness across carrier nodes.

## What requires real hardware

- real privacy-safe contact traces from UC-008;
- several student relay nodes with bounded cache storage;
- repeated controlled routes so the same prefetch policies can be compared;
- real object movement over LoRa→rich-bearer handoffs;
- measured contact duration, transfer success and storage/energy impact where instrumentation permits.

No simulator result should be promoted to a claim that a given student/node is a good relay until measured traces support it.

## Messina teaching scenario

Use controlled recurring routes among school, Rometta, Spadafora/Venetico, Villafranca and Milazzo.

Suppose a class in one area is likely to need tomorrow's versioned course pack. The school cache has the complete pack today. UC-040 may choose two student nodes with different measured contact patterns and pre-position different verified chunks while they are on school Wi-Fi.

The next day, requesters try to reconstruct the pack using local encounters before falling back to Internet or the school server.

The experiment compares a placement algorithm against a deliberately simple baseline on **the same real contact trace**.

## Privacy / security

Mobility-aware optimization can easily become person tracking if designed carelessly.

- use pseudonymous/rotating node identities;
- operate on coarse contact graphs rather than home addresses or continuous GPS tracks;
- make participation opt-in for real students;
- separate topology usefulness from personal identity;
- never prefetch private content to a relay merely because it is well connected;
- encrypt payloads so storage/carry does not imply read authority;
- cap storage, bandwidth and energy burden per participant;
- preserve an explainable reason for every placement decision.

## Difficulty

**High.** The mechanics are simple, but useful placement requires measured mobility, fair resource budgets and a baseline-controlled experiment that distinguishes real benefit from overfitting to one trace.

## Research signal

Recent ICN research continues to study proactive caching, nearby cache collaboration and resource-aware placement, while DTN research continues to model forwarding decisions over contact graphs and uncertain contacts. Those ideas make UC-040 worth testing, but PollicinoNet must compare policies using its own measured student-network traces.

References:

- https://journals.sagepub.com/doi/abs/10.3233/JHS-240059
- https://personales.upv.es/thinkmind/NetSer/NetSer_v17_n34_2024/netser_v17_n34_2024_5.html
