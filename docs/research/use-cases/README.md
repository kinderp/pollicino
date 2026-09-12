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
| [UC-038](uc-038-edge-model-evaluation-round.md) | Edge Model Evaluation Round | compare exact AI model/runtime performance across intermittently connected devices | pinned benchmark manifest + delayed result round | useful early | Medium–High |
| [UC-039](uc-039-offline-vulnerability-advisory-exposure-census.md) | Offline Vulnerability Advisory and Exposure Census | propagate security knowledge and learn which offline nodes are affected | signed advisory + synthetic software inventories | useful early | Medium–High |
| [UC-040](uc-040-mobility-aware-prefetch-replica-placement.md) | Mobility-Aware Prefetch and Replica Placement | place scarce replicas before likely future requests/contacts | contact-trace replay + placement-policy comparison | useful after UC-008 | High |
| [UC-041](uc-041-pop-up-offline-classroom-hotspot.md) | Pop-Up Offline Classroom Hotspot | expose nearby cached knowledge as a temporary local service without Internet | local HTTP hotspot + simulated LoRa advertisement | useful early | Medium |
| [UC-042](uc-042-physical-asset-chain-of-custody.md) | Physical Asset Chain-of-Custody Courier | preserve signed custody events while real assets move through disconnected groups | append-only custody chain + delayed events | useful early | Medium |
| [UC-043](uc-043-opportunistic-local-exchange-reuse-marketplace.md) | Opportunistic Local Exchange and Reuse Marketplace | match needs/offers for reusable physical goods across disconnected communities | synthetic listings + delayed match/reservation lifecycle | useful early | Medium–High |
| [UC-044](uc-044-offline-git-repository-patch-ferry.md) | Offline Git Repository and Patch Ferry | move exact source-control history without a simultaneously reachable forge | partitioned Git repos + incremental bundle courier | useful early | Medium |
| [UC-045](uc-045-buffer-aware-mobile-data-harvester.md) | Buffer-Aware Mobile Data Harvester | choose what to collect first during short mobile contacts | finite-contact queue-policy comparison | useful after UC-008 | High |
| [UC-046](uc-046-raiatea-answer-capsule-edge-rag.md) | Raiatea Answer Capsule / Offline Edge RAG | return compact source-bound answers without moving corpus/model | public corpus + delayed query/answer/evidence loop | useful early | High |
| [UC-047](uc-047-digital-to-physical-fabrication-job-courier.md) | Digital-to-Physical Fabrication Job Courier | discover/queue a safe fabrication capability and later receive a physical result | virtual machine/job queue + exact artifact manifest | useful early | Medium–High |
| [UC-048](uc-048-offline-verifiable-credential-entitlement-ferry.md) | Offline Verifiable Credential and Entitlement Ferry | verify a narrow entitlement while issuer/verifier are disconnected | synthetic credentials + stale/revoked status tests | useful early | Medium–High |
| [UC-049](uc-049-dynamic-route-condition-access-map.md) | Dynamic Route Condition and Access Map | propagate fresh/conflicting passability state over an offline base map | synthetic route graph + delayed signed observations | useful early | Medium–High |
| [UC-050](uc-050-pseudonymous-lost-found-encounter-trail.md) | Pseudonymous Lost-and-Found Encounter Trail | recover a tagged object without keeping continuous people/object tracks | synthetic rotating-tag encounters + delayed lost query | useful early | Medium |
| [UC-051](uc-051-delay-tolerant-anonymous-classroom-ballot.md) | Delay-Tolerant Anonymous Classroom Survey / Ballot | converge a low-stakes private poll across disconnected groups | synthetic eligibility + encrypted delayed ballots | later | High |
| [UC-052](uc-052-islanded-microgrid-energy-budget-coordination.md) | Islanded Microgrid Energy Budget and Flexible-Load Coordination | coordinate harmless flexible loads under intermittent energy/connectivity | discrete-time energy/load simulator | later | High |

## Current top 3 next experiments for the Messina student network

### 1. UC-008 — Privacy-Preserving Network Observatory

This still comes first because it produces the **real contact traces** needed to make later routing/content simulations less hypothetical. Controlled routes with 3+ boards can reveal contact windows, useful relays and queue opportunities without requiring continuous coverage. The privacy rule is strict: measure encounters, not student lives.

### 2. UC-033 — Secure Rich-Bearer Handoff Bootstrap

This is now the most important protocol-level field experiment after contact measurement because many other use cases already assume `LoRa discovery -> BLE/Wi-Fi/LAN bulk transfer`. Two or three dual-radio endpoints are enough to test exact peer/object binding, short-lived rendezvous material, replay rejection and measured handoff time without changing the LoRa PHY.

### 3. UC-023 — Delay-Tolerant Private Mailbox

This remains the best immediate human-visible service experiment. Four boards are enough to create two disconnected groups plus a moving courier, and success is objectively easy to understand: one encrypted logical message leaves an outbox, survives disconnection/duplication, arrives once and eventually returns a receipt.

### Strong follow-ups

- **UC-049 — Dynamic Route Condition and Access Map:** strongest new emergency/mapping teaching scenario because it adds fresh/conflicting access state on top of UC-017 without pretending the prototype is an authoritative evacuation router.
- **UC-050 — Pseudonymous Lost-and-Found Encounter Trail:** strongest new student-facing DNATrace-style experiment; BLE encounters plus delayed LoRa query/result flow can be demonstrated with a harmless tagged school object and explicit anti-tracking rules.
- **UC-048 — Offline Verifiable Credential and Entitlement Ferry:** strong security primitive for later services because it separates narrow offline authorization from reusable credentials and composes directly with UC-019/020.
- **UC-051 — Delay-Tolerant Anonymous Classroom Survey / Ballot:** compact cryptography/distributed-systems teaching case, deliberately limited to harmless synthetic polls and not election-grade claims.
- **UC-052 — Islanded Microgrid Energy Budget and Flexible-Load Coordination:** useful rural/IoT research direction, but only after a software simulator and then a low-voltage bench; local safety bounds remain non-networked.
- **UC-043 — Opportunistic Local Exchange and Reuse Marketplace:** especially strong September/student-facing scenario; use textbooks first, then repeat with calculators/components to prove the protocol is generic rather than book-specific.
- **UC-044 — Offline Git Repository and Patch Ferry:** highly practical computing-class experiment because Git already provides exact object identity and offline bundles while PollicinoNet contributes delayed discovery/courier behavior.
- **UC-045 — Buffer-Aware Mobile Data Harvester:** focused research follow-up to UC-005/UC-008 that asks what a moving collector should take first when the contact window is too short for the whole backlog.
- **UC-046 — Raiatea Answer Capsule / Offline Edge RAG:** visible AI/document demo that returns a tiny source-bound explanation while preserving exact evidence retrieval and explicit abstention.
- **UC-047 — Digital-to-Physical Fabrication Job Courier:** concrete bridge between capability discovery and a physical output, initially limited to supervised safe school-lab fabrication.
- **UC-040 — Mobility-Aware Prefetch and Replica Placement:** strongest research follow-up to UC-008 because it turns measured student mobility into an explicit cache/replica-placement input and can be compared against simple baselines on the same trace.
- **UC-041 — Pop-Up Offline Classroom Hotspot:** strongest human-visible education demo after UC-033; cached Raiatea/course/reference content becomes a temporary local Wi-Fi service without Internet.
- **UC-039 — Offline Vulnerability Advisory and Exposure Census:** compact security use case that separates `know who is affected` from the larger firmware/package remediation path.
- **UC-038 — Edge Model Evaluation Round:** useful AI-engineering experiment because exact model/runtime/benchmark provenance can converge even when students run tests at different times and places.
- **UC-042 — Physical Asset Chain-of-Custody Courier:** clean physical-world DTN experiment where the asset moves physically while signed custody events converge later.
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
33. implement UC-038 a canonical benchmark round with exact model/runtime/dataset bindings, heterogeneous device profiles, stale-result rejection and delayed result convergence;
34. implement UC-039 signed synthetic advisory revisions, exact software-inventory matching, VEX-like exposure states, forged/stale advisory negative tests and later remediation requests;
35. implement UC-040 several replica-placement policies over identical UC-008 traces, with cache/storage budgets, demand-prediction errors, sensitive-content constraints and wasted-prefetch accounting;
36. implement UC-041 a local HTTP classroom/content service with exact pack identity, simulated LoRa discovery, two competing hotspot versions, short-lived handoff and privacy-safe service logging;
37. implement UC-042 append-only signed custody events, missing/out-of-order handovers, conflicting current-custodian claims and delayed evidence attachment;
38. implement UC-043 generic `ExchangeNeed`/`ExchangeOffer`/`Reservation` state, stale listings, conflicting requesters, expiry, private negotiation and a completed physical-handover receipt;
39. implement UC-044 partitioned Git histories, incremental `git bundle` creation/verification, prerequisite misses, corrupted bundle rejection and explicit divergent branches;
40. implement UC-045 finite-contact queue scheduling with FIFO/expiry/priority/buffer-pressure baselines and resumable partial objects over identical synthetic traces;
41. implement UC-046 a public versioned corpus + local RAG node that returns short answer capsules with exact evidence refs, explicit abstention and stale-version rejection;
42. implement UC-047 a virtual fabrication capability/queue with exact job manifests, duplicate-execution prevention, operator approval, cancellation and physical-pickup state;
43. implement UC-048 synthetic issuer/holder/verifier credentials, offline verification, verifier-bound replay tests, revocation freshness states and minimal-claim presentations;
44. implement UC-049 a synthetic route graph with signed condition observations, TTL/freshness, conflicts, reopening updates, multi-witness corroboration and evidence-by-hash;
45. implement UC-050 rotating synthetic object tags, delayed lost-item queries, privacy-limited match disclosure, replay/fabricated-sighting negative tests and short retention;
46. implement UC-051 a harmless synthetic poll with one-use eligibility tokens, encrypted ballot envelopes, duplicate/late rejection and exact accepted-set convergence;
47. implement UC-052 a discrete-time low-voltage microgrid simulator with battery/production traces, local hard bounds, delayed energy summaries and at least three flexible-load policies;
48. record TRC, delivery delay, cache hit ratio, duplicate overhead, age-of-information, completed-object rate, convergence delay, stale-work rate, trust-epoch propagation, reconstruction success, mailbox delivery/receipt delay, time-to-provider, missed-contact penalty, operation-backlog convergence, dependency bytes avoided, check-in reconciliation delay, calibration-version propagation, label turnaround, handoff setup time, query turnaround, sketch bytes/error, corruption-detection/repair delay, coarse-cell coverage, benchmark-round turnaround, advisory exposure coverage, prefetch hit/waste ratio, hotspot service availability, custody-gap convergence, exchange time-to-match, Git bytes/commit convergence, harvest deadline/drop metrics, answer/evidence bytes, fabrication-job turnaround, credential-status freshness, route-condition convergence, lost-query match delay, accepted-ballot convergence and flexible-load completion as applicable.

This reuses the current architecture instead of creating a special PHY or a separate networking stack per scenario.

## Physical experiments that become necessary

After the simulator contracts are stable:

- repeatable 2-node and 3+ node relay measurements;
- controlled walking/bicycle data-mule passes;
- privacy-safe contact-window collection for UC-008;
- a UC-033 2–3 provider experiment with real LoRa discovery, multiple visible nearby peers, exact peer/object binding and measured BLE/Wi-Fi/LAN handoff time;
- a UC-023 four-node mailbox test with two disconnected groups, one moving courier and a delayed receipt;
- a UC-043 4–6 node exchange experiment with synthetic/opt-in textbook or calculator listings, delayed matching, reservation conflict, UC-033 detail handoff and a controlled school pickup;
- a UC-044 3–4 laptop coding experiment with partitioned Git histories, LoRa ref discovery, an incremental bundle carried over a rich bearer and explicit merge/divergence handling;
- a UC-045 3–5 fixed-node + walking/bicycle collector experiment where contacts are deliberately too short for all backlog, comparing at least two queue policies on the same route;
- a UC-046 3-node requester/relay/local-RAG experiment using a public teaching corpus, compact query/answer metadata and later exact evidence retrieval over UC-033;
- a UC-047 supervised paper/3D-print job with real capability/status exchange, rich-bearer file submission, operator approval and physical pickup;
- a UC-048 3–4 node synthetic credential drill with a disconnected verifier, relay-carried trust/status update, local BLE/NFC/Wi-Fi presentation and replay/revocation negative cases;
- a UC-049 4+ node campus/corridor access-map drill with synthetic closures/reopenings, moving relays, conflicting observations and optional later photo retrieval;
- a UC-050 4–6 node lost-and-found drill with a harmless tagged school object, rotating BLE IDs, delayed lost-item query and measured query-to-match behavior;
- a UC-051 5+ node harmless classroom poll split across two disconnected groups, one moving courier, duplicate/late ballots and final accepted-set convergence;
- a UC-052 low-voltage DC bench experiment only after simulation, using harmless LEDs/fans/USB loads, 3–5 LoRa nodes and scripted energy/load profiles; never mains or safety-critical loads;
- a UC-024 4+ node cache/request experiment where the requester cannot directly contact the content holder and the final object moves over a richer bearer;
- a UC-034 3+ node query-to-data experiment with one unreachable corpus/search node, one moving relay and later exact selected-document retrieval over UC-033;
- a UC-035 4–6 node aggregate experiment comparing raw-event forwarding with a mergeable summary under the same controlled workload;
- a UC-036 3+ storage-node experiment with disposable test data, deliberate corruption/deletion and measured detection-to-repair through a later peer contact;
- a UC-037 3–6 sensor-node controlled-route experiment using coarse public test zones, calibration/reference checks and explicit geoprivacy validation;
- a UC-038 2+ heterogeneous compute-node benchmark round with exact model/runtime pins, repeated real measurements and LoRa-carried round/result metadata;
- a UC-039 4+ node advisory-partition drill using harmless synthetic package versions, delayed exposure reports and one later rich-bearer remediation;
- a UC-040 4–6 node bounded-cache experiment comparing at least two replica-placement policies on the same measured UC-008 contact traces;
- a UC-041 1–2 hotspot/cache nodes plus 3+ client devices with real LoRa service discovery, UC-033 handoff and offline HTTP content access;
- a UC-042 3–5 node physical handover chain using harmless tagged equipment, delayed custody events and explicit conflict/gap detection;
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

- W3C Verifiable Credentials 2.0, JOSE/COSE and compact credential status mechanisms, relevant to UC-048 while keeping the first profile synthetic and much smaller than a full identity ecosystem;
- 2026 humanitarian/open-mapping activations that emphasize damaged roads/infrastructure and changing access conditions, relevant to UC-049 without making PollicinoNet an authoritative emergency map;
- opportunistic BLE crowds/phone readers used by modern asset-tracking systems, relevant to UC-050 while PollicinoNet deliberately minimizes trajectory and identity retention;
- privacy-preserving/verifiable voting systems using anonymous eligibility and threshold cryptography, relevant to UC-051 as research signal only, not election-grade validation;
- 2026 LPWAN/LoRaMESH energy-management and demand-response research, relevant to UC-052 while restricting PollicinoNet experiments to simulation and low-voltage harmless loads;
- community reuse/circular-economy platforms and reuse organisations as social infrastructure, relevant to UC-043 while keeping payments and unsafe goods outside the initial protocol;
- Git's official offline bundle mechanism and local-first/P2P Git systems such as Radicle, relevant to UC-044 without replacing Git's object/merge semantics;
- buffer-aware/signal-aware mobile data harvesting and Flying DTN forwarding, relevant to UC-045 but requiring PollicinoNet's own measured contact traces;
- offline/local RAG systems with source-cited compact response modes, relevant to UC-046 while keeping semantic answers non-authoritative and evidence exact;
- local fabrication job APIs and LAN queues such as OctoPrint/Continuous Print, relevant to UC-047 as adapters while PollicinoNet supplies delayed discovery/control;
- repeatable local/edge LLM benchmarking with pinned model/runtime/hardware provenance, relevant to UC-038 without treating another project's measurements as ours;
- CSAF/VEX machine-readable vulnerability advisories and SBOM-linked exposure status, relevant to UC-039's compact advisory/control plane;
- proactive caching and mobility/contact-aware content placement, relevant to UC-040 only after UC-008 gives us real local traces and suitable baselines;
- offline-first education/content hotspots such as Kolibri and Kiwix, relevant to UC-041's local-service activation model without making PollicinoNet a learning platform itself;
- event-based physical asset traceability/chain-of-custody standards such as GS1 EPCIS, relevant to UC-042 while keeping PollicinoNet's transport/event contracts smaller and delay-tolerant;
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