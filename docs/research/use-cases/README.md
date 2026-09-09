# PollicinoNet use-case catalog

This catalog turns PollicinoNet research primitives into concrete scenarios that can be simulated first and validated later on real nodes.

Core rules for every use case:

- do not modify the frozen LoRa PHY as part of use-case work;
- `DISCOVERY`, `EXACT` and `SEMANTIC` remain information contracts, not radio technologies;
- prefer LoRa for compact discovery/control and a richer bearer for bulk bytes whenever one is available;
- do not claim physical range, reliability, airtime or energy results without real measurements;
- safety-critical/emergency scenarios remain experiments until independently validated;
- protect identity, location, content metadata and authorization at the application layer.

## Catalog

| ID | Use case | Main problem | Best first experiment | HW need | Difficulty |
|---|---|---|---|---|---|
| [UC-001](uc-001-student-knowledge-ferry.md) | Student Knowledge Ferry | disconnected school/home/town islands | synthetic student mobility + store-and-forward | later | Medium |
| [UC-002](uc-002-signed-community-bulletin.md) | Signed Community Bulletin / civil-protection drill | resilient small authoritative messages | signatures + expiry + network partitions | later | Medium |
| [UC-003](uc-003-rural-sensor-courier.md) | Rural Sensor Courier | collect data without permanent backhaul | synthetic sensor backlog + moving relay | useful early | Low–Medium |
| [UC-004](uc-004-offline-ai-artifact-distribution.md) | Offline AI Artifact Distribution | models/datasets across intermittent links | chunk inventory + cache reconciliation | later | Medium–High |
| [UC-005](uc-005-mobile-gateway-uav-vehicle.md) | Mobile Gateway / UAV / vehicle | fixed nodes without end-to-end paths | contact-window and queue simulator | required for claims | High |
| [UC-006](uc-006-raiatea-document-capsules.md) | Raiatea Document Capsules | exact document/version distribution | versioned corpus + missing-chunk retrieval | optional first | Medium |
| [UC-007](uc-007-edge-ai-event-scout.md) | Edge AI Event Scout | send interesting events, not raw streams | semantic event + exact evidence simulator | later | High |
| [UC-008](uc-008-network-observatory-contact-graph.md) | Privacy-Preserving Network Observatory | learn real contact opportunities and relay value | synthetic contact graph + relay planning | useful early | Medium |
| [UC-009](uc-009-signed-firmware-config-ferry.md) | Signed Firmware and Configuration Ferry | maintain isolated sensors/robots safely | signed manifest + interrupted-update simulator | required before claims | High |
| [UC-010](uc-010-robot-mission-mailbox.md) | Robot Mission Mailbox | asynchronous jobs for intermittently connected robots | idempotent mission queue + simulated outages | useful early | Medium–High |
| [UC-011](uc-011-dnatrace-encounter-capsules.md) | DNATrace Encounter Capsules | pseudonymous offline discovery with later consent | synthetic traces + consent/rendezvous state machine | later | Medium |
| [UC-012](uc-012-opportunistic-backup-restore.md) | Opportunistic Backup and Restore | exact P2P recovery across intermittent nodes | node-loss + content-addressed restore | useful early | Medium–High |
| [UC-013](uc-013-field-report-evidence-capsules.md) | Field Report and Evidence Capsules | bring signed observations back from disconnected field teams | synthetic incident/report simulator | useful early | Medium |
| [UC-014](uc-014-opportunistic-capability-compute-exchange.md) | Opportunistic Capability and Compute Exchange | discover and use compute/storage/connectivity across partitions | capability scheduler + idempotent job manifests | useful early | High |
| [UC-015](uc-015-partition-tolerant-resource-ledger.md) | Partition-Tolerant Resource Ledger | reconcile inventory/requests while disconnected | CRDT/log convergence under partition and reorder | useful early | Medium |
| [UC-016](uc-016-federated-adapter-round-courier.md) | Federated Adapter Round Courier | coordinate AI updates across intermittent clients | synthetic clients + exact adapter manifests | later | High |
| [UC-017](uc-017-offline-map-tile-ferry.md) | Offline Map and Route Tile Ferry | keep useful map subsets available without Internet | versioned tile cache + area-of-interest reconciliation | useful early | Medium |
| [UC-018](uc-018-erasure-coded-content-swarm.md) | Erasure-Coded Content Swarm | reconstruct exact content from multiple partial carriers | `k-of-n` shards + synthetic contact traces | useful early | High |
| [UC-019](uc-019-offline-trust-revocation-ferry.md) | Offline Trust Epoch and Revocation Ferry | keep revocation/key-rotation state current across partitions | signed trust epochs + downgrade/replay tests | useful early | Medium–High |
| [UC-020](uc-020-trusted-time-checkpoint-ferry.md) | Trusted Time Checkpoint Ferry | freshness/expiry evidence without permanent time service | drift + delayed signed-checkpoint simulator | useful early | Medium–High |
| [UC-021](uc-021-threshold-sealed-sensitive-courier.md) | Threshold-Sealed Sensitive Courier | let untrusted carriers transport sensitive content without reading it | encrypted object + `k-of-n` key shares | later | High |
| [UC-022](uc-022-multi-witness-event-corroboration.md) | Multi-Witness Event Corroboration | avoid trusting one noisy sensor/edge inference | signed claims + delayed/conflicting witnesses | useful early | Medium–High |
| [UC-023](uc-023-delay-tolerant-private-mailbox.md) | Delay-Tolerant Private Mailbox | private asynchronous human messaging across disconnected groups | encrypted outbox + courier + delayed receipt | useful early | Medium |
| [UC-024](uc-024-content-need-rendezvous.md) | Content-Need Rendezvous / Interest Ferry | request content without knowing which peer currently has it | `ContentNeed` propagation + arbitrary cache satisfaction | useful early | Medium–High |
| [UC-025](uc-025-scheduled-mobility-backbone.md) | Scheduled Mobility Backbone | exploit recurring contact opportunities without assuming they occur | uncertain contact-plan routing vs baseline | useful early | Medium–High |
| [UC-026](uc-026-delegated-offline-action-ticket.md) | Delegated Offline Action Ticket | authorize one scoped offline action without broad credentials | signed one-use ticket + replay/crash tests | useful early | High |
| [UC-027](uc-027-post-event-vibration-log-courier.md) | Post-Event Vibration / Structural Log Courier | move event summaries now and exact high-rate evidence later | synthetic waveforms + summary/hash retrieval | useful early | Medium–High |
| [UC-028](uc-028-offline-collaborative-notebook.md) | Offline Collaborative Notebook | concurrent human editing across disconnected groups | CRDT/op-log convergence under partition/reorder | useful early | Medium–High |
| [UC-029](uc-029-opportunistic-software-dependency-cache.md) | Opportunistic Software Dependency Cache | make reproducible dev environments available from nearby caches | dependency closure + multi-provider cache simulator | useful early | Medium–High |
| [UC-030](uc-030-privacy-preserving-muster-checkin.md) | Privacy-Preserving Muster / Safety Check-In | delayed checkpoint presence without continuous tracking | rotating synthetic IDs + replay/stale check-in tests | useful early | Medium |
| [UC-031](uc-031-sensor-calibration-provenance-ferry.md) | Sensor Calibration and Provenance Ferry | keep calibration version/evidence explicit on offline sensors | synthetic drift + versioned calibration propagation | useful early | Medium |
| [UC-032](uc-032-active-learning-label-courier.md) | Active-Learning Label Courier | spend scarce annotation/network effort on informative samples | public/synthetic data + delayed label workflow | later | Medium–High |
| [UC-033](uc-033-secure-rich-bearer-handoff-bootstrap.md) | Secure Rich-Bearer Handoff Bootstrap | securely switch from LoRa discovery/control to BLE/Wi-Fi/LAN transfer | handoff state machine + replay/wrong-peer tests | useful very early | Medium–High |
| [UC-034](uc-034-raiatea-query-to-data-search-courier.md) | Raiatea Query-to-Data Search Courier | answer offline document queries without moving the full corpus/index | versioned corpus + delayed query/result courier | useful early | Medium–High |
| [UC-035](uc-035-federated-sketch-aggregate-courier.md) | Federated Sketch / Aggregate Courier | compute useful network/sensor aggregates without forwarding every raw record | mergeable sketches + duplicate/reorder tests | useful early | Medium |
| [UC-036](uc-036-proactive-integrity-scrub-repair-swarm.md) | Proactive Integrity Scrub and Repair Swarm | detect latent corruption/missing replicas before restore time | injected bit-rot/deletion + delayed peer repair | useful early | Medium–High |
| [UC-037](uc-037-privacy-safe-mobile-environmental-transect.md) | Privacy-Safe Mobile Environmental Transect | gain coarse environmental spatial coverage without retaining student trajectories | synthetic coarse-cell sampling + delayed batches | useful early | Medium |

## Current top 3 next experiments for the Messina student network

### 1. UC-008 — Privacy-Preserving Network Observatory

This still comes first because it produces the **real contact traces** needed to make later routing/content simulations less hypothetical. Controlled routes with 3+ boards can reveal contact windows, useful relays and queue opportunities without requiring continuous coverage. The privacy rule is strict: measure encounters, not student lives.

### 2. UC-033 — Secure Rich-Bearer Handoff Bootstrap

This is now the most important protocol-level field experiment after contact measurement because many other use cases already assume `LoRa discovery -> BLE/Wi-Fi/LAN bulk transfer`. Two or three dual-radio endpoints are enough to test exact peer/object binding, short-lived rendezvous material, replay rejection and measured handoff time without changing the LoRa PHY.

### 3. UC-023 — Delay-Tolerant Private Mailbox

This remains the best immediate human-visible service experiment. Four boards are enough to create two disconnected groups plus a moving courier, and success is objectively easy to understand: one encrypted logical message leaves an outbox, survives disconnection/duplication, arrives once and eventually returns a receipt.

### Strong follow-ups

- **UC-024 — Content-Need Rendezvous / Interest Ferry:** the strongest architectural pull-side primitive once UC-033 gives us a measured rich-bearer handoff path.
- **UC-034 — Raiatea Query-to-Data Search Courier:** high-value document/edge-search scenario because only the compact query/result travels by DTN while the corpus remains where it already exists.
- **UC-036 — Proactive Integrity Scrub and Repair Swarm:** turns backup from a passive restore feature into an actively verified P2P durability experiment.
- **UC-035 — Federated Sketch / Aggregate Courier:** compact LoRa-native analytics experiment that can reuse UC-008 data without forwarding every raw observation.
- **UC-037 — Privacy-Safe Mobile Environmental Transect:** locally meaningful IoT/crowdsensing experiment after UC-031 calibration and strict coarse-location safeguards are in place.
- **UC-028 — Offline Collaborative Notebook:** strong classroom experiment because concurrent partitioned work is visible and deterministic convergence is objectively testable while semantic conflicts remain for human review.
- **UC-029 — Opportunistic Software Dependency Cache:** practical bridge between PollicinoNet, reproducible development environments, The Blob/Nix prewarming and content-addressed P2P distribution.
- **UC-032 — Active-Learning Label Courier:** strong AI/dataset direction because it adds a human-in-the-loop label workflow distinct from model/adapter exchange.
- **UC-030 — Privacy-Preserving Muster / Safety Check-In:** compact experiment for rotating IDs, freshness and store-and-forward, but only under strict anti-surveillance rules.
- **UC-031 — Sensor Calibration and Provenance Ferry:** clean IoT/provenance experiment that can start with harmless temperature/humidity teaching sensors.
- **UC-025 — Scheduled Mobility Backbone:** strong research track after UC-008 because recurring student/rail/bus/ferry-style contact windows can be compared against schedule-blind forwarding on the same measured traces.
- **UC-019 — Offline Trust Epoch and Revocation Ferry:** strongest compact security-state experiment; pair it with UC-026 later.
- **UC-018 — Erasure-Coded Content Swarm:** concrete P2P/content-distribution experiment once real contact traces exist.
- **UC-026 — Delegated Offline Action Ticket:** excellent security/robotics experiment once trust/freshness semantics are stable; restrict hardware to harmless demo actions.
- **UC-027 — Post-Event Vibration / Structural Log Courier:** locally meaningful Messina IoT experiment that cleanly separates compact event summaries from exact high-rate evidence.
- **UC-022 — Multi-Witness Event Corroboration:** strong bridge between IoT, edge AI, emergency drills and exact evidence retrieval.
- **UC-015 — Partition-Tolerant Resource Ledger:** one of the cleanest distributed-systems experiments because payloads are tiny and convergence is objectively testable.
- **UC-017 — Offline Map and Route Tile Ferry:** highly visible content-addressed demo with real LoRa→BLE/Wi-Fi handover.
- **UC-020 — Trusted Time Checkpoint Ferry:** foundational for TTL, expiry, trust freshness and audit ordering, but separate from claims of precise radio synchronization.
- **UC-014 — Opportunistic Capability and Compute Exchange:** strategically important because nodes become discoverable compute/storage/service providers, not only content holders.
- **UC-012 — Opportunistic Backup and Restore:** important for the P2P/content-addressed track; replica placement can eventually be tested against UC-008 mobility traces.
- **UC-021 — Threshold-Sealed Sensitive Courier:** valuable for Raiatea/sensitive-document and privacy research after key-management/test infrastructure is mature.
- **UC-010 — Robot Mission Mailbox:** strong visible classroom demonstration of queued, delay-tolerant control that explicitly excludes safety-critical functions.
- **UC-016 — Federated Adapter Round Courier:** high-value AI research direction after the network simulator and artifact model are stable.

## Immediate software-only test plan

The following can be implemented without any radio hardware:

1. create a deterministic contact/mobility simulator with nodes, time windows and link availability;
2. model per-node `PollicinoStore` inventories and exact content-addressed chunks;
3. add store-and-forward queues with TTL, hop limit, priority and duplicate suppression;
4. simulate LoRa as a scarce control bearer and Wi-Fi/Internet/physical carry as richer bearers;
5. produce privacy-safe synthetic contact graphs for UC-008 and feed them into UC-001/UC-003/UC-013;
6. implement signed/idempotent state machines for UC-009, UC-010 and UC-013;
7. implement synthetic DNATrace rendezvous/consent for UC-011;
8. inject node loss and perform exact content-addressed restore for UC-012;
9. build a capability-aware job scheduler for UC-014 with exact input/output manifests, stale advertisements and retry without duplicate execution;
10. build the UC-015 synthetic resource ledger and property-test convergence under partition, reordering and duplication;
11. run UC-016 with a tiny public/synthetic model and dataset, treating LoRa only as coordination/discovery unless measurements justify more;
12. package a small open map area into deterministic content-addressed tiles for UC-017, create a second version and prove that only missing/changed tiles move;
13. implement UC-018 deterministic `k-of-n` coding, shard manifests, corruption tests and a replication-vs-coding comparison under identical synthetic contact traces;
14. implement UC-019 signed monotonic trust epochs, revocation, key rotation, stale-state exposure and replay/downgrade negative tests;
15. implement UC-020 clock-drift/reboot models and signed checkpoint propagation while preserving explicit time uncertainty;
16. implement UC-021 with a reviewed threshold-sharing library over synthetic data, proving that carriers transport shares without plaintext authority;
17. implement UC-022 signed event claims, conflicting/delayed witnesses, provenance and exact-evidence attachment after semantic corroboration;
18. implement UC-023 encrypted `MessageEnvelope`/outbox/inbox state, bounded-copy forwarding, delayed receipts and persistent duplicate suppression;
19. implement UC-024 `ContentNeed` propagation, multi-provider response, stale availability, cancellation after exact satisfaction and request-privacy tests;
20. implement UC-025 uncertain recurring `ContactPlan` routing and compare schedule-aware decisions with schedule-blind baselines under identical traces;
21. implement UC-026 canonical signed one-use action tickets, replay/crash-consistency tests and explicit interaction with UC-019/UC-020 freshness state;
22. implement UC-027 synthetic vibration windows, compact event summaries, exact evidence hashes, retention pressure and delayed evidence retrieval;
23. implement UC-028 partitioned collaborative replicas, concurrent edits, reorder/duplicate delivery, attachment-by-hash and explicit semantic-conflict marking;
24. implement UC-029 dependency-closure discovery with partial caches, multiple providers, corruption/poisoning negative tests and a tiny optional Nix/OCI backend;
25. implement UC-030 rotating synthetic IDs, checkpoint challenges, stale/replay rejection and a log that intentionally cannot reconstruct continuous movement;
26. implement UC-031 synthetic sensor drift, versioned calibration manifests, wrong-hardware rejection and exact calibration-evidence provenance;
27. implement UC-032 public/synthetic active-learning requests, delayed label returns, model/schema version binding, annotator disagreement and data-poisoning negative tests;
28. implement UC-033 `HandoffSession` state transitions, peer/object/channel binding, one-use rendezvous, wrong-peer/replay/downgrade failure tests and rich-link retry;
29. implement UC-034 a small versioned Raiatea-like corpus, delayed query courier, local search, exact result references, stale-index tests and selective final fetch;
30. implement UC-035 two or three mergeable sketch types, duplicate/reorder/dropout tests, exact baseline error measurement and privacy-leakage negative tests;
31. implement UC-036 content scrubbing with injected bit flips/deletion/stale inventory, delayed repair scheduling, multi-provider race handling and exact post-repair verification;
32. implement UC-037 synthetic coarse-cell mobile sampling, delayed batches, missing-cell discovery, UC-031 calibration binding and deliberate route-reconstruction privacy tests;
33. record TRC, delivery delay, cache hit ratio, duplicate overhead, age-of-information, completed-object rate, convergence delay, stale-work rate, trust-epoch propagation, reconstruction success, mailbox delivery/receipt delay, time-to-provider, missed-contact penalty, operation-backlog convergence, dependency bytes avoided, check-in reconciliation delay, calibration-version propagation, label turnaround, handoff setup time, query turnaround, sketch bytes/error, corruption-detection/repair delay and coarse-cell coverage as applicable.

This reuses the current architecture instead of creating a special PHY or a separate networking stack per scenario.

## Physical experiments that become necessary

After the simulator contracts are stable:

- repeatable 2-node and 3+ node relay measurements;
- controlled walking/bicycle data-mule passes;
- privacy-safe contact-window collection for UC-008;
- a UC-033 2–3 provider experiment with real LoRa discovery, multiple visible nearby peers, exact peer/object binding and measured BLE/Wi-Fi/LAN handoff time;
- a UC-023 four-node mailbox test with two disconnected groups, one moving courier and a delayed receipt;
- a UC-024 4+ node cache/request experiment where the requester cannot directly contact the content holder and the final object moves over a richer bearer;
- a UC-034 3+ node query-to-data experiment with one unreachable corpus/search node, one moving relay and later exact selected-document retrieval over UC-033;
- a UC-035 4–6 node aggregate experiment comparing raw-event forwarding with a mergeable summary under the same controlled workload;
- a UC-036 3+ storage-node experiment with disposable test data, deliberate corruption/deletion and measured detection-to-repair through a later peer contact;
- a UC-037 3–6 sensor-node controlled-route experiment using coarse public test zones, calibration/reference checks and explicit geoprivacy validation;
- a UC-028 four-node collaborative-notebook experiment with two editing islands, concurrent changes, one moving relay and measured convergence;
- a UC-029 3+ laptop/cache experiment where LoRa discovers missing dependency closure and Wi-Fi/LAN/BLE transfers only verified missing objects;
- a UC-030 controlled checkpoint drill with rotating synthetic identities, replay attempts and no continuous location collection;
- a UC-031 2–3 sensor plus reference-sensor co-location/calibration experiment before any accuracy claim;
- a UC-032 3–4 node label-request experiment using public/synthetic evidence and a richer-bearer handover to the annotator;
- repeated UC-025 controlled routes with deliberate delays/missed contacts before any claim that schedule-aware forwarding helps;
- a UC-026 harmless one-use action-ticket test on an LED/servo/demo rover with replay and power-cycle negative controls;
- a UC-027 2–3 accelerometer/IMU bench experiment with controlled vibration, LoRa summary and later exact waveform retrieval;
- sensor-node backlog collection;
- real LoRa discovery followed by BLE/Wi-Fi/LAN handover;
- one synthetic field-report relay chain with exact evidence retrieval;
- one safe rover mission-mailbox demo, explicitly excluding safety-critical control;
- 3+ storage nodes with a deliberate node-loss/restore test;
- a UC-015 split-network experiment where two groups update a synthetic ledger and a moving relay causes measured convergence;
- a UC-014 three-node capability/job experiment with an allow-listed task and one real rich-link artifact handover;
- a UC-017 three-node map-cache experiment with LoRa area/version discovery and measured Wi-Fi/BLE tile retrieval;
- a UC-018 4–6 node shard-carry experiment where no single relay has the complete object, compared against an ordinary replication baseline on the same route;
- a UC-019 4+ node trust-partition experiment with one synthetic revoked identity and measured trust-epoch propagation;
- UC-020 real clock-drift/reboot measurements against a trusted reference before stating any timing accuracy;
- UC-021 threshold-share carry only with synthetic harmless content and separate carriers;
- UC-022 3+ controlled sensor/edge witnesses with deliberate false-positive/conflict injections and later exact-evidence retrieval;
- firmware/configuration experiments only on spare non-critical hardware with rollback tests;
- federated-adapter experiments only after the software protocol is stable, with public/synthetic data first;
- only later, public-transport or UAV deployments with the relevant permission, safety and legal controls.

Measured packet loss, RSSI/SNR, airtime, latency, contact duration, energy where relevant, clock drift and reconstruction/convergence success must be recorded explicitly. Simulator outcomes must not be promoted to field claims.

## Related prior art worth watching

The use cases are consistent with existing research directions without copying their assumptions into the PollicinoNet core:

- delay-tolerant/opportunistic networking and public-transport data mules;
- DTN reliability work that explicitly avoids assuming simultaneous end-to-end paths, relevant to UC-023;
- information-centric/named-data forwarding and in-network caching, relevant to UC-024's request-by-content model;
- scheduled/semischeduled public-transport mobility models and Age-of-Information analysis, relevant to UC-025;
- cryptographically scoped offline-verifiable delegation tokens, relevant to UC-026 but not a reason to import a complex authorization stack blindly;
- LoRa vibration/geotechnical monitoring with local edge processing and event summaries, relevant to UC-027;
- offline-first CRDT/local-first collaborative editing under intermittent connectivity, relevant to UC-028 while preserving the distinction between mechanical convergence and semantic conflict;
- content-addressed software stores/binary caches and signed substituters, relevant to UC-029's dependency-closure ferry without making PollicinoNet package-manager-specific;
- privacy-preserving offline nearby-device discovery and rotating/probabilistic identity techniques, relevant to UC-030 but not permission to build a tracking system;
- distributed/reference-based calibration of low-cost sensor networks, relevant to UC-031's versioned calibration provenance;
- active learning, selective relabeling and intermittent edge-learning workflows, relevant to UC-032's label-task courier;
- dual-radio LoRa + BLE/Wi-Fi systems, relevant to UC-033 as evidence that scarce/rich bearer separation is a practical architecture pattern, not evidence of our handoff performance;
- offline/on-device and collaborative edge RAG/retrieval, relevant to UC-034's query-to-data model while keeping exact result provenance separate from semantic ranking;
- communication-efficient/verifiable federated edge analytics, relevant to UC-035's simpler deterministic sketch/aggregate experiments;
- storage-integrity auditing and locality-aware distributed repair, relevant to UC-036's proactive scrub/repair model;
- mobile crowdsensing geoprivacy/location masking and LoRa/Wi-Fi environmental monitoring, relevant to UC-037's coarse-zone privacy requirements;
- multi-hop LoRa relay-placement research, useful as a reminder that relay position strongly affects delay, throughput and coverage;
- incremental firmware-update work over LoRa/LoRaWAN, including compact binary deltas and bounded-update architectures;
- blackout/disaster-resilient hybrid mesh work combining scarce and richer local bearers;
- offline replication and CRDT-based emergency-management work under mobile/weak connectivity;
- mobile-edge task offloading research that considers compute placement, cache state, bandwidth and device constraints together;
- bandwidth-aware federated/LoRA adapter exchange for heterogeneous edge devices;
- self-hosted/offline map stacks used where field connectivity cannot be assumed;
- UAV-assisted LoRa collection, where scheduling, geometry and antenna effects must be measured rather than assumed;
- forward erasure correction/network coding for disrupted or delayed-feedback networks, relevant to UC-018 but requiring a PollicinoNet baseline comparison;
- certificate lifecycle/revocation freshness in intermittently reachable infrastructure, relevant to UC-019;
- LoRa/LoRaWAN time synchronization and timestamp compensation research, relevant to the measurement discipline of UC-020 but not evidence of PollicinoNet precision;
- threshold cryptography/secret sharing as a way to separate storage/transport from decryption authority, relevant to UC-021;
- 2026 multi-node IoT/edge-AI systems combining heterogeneous LoRa/BLE communication and multimodal/reliability-aware sensing, relevant to UC-022.

These are design references, not evidence that PollicinoNet has achieved the same physical results.