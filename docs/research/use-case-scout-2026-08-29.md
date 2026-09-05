# PollicinoNet use-case scouting — 2026-08-29

Status: research checkpoint

## Repository state checked

PR #52 and its current research head were inspected before scouting. The catalog already contains DNA/topic data mules, content/reference distribution/search, emergency bulletin, sensor ferry, scheduled mobility, fleet management, classroom resources, encounter traces, citizen science, backup, Raiatea, rural kiosk, map delta, physical assets, public transport, trust/revocation, time anchors, edge-AI artifacts, robot/drone exchange and delay-tolerant compute.

The branch has also advanced since the previous scout: a host-side `NodeBearerRuntime` now prototypes stable object state across `CONNECTED_MESH`, `OPPORTUNISTIC_DTN` and `RICH_HOME`, while LoRaMesher host validation remains explicitly separate from real-board/RF evidence. This scouting round therefore gives extra weight to application workloads that genuinely stress cross-bearer state without changing the frozen PHY.

No new case below is merely another generic sensor, content, vehicle or bulletin variant.

## New use cases added

### UC-MSG-001 — Private delay-tolerant mailbox

Small end-to-end-encrypted mailbox messages can be carried through nodes that never see plaintext; delayed receipts return later.

Distinct criterion: destination-specific confidentiality, metadata minimization and asynchronous receipt/replica retirement.

Difficulty: medium-high. Start with encrypted fixtures/bot endpoints, not real student chats.

### UC-TASK-001 — Offline task and volunteer coordination board

Task cards move through `OPEN -> CLAIMED -> DONE/EXPIRED/CANCELLED` while partitions can create conflicting claims.

Distinct criterion: safe conflict/lease/deadline resolution for work state, rather than merely broadcasting information.

Difficulty: medium. Strong school-lab workload and later emergency-drill research candidate.

### UC-EGRESS-001 — Opportunistic Internet request/reply ferry

A disconnected node sends a bounded request; a student relay later reaches trusted Wi-Fi/Internet, executes it through an allowlisted service adapter, stores the response and carries it back.

Distinct criterion: idempotent request/reply correlation and egress trust across `DTN -> RICH_HOME -> DTN`.

Difficulty: medium-high. Do not build an open proxy.

### UC-FL-001 — Delay-tolerant federated evaluation / learning rendezvous

Edge clients produce contributions from different model generations. Intermittent mobility makes updates stale; not every eventually delivered update should necessarily be aggregated.

Distinct criterion: staleness-aware learning/evaluation convergence and participation fairness, not static AI artifact synchronization.

Difficulty: high. Synthetic/public datasets and tiny models first; full modern gradients are not assumed to fit LoRa.

### UC-EVIDENCE-001 — Integrity-first field evidence manifest ferry

Large photos/videos/logs remain on rich storage while LoRa carries hash/provenance/custody manifests that bind later retrieval to exact bytes.

Distinct criterion: integrity/provenance across delayed custody. This is not claimed as a legally compliant chain-of-custody system.

Difficulty: high because security, time, key custody and human procedure dominate hashing itself.

### UC-GAME-001 — Opportunistic relay challenge

Signed synthetic game tokens/puzzle fragments create a safe, controlled student workload that requires store-carry-forward and can be replayed in simulation.

Distinct criterion: a pedagogical field-test harness with known expected application outcomes.

Difficulty: low-medium. Strong candidate for a supervised first deployment after physical/privacy gates.

## Top three from this round

### 1. UC-TASK-001

Best combined research + educational + Civil Protection-adjacent case. It introduces a real distributed-systems problem that the existing bulletin/content workloads do not: conflicting state transitions under partitions. It can begin with harmless lab tasks and later support a separately governed drill.

Immediate software experiment: three afternoon clusters, 50 task cards, concurrent claims, finite leases, clock uncertainty and a next-morning school merge. Compare authoritative-hub, generation/first-valid-claim and only then a CRDT-like alternative. Measure duplicate work, stale resurrection, deadline success and bytes.

### 2. UC-EGRESS-001

Best practical multi-bearer case. It directly exercises the new bearer runtime: an object starts in `OPPORTUNISTIC_DTN`, is serviced only in `RICH_HOME`, then returns to the DTN without losing identity/idempotency.

Immediate software experiment: local fake service, intermittent gateways, duplicate request injection, asymmetric return paths, response-as-reference for large replies and explicit egress authorization.

### 3. UC-GAME-001

Best candidate for a first student-facing physical workload after HW-006. It uses synthetic data, needs no GPS, can avoid private content, generates known traffic and makes the store-carry-forward concept visible to students.

Immediate software experiment: signed tokens that require three distinct logical relay roles and one carry-required partition before returning to the referee. Replay the exact fixture with multiple routing baselines.

`UC-FL-001` is strategically interesting for AI research but is deliberately Tier C until a tiny-model software experiment proves that Pollicino's contribution-generation semantics add value beyond `UC-AI-001`. `UC-EVIDENCE-001` has strong emergency/robot/citizen-science potential but needs stricter security/governance. `UC-MSG-001` is technically natural but human messaging among students has a higher privacy/abuse burden, so bot/test endpoints come first.

## Literature / standards context used

- RFC 9171 BPv7: intermittent connectivity, physical motility and store-carry-forward overlay: https://www.rfc-editor.org/rfc/rfc9171.html
- Briar: current peer-to-peer encrypted messaging over Bluetooth/Wi-Fi/Tor, including offline nearby messaging: https://briarproject.org/
- University of Waterloo KioskNet design: ferries move data between rural kiosks and Internet gateways/proxy: https://uwspace.uwaterloo.ca/items/658cdf6d-8d56-4ea5-b832-b94a1606979b
- Hanssen 2025: offline/weakly connected emergency-management replication and CRDT trade-offs: https://doi.org/10.5324/b816jf45
- Mobility-aware asynchronous FL with intermittent contact/staleness/sparsification: https://arxiv.org/abs/2506.07328
- FedStale: stale updates plus heterogeneous participation can materially affect FL behavior: https://doi.org/10.3233/FAIA240849
- NIST chain-of-custody definition: https://csrc.nist.gov/glossary/term/chain_of_custody

These sources justify workload families and caution boundaries. They are not physical evidence for PollicinoNet.

## What can be tested before hardware

The existing synthetic/contact-window and bearer-runtime work can already support:

- MSG: destination-specific encrypted fixtures, delayed receipts, replica retirement and metadata accounting;
- TASK: conflicting claims, leases, deadlines, causal ordering and next-morning convergence;
- EGRESS: idempotent request/reply over `DTN -> RICH_HOME -> DTN`, gateway churn and asymmetric reply paths;
- FL: tiny-model synchronous versus stale/asynchronous aggregation over synthetic contacts;
- EVIDENCE: hash manifests, staged corruption/replay, missing rich objects and custody receipts;
- GAME: signed token/puzzle fixtures with controlled routing requirements and anti-replay.

All remain `MODEL_SYNTHETIC` until physical evidence exists.

## Physical evidence required later

HW-006 remains the first RF gate and the frozen first campaign remains **42-byte frames / 2 dBm**, same-room -> separation -> wall -> multi-wall/floor -> outdoor.

After that:

- MSG: delivery/receipt behavior and storage/energy with test endpoints; human messaging only after privacy/security governance;
- TASK: supervised checkpoint usability and real task-delivery latency;
- EGRESS: LoRa-to-Wi-Fi lifecycle, enrolled gateway behavior, turnaround and energy;
- FL: separate edge-compute/battery measurements plus measured contact budgets; HW-006 alone does not validate ML feasibility;
- EVIDENCE: capture/hash/storage/handoff timing and security procedure, without claiming legal admissibility;
- GAME: a supervised synthetic-token pilot measuring real encounter/delivery behavior without GPS or movement incentives.

No use case changes the frozen LoRa PHY and no synthetic result is presented as Messina-area coverage/capacity evidence.

## Repository changes

Added:

- `uc-msg-001-private-delay-tolerant-mailbox.md`;
- `uc-task-001-offline-task-coordination-board.md`;
- `uc-egress-001-opportunistic-internet-request-reply-ferry.md`;
- `uc-fl-001-delay-tolerant-federated-learning-rendezvous.md`;
- `uc-evidence-001-integrity-first-field-evidence-ferry.md`;
- `uc-game-001-opportunistic-relay-challenge.md`;
- this checkpoint.

Updated:

- `pollicinonet-use-case-index.md` — date, six entries, priority tiers, workload distinctions and software/physical test dimensions.

Documentation/research only. No source code, LoRa PHY value or hardware configuration is modified by this scouting commit.
