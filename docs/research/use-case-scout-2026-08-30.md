# PollicinoNet use-case scouting — 2026-08-30

Status: research checkpoint

## Repository state checked

PR #52 and `pollicinonet-use-case-index.md` were inspected before scouting. The catalog already contained 27 families covering DNA/topic data mules, content/reference distribution/search, emergency bulletin, sensor ferry, scheduled mobility, fleet management, classroom resources, encounter traces, citizen science, backup, Raiatea, rural kiosk, map delta, physical assets, public transport, trust/revocation, time anchors, private mailbox, task coordination, Internet egress, field evidence, relay game, edge-AI artifacts, federated learning, robots/drones and delay-tolerant compute.

Repository searches for `prefetch/cache preposition`, `service discovery/capability directory`, `transparency witness gossip`, `physical custody/handoff` and `erasure coding/shards` found no existing use-case documents under other names.

This round therefore adds five distinct workload families rather than another generic content, sensor, mobility or security variant.

## New use cases added

### UC-PREFETCH-001 — Mobility-aware cache prepositioning

Use the dense morning school phase to seed a bounded set of objects/references on carriers likely to reach different territorial clusters later.

Distinct criterion: **placement utility before the graph fragments**, measured as delivery gain per seeded/stored byte. This is not ordinary content transfer or route selection.

Difficulty: medium. Start with greedy/random/popularity/cluster-aware baselines and finite caches before any prediction/ML policy.

### UC-SERVICE-001 — Offline service and capability directory

Carry compact, expiring advertisements saying that a node can eventually provide an enrolled capability such as Internet egress, reference resolution, tiny compute, sensor topic or school service.

Distinct criterion: **capability discovery and freshness** when requester and provider are not contemporaneously connected. Discovery never implies authorization.

Difficulty: medium. A minimal signed explicit record can be tested immediately; shared wire-format adoption remains gated by reuse across EGRESS/COMPUTE/CONTENT.

### UC-COURIER-001 — Physical object custody and handoff

Track delayed handoff/return receipts for supervised sensor kits, robot parts, sample containers or school/lab items while the physical object and its digital receipt may travel by different paths.

Distinct criterion: **physical custody generation and handoff correctness**, not asset reservation or digital-evidence integrity.

Difficulty: medium. Strong tangible educational pilot after HW-006 using harmless objects, QR/NFC/BLE locally and LoRa/store-carry-forward for compact receipts.

### UC-WITNESS-001 — Offline transparency / witness gossip

Student-carried nodes exchange compact signed publication checkpoints from test logs. When partitions reunite, conflicting signed views or rollback can be detected by an auditor.

Distinct criterion: **cross-partition signed-view consistency**. Ordinary signatures prove who signed a view; witness gossip asks whether different partitions saw mutually inconsistent valid views.

Difficulty: medium-high and security-sensitive. Toy Merkle/signed-generation fixtures only until a concrete production threat model exists.

### UC-SHARD-001 — Diversity-coded multipath object carriage

Encode an authorized exact object into bounded `k-of-n` shards carried on different paths, then compare exact reconstruction probability/storage/wire cost against one-copy and full-replication baselines.

Distinct criterion: **coded redundancy under carrier dropout/storage constraints**. This is object-layer research, not PHY/network coding.

Difficulty: medium-high. Keep software-only until it beats simple bounded replication after complete byte/compute/storage accounting.

## Why these are interesting for the student network

The first three exploit concrete properties of the proposed Messina educational topology:

```text
morning: school mixing hub
        |
        +-- pre-position selected objects/references
        +-- learn safe service advertisements
        +-- issue/merge supervised item receipts
        |
        v
afternoon: pseudonymous territorial clusters
        |
        +-- store-carry-forward / physical mobility
        |
        v
home/school rich link
```

Public labels such as Rometta, Spadafora, Saponara or Villafranca can be used for synthetic cohorts only. No LoRa coverage, inter-town reach or contact duration is assumed.

WITNESS is attractive because very small security checkpoints naturally fit scarce/disconnected exchange. SHARD is attractive scientifically because the student network may eventually provide independent mobility paths, but it remains behind a strong simple-replication gate.

## Top three from this round

### 1. UC-PREFETCH-001

Best research/application candidate. The school is already PollicinoNet's dense mixing hub; the new question is whether we can use that short dense phase deliberately rather than merely reacting after the network fragments.

Immediate experiment: 30–50 synthetic student nodes, finite caches, four logical territorial clusters, 100 objects with relevance/deadline, random carrier absence. Compare no prefetch, random, popularity-only and simple cluster-aware pre-positioning under identical afternoon contacts. Measure deadline delivery, seeded bytes, afternoon wire bytes and wasted cache.

### 2. UC-SERVICE-001

Best infrastructure candidate. EGRESS, COMPUTE and CONTENT already need to know that a suitable gateway/resolver/worker exists. A minimal capability record could let those independent use cases reuse one simple discovery primitive without exposing IP-style topology or personal device details.

Immediate experiment: providers appear/disappear, advertisements become stale, multiple gateways compete, requests use a stale provider and fail closed. Test whether `service type + provider ID + generation + expiry + rendezvous hint` is enough before inventing richer negotiation.

### 3. UC-COURIER-001

Best new visible field activity. A supervised sensor kit or robot part creates a real physical state transition that students can understand, while Pollicino carries only tiny receipts. It needs no GPS and can use pseudonymous teams/items.

Immediate experiment: synthetic `ISSUED -> IN_CUSTODY -> HANDED_OFF -> RETURNED` records with duplicate/out-of-order/conflicting receipts, then later a supervised physical kit pilot after HW-006.

WITNESS is security-research infrastructure and therefore Tier B. SHARD is deliberately Tier C until it defeats simple replication on a preregistered workload.

## Literature / standards context used

- RFC 4838 DTN architecture: scheduled and opportunistic contacts are first-class DTN concepts: https://datatracker.ietf.org/doc/rfc4838/
- Mobility-aware caching / MobiCacher: https://arxiv.org/abs/1407.1307
- Context-aware proactive caching: https://arxiv.org/abs/1606.04236
- DTN IP Neighbor Discovery explicitly discusses advertising services together with or separately from neighbor discovery: https://datatracker.ietf.org/doc/id/draft-irtf-dtnrg-ipnd-00.html
- 2026 IETF SAND draft studies secure advertisement/neighborhood discovery across heterogeneous DTN links: https://datatracker.ietf.org/doc/draft-ietf-dtn-bp-sand/
- RFC 9162 Certificate Transparency v2 notes that conflicting signed tree views can be detected by clients comparing Signed Tree Heads (gossip): https://www.rfc-editor.org/rfc/rfc9162.html
- Historical CT gossip draft explored Signed Tree Head pollination: https://datatracker.ietf.org/doc/draft-ietf-trans-gossip/
- DTN coding research studies Reed-Solomon/network-coding redundancy versus replication/delivery probability: https://arxiv.org/abs/0907.5430

These references motivate workload families and simple baselines. None provides physical evidence for PollicinoNet, LoRa or Messina.

## What can be tested before hardware

All five new cases can start as `MODEL_SYNTHETIC`:

- PREFETCH: morning cache-placement policies, finite storage, prediction errors, carrier absence and afternoon deadline delivery;
- SERVICE: capability generations/expiry, stale providers, duplicate advertisements, provider selection and authorization separation;
- COURIER: item state machine, out-of-order receipts, conflict handling and catalog convergence;
- WITNESS: signed test checkpoints, deliberate split views, rollback and detection delay;
- SHARD: one-copy versus replication versus k-of-n coded diversity under carrier dropout/storage quotas.

No synthetic town-labeled topology is measured RF coverage.

## Physical evidence required later

HW-006 remains the first RF gate and the frozen first campaign remains **42-byte frames / 2 dBm**, same-room -> separation -> wall -> multi-wall/floor -> outdoor.

After that:

- PREFETCH: real school contact density, seeding capacity/energy and privacy-safe carrier-pattern stability;
- SERVICE: real advertisement latency/energy plus embedded readiness mapping for enrolled services;
- COURIER: supervised QR/NFC/BLE handoff ergonomics and real receipt convergence, without student tracking;
- WITNESS: only after the software threat model is correct, measure tiny-checkpoint exchange/storage/energy; production security requires independent review;
- SHARD: separate embedded coding CPU/RAM/energy gate plus measured path diversity; HW-006 alone does not justify erasure coding.

No use case changes the frozen LoRa PHY and no physical result is claimed in this scouting checkpoint.

## Repository changes

Added:

- `uc-prefetch-001-mobility-aware-cache-prepositioning.md`;
- `uc-service-001-offline-service-capability-directory.md`;
- `uc-courier-001-physical-object-custody-handoff.md`;
- `uc-witness-001-offline-transparency-witness-gossip.md`;
- `uc-shard-001-diversity-coded-multipath-object-carriage.md`;
- this checkpoint.

Updated:

- `pollicinonet-use-case-index.md` — date, total count (32), five new entries, priority tiers, workload distinctions, Messina scenario notes and physical-evidence boundaries.

Documentation/research only. No source code, LoRa PHY value or hardware configuration is modified by this scouting round.
