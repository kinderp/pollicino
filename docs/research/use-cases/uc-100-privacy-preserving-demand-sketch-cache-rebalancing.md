# UC-100 — Privacy-Preserving Demand Sketch and Cache Rebalancing

## Idea

Let PollicinoNet caches exchange **compact, delayed summaries of demand** so they can decide what to replicate, keep or evict without building a central log of exactly which student requested which document/model/package.

Instead of sending raw request histories, nodes can exchange bounded summaries such as top-K counters, Count-Min Sketch-like frequency estimates or coarse topic demand.

The objective is:

> improve cache usefulness while revealing less about individual reading, software or AI-model choices.

## Problem solved

UC-040 can place replicas based on expected future mobility, but it still needs a useful demand signal. A naive solution is to collect every request centrally. That creates several problems:

- request histories can reveal interests or school activity;
- always-online telemetry is unavailable by design;
- exact logs are larger than the decision usually needs;
- old popularity may persist long after demand changes;
- a few heavy requesters can distort cache policy;
- cache nodes need local autonomy under storage budgets.

We need a delayed, mergeable demand signal that is useful for placement/eviction but does not require permanent per-user histories.

## Actors / nodes

- requester nodes;
- student relay/store-and-forward nodes;
- local content/model/package caches;
- optional school cache coordinator;
- optional privacy-preserving aggregator.

## Why PollicinoNet fits

The useful signal is much smaller than the content it controls.

- **DISCOVERY:** cache advertises capacity, topic/profile support and sketch epoch;
- **EXACT:** sketch type/version, epoch, salt/key ID where relevant, parameters and content/topic identifiers used by the selected profile;
- **SEMANTIC:** `hot`, `cooling`, `under-replicated`, `evict-candidate` or `unknown-demand` are decisions derived from the summaries, not facts carried directly by LoRa.

Demand summaries can move opportunistically over LoRa while actual course packs, models or package archives move over Wi-Fi/BLE/physical transport.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact demand sketch, top-K summary, cache pressure, epoch and replica recommendation digest;
- **BLE:** exchange of a larger local summary between nearby caches;
- **Wi-Fi/LAN:** content replication/eviction reconciliation and full experiment traces;
- **Internet:** optional fast-path synchronization when available;
- **physical transport:** student laptop/SSD carries large replicas selected by the policy.

## What we can test now in software

Create a synthetic catalog containing, for example:

- Python course packs;
- Git/dependency bundles;
- Raiatea document collections;
- several local AI model variants;
- map tiles;
- deliberately unpopular objects.

Generate request streams for multiple disconnected groups and compare policies:

1. no demand exchange;
2. exact centralized request log baseline;
3. top-K-only summaries;
4. Count-Min Sketch-like summaries;
5. decayed demand summaries;
6. demand + UC-008 mobility/contact signal;
7. demand + UC-095 local relay/cache budgets.

Test:

- sudden popularity shift;
- one noisy/heavy requester;
- false positives from a sketch;
- stale summary arriving after a newer epoch;
- cache with different storage capacity;
- conflicting recommendations;
- object deletion/tombstone from UC-077;
- rights/policy restriction from UC-076;
- content that is popular but too large for the current cache.

Useful metrics include cache-hit ratio, bytes moved over rich bearers, eviction churn, stale-demand decisions, fairness between content classes, sketch size and divergence from the exact-log baseline.

No improvement claim should be made for the real student network until the policy is replayed against real UC-008/UC-098 traces and then tested physically.

## What requires real hardware

A first physical test can use 5–8 nodes with deliberately small caches.

Suggested procedure:

1. seed each group with a different subset of harmless course/test content;
2. generate scripted requests over several sessions;
3. allow only compact demand summaries to move over LoRa;
4. perform chosen replica transfers when Wi-Fi/BLE contact becomes available;
5. repeat the same workload with different policies;
6. compare cache hits and transferred bytes from the recovered logs.

Energy, contact duration, throughput and radio overhead remain empirical measurements.

## Messina teaching scenario

Suppose groups near Messina, Villafranca, Rometta/Venetico and Spadafora request different materials during a school week. The Rometta group may suddenly need a Python pack while Messina has multiple copies and Spadafora has free storage but few requests.

Rather than upload every student's request log, nodes ferry a compact statement such as:

```text
epoch = 42
cache_pressure = 0.81
approx_hot = [python-pack-v5, map-zone-R, model-small-it]
sketch_hash = ...
```

Combined with observed mobility, the system can decide where a useful replica should travel next.

## Privacy / security

- do not carry requester identity in demand summaries;
- aggregate over minimum group/time windows before exporting a summary;
- use coarse content/topic identifiers when exact object IDs would expose sensitive interests;
- rotate sketch epochs/salts where appropriate to reduce long-term linkage;
- enforce local opt-out and storage/traffic budgets;
- treat sketches as estimates, never proof that a specific user requested something;
- defend against demand poisoning/ranking manipulation with bounded per-node contribution and signed/authorized summaries where needed;
- never replicate an artifact merely because it is popular if UC-076 policy forbids it;
- preserve deletion/expiry state from UC-077.

## Difficulty

**Medium-high.** Sketches are straightforward; robust decay, poisoning resistance, privacy choices and interaction with mobility/storage constraints require careful experiments.

## Why this is distinct from nearby use cases

- **UC-035:** computes generic federated sketches/aggregates; UC-100 uses bounded demand summaries specifically to drive cache placement/eviction.
- **UC-040:** decides mobility-aware prefetch/replica placement; UC-100 supplies a privacy-minimized demand signal that UC-040 can consume.
- **UC-045:** chooses what to transfer during one short contact; UC-100 changes what caches should hold before that contact.
- **UC-095:** protects volunteer resource budgets; UC-100 optimizes content utility inside those budgets.

## Research / implementation signal

Streaming sketches such as Count-Min Sketch are established tools for bounded-memory frequency estimation. Recent 2026 work continues to use mergeable sketches for secure/outsourced streaming analytics, reinforcing that compact approximate summaries remain useful when exact event streams are too expensive or sensitive to centralize. PollicinoNet can begin with very small, transparent sketches before considering stronger privacy mechanisms.

References:

- https://doi.org/10.1145/3802110
- https://dimacs.rutgers.edu/~graham/pubs/papers/cm-full.pdf
