# PollicinoNet use-case catalog

Current compact index of the concrete PollicinoNet use cases. The detailed per-use-case files are authoritative for scenario, privacy/security and validation constraints.

Core rules remain unchanged:

- do not modify the frozen LoRa PHY as part of use-case work;
- keep `DISCOVERY`, `EXACT` and `SEMANTIC` as information contracts, not radio technologies;
- prefer LoRa for compact discovery/control and richer bearers for bulk data;
- do not claim physical range, reliability, airtime, energy or coverage results without real measurements;
- treat emergency/safety scenarios as controlled experiments until independently validated;
- protect identity, location, content metadata and authorization at the application layer.

Last synchronized: **2026-09-26**.

| ID | Use case | Short purpose |
|---|---|---|
| [UC-001](uc-001-student-knowledge-ferry.md) | Student Knowledge Ferry | move knowledge between disconnected school/home/town islands |
| [UC-002](uc-002-signed-community-bulletin.md) | Signed Community Bulletin / civil-protection drill | resilient small authoritative messages |
| [UC-003](uc-003-rural-sensor-courier.md) | Rural Sensor Courier | collect sensor data without permanent backhaul |
| [UC-004](uc-004-offline-ai-artifact-distribution.md) | Offline AI Artifact Distribution | move models/datasets across intermittent links |
| [UC-005](uc-005-mobile-gateway-uav-vehicle.md) | Mobile Gateway / UAV / vehicle | use moving nodes when fixed nodes have no end-to-end path |
| [UC-006](uc-006-raiatea-document-capsules.md) | Raiatea Document Capsules | exact versioned document distribution |
| [UC-007](uc-007-edge-ai-event-scout.md) | Edge AI Event Scout | send interesting events rather than raw streams |
| [UC-008](uc-008-network-observatory-contact-graph.md) | Privacy-Preserving Network Observatory | learn real contact opportunities and relay value |
| [UC-009](uc-009-signed-firmware-config-ferry.md) | Signed Firmware and Configuration Ferry | maintain isolated sensors/robots safely |
| [UC-010](uc-010-robot-mission-mailbox.md) | Robot Mission Mailbox | asynchronous jobs for intermittently connected robots |
| [UC-011](uc-011-dnatrace-encounter-capsules.md) | DNATrace Encounter Capsules | pseudonymous offline discovery with later consent |
| [UC-012](uc-012-opportunistic-backup-restore.md) | Opportunistic Backup and Restore | exact P2P recovery across intermittent nodes |
| [UC-013](uc-013-field-report-evidence-capsules.md) | Field Report and Evidence Capsules | return signed observations/evidence from disconnected teams |
| [UC-014](uc-014-opportunistic-capability-compute-exchange.md) | Opportunistic Capability and Compute Exchange | discover/use compute, storage and connectivity across partitions |
| [UC-015](uc-015-partition-tolerant-resource-ledger.md) | Partition-Tolerant Resource Ledger | reconcile inventory, requests and reservations offline |
| [UC-016](uc-016-federated-adapter-round-courier.md) | Federated Adapter Round Courier | coordinate AI updates across intermittent clients |
| [UC-017](uc-017-offline-map-tile-ferry.md) | Offline Map and Route Tile Ferry | keep useful map subsets available without Internet |
| [UC-018](uc-018-erasure-coded-content-swarm.md) | Erasure-Coded Content Swarm | reconstruct content from partial carriers |
| [UC-019](uc-019-offline-trust-revocation-ferry.md) | Offline Trust Epoch and Revocation Ferry | propagate revocation/key-rotation state |
| [UC-020](uc-020-trusted-time-checkpoint-ferry.md) | Trusted Time Checkpoint Ferry | carry freshness/expiry evidence without permanent time service |
| [UC-021](uc-021-threshold-sealed-sensitive-courier.md) | Threshold-Sealed Sensitive Courier | transport sensitive content without giving carriers plaintext authority |
| [UC-022](uc-022-multi-witness-event-corroboration.md) | Multi-Witness Event Corroboration | corroborate noisy sensor/edge claims |
| [UC-023](uc-023-delay-tolerant-private-mailbox.md) | Delay-Tolerant Private Mailbox | private asynchronous messaging across disconnected groups |
| [UC-024](uc-024-content-need-rendezvous.md) | Content-Need Rendezvous / Interest Ferry | request content without knowing its current holder |
| [UC-025](uc-025-scheduled-mobility-backbone.md) | Scheduled Mobility Backbone | exploit recurring contact opportunities |
| [UC-026](uc-026-delegated-offline-action-ticket.md) | Delegated Offline Action Ticket | authorize one narrow offline action |
| [UC-027](uc-027-post-event-vibration-log-courier.md) | Post-Event Vibration / Structural Log Courier | announce events now and retrieve high-rate evidence later |
| [UC-028](uc-028-offline-collaborative-notebook.md) | Offline Collaborative Notebook | converge concurrent human edits after partitions |
| [UC-029](uc-029-opportunistic-software-dependency-cache.md) | Opportunistic Software Dependency Cache | reconstruct dev environments from nearby caches |
| [UC-030](uc-030-privacy-preserving-muster-checkin.md) | Privacy-Preserving Muster / Safety Check-In | delayed checkpoint presence without continuous tracking |
| [UC-031](uc-031-sensor-calibration-provenance-ferry.md) | Sensor Calibration and Provenance Ferry | keep calibration/evidence bound to sensor measurements |
| [UC-032](uc-032-active-learning-label-courier.md) | Active-Learning Label Courier | spend annotation/network effort on informative samples |
| [UC-033](uc-033-secure-rich-bearer-handoff-bootstrap.md) | Secure Rich-Bearer Handoff Bootstrap | securely switch from LoRa discovery to BLE/Wi-Fi/LAN transfer |
| [UC-034](uc-034-raiatea-query-to-data-search-courier.md) | Raiatea Query-to-Data Search Courier | move queries to corpora instead of moving whole corpora |
| [UC-035](uc-035-federated-sketch-aggregate-courier.md) | Federated Sketch / Aggregate Courier | compute useful aggregates without forwarding every raw record |
| [UC-036](uc-036-proactive-integrity-scrub-repair-swarm.md) | Proactive Integrity Scrub and Repair Swarm | find and repair latent corruption before restore time |
| [UC-037](uc-037-privacy-safe-mobile-environmental-transect.md) | Privacy-Safe Mobile Environmental Transect | gain coarse spatial sensor coverage without retaining trajectories |
| [UC-038](uc-038-edge-model-evaluation-round.md) | Edge Model Evaluation Round | compare exact model/runtime behavior across intermittent devices |
| [UC-039](uc-039-offline-vulnerability-advisory-exposure-census.md) | Offline Vulnerability Advisory and Exposure Census | propagate advisories and learn which offline nodes are affected |
| [UC-040](uc-040-mobility-aware-prefetch-replica-placement.md) | Mobility-Aware Prefetch and Replica Placement | place replicas before likely future demand/contacts |
| [UC-041](uc-041-pop-up-offline-classroom-hotspot.md) | Pop-Up Offline Classroom Hotspot | expose nearby cached knowledge as a temporary local service |
| [UC-042](uc-042-physical-asset-chain-of-custody.md) | Physical Asset Chain-of-Custody Courier | preserve signed custody events while assets move physically |
| [UC-043](uc-043-opportunistic-local-exchange-reuse-marketplace.md) | Opportunistic Local Exchange and Reuse Marketplace | match needs/offers for reusable physical goods |
| [UC-044](uc-044-offline-git-repository-patch-ferry.md) | Offline Git Repository and Patch Ferry | move exact source-control history without a live forge |
| [UC-045](uc-045-buffer-aware-mobile-data-harvester.md) | Buffer-Aware Mobile Data Harvester | choose what to collect first during short contacts |
| [UC-046](uc-046-raiatea-answer-capsule-edge-rag.md) | Raiatea Answer Capsule / Offline Edge RAG | return compact source-bound answers with exact evidence refs |
| [UC-047](uc-047-digital-to-physical-fabrication-job-courier.md) | Digital-to-Physical Fabrication Job Courier | discover/queue safe fabrication and later receive physical output |
| [UC-048](uc-048-offline-verifiable-credential-entitlement-ferry.md) | Offline Verifiable Credential and Entitlement Ferry | verify narrow entitlements while disconnected |
| [UC-049](uc-049-dynamic-route-condition-access-map.md) | Dynamic Route Condition and Access Map | propagate fresh/conflicting passability state |
| [UC-050](uc-050-pseudonymous-lost-found-encounter-trail.md) | Pseudonymous Lost-and-Found Encounter Trail | recover tagged objects without continuous tracking |
| [UC-051](uc-051-delay-tolerant-anonymous-classroom-ballot.md) | Delay-Tolerant Anonymous Classroom Survey / Ballot | converge a low-stakes private poll across partitions |
| [UC-052](uc-052-islanded-microgrid-energy-budget-coordination.md) | Islanded Microgrid Energy Budget and Flexible-Load Coordination | coordinate harmless flexible loads under intermittent energy/connectivity |
| [UC-053](uc-053-delay-tolerant-sensor-tasking-sampling-campaign.md) | Delay-Tolerant Sensor Tasking and Sampling Campaign | send bounded observation requests to disconnected sensors |
| [UC-054](uc-054-offline-assignment-submission-feedback-courier.md) | Offline Assignment Submission and Feedback Courier | preserve submission/receipt/feedback state across partitions |
| [UC-055](uc-055-opportunistic-transit-disruption-arrival-relay.md) | Opportunistic Transit Disruption and Arrival Relay | propagate fresh transit status without continuous connectivity |
| [UC-056](uc-056-consent-bound-data-donation-dataset-provenance.md) | Consent-Bound Data Donation and Dataset Provenance Courier | keep consent/purpose/provenance attached to delayed contributions |
| [UC-057](uc-057-model-to-data-edge-inference-courier.md) | Model-to-Data Edge Inference Courier | move approved analysis toward private/local data |
| [UC-058](uc-058-floating-local-service-state-handoff.md) | Floating Local Service and State Handoff | migrate a small local service and exact state between hosts |
| [UC-059](uc-059-mutual-aid-skill-service-rendezvous.md) | Mutual-Aid Skill and Service Rendezvous | match human skills/help needs without a permanent directory |
| [UC-060](uc-060-visual-survey-imagery-evidence-ferry.md) | Visual Survey and Imagery Evidence Ferry | announce visual evidence now and retrieve large imagery later |
| [UC-061](uc-061-named-computation-result-cache.md) | Named Computation and Result Cache | reuse exact deterministic results across sparse edge nodes |
| [UC-062](uc-062-offline-diagnostics-crash-capsule.md) | Offline Diagnostics and Crash Capsule | debug distributed nodes without continuous telemetry |
| [UC-063](uc-063-spectrum-occupancy-interference-survey-ferry.md) | Spectrum Occupancy and Interference Survey Ferry | collect delay-tolerant RF-environment observations separate from contact traces |
| [UC-064](uc-064-offline-transparency-gossip-equivocation-detection.md) | Offline Transparency Gossip and Equivocation Detection | detect inconsistent signed histories through delayed checkpoint gossip |
| [UC-065](uc-065-federated-multi-corpus-search-rank-merge-courier.md) | Federated Multi-Corpus Search and Rank-Merge Courier | query multiple disconnected corpora and merge provenance-preserving results |
| [UC-066](uc-066-pseudonymous-separated-group-reunification-drill.md) | Pseudonymous Separated-Group Reunification Drill | reconcile synthetic separated-group status with strict privacy |
| [UC-067](uc-067-signed-offline-service-name-directory-ferry.md) | Signed Offline Service Name Directory Ferry | map stable service names to exact authenticated identities while disconnected |
| [UC-068](uc-068-offline-device-enrollment-identity-bootstrap.md) | Offline Device Enrollment and Identity Bootstrap | securely introduce/reset student boards without a live registrar path |
| [UC-069](uc-069-staged-firmware-rollout-health-evidence-ferry.md) | Staged Firmware Rollout and Health-Evidence Ferry | phase updates, collect health evidence and propagate pause/abort state |
| [UC-070](uc-070-physical-energy-mule-charging-rendezvous.md) | Physical Energy Mule and Charging Rendezvous | coordinate safe low-voltage energy delivery by human/vehicle carriers |
| [UC-071](uc-071-multi-party-quorum-approval-courier.md) | Multi-Party Quorum Approval Courier | collect M-of-N or ordered approvals for one exact offline action |
| [UC-072](uc-072-edge-model-drift-distribution-shift-scout.md) | Edge Model Drift and Distribution-Shift Scout | ferry compact drift warnings before requesting raw evidence |
| [UC-073](uc-073-demand-aware-mobile-courier-route-planner.md) | Demand-Aware Mobile Courier Route Planner | choose the next useful checkpoint from current needs, backlog and expected contacts |
| [UC-074](uc-074-adaptive-sensor-duty-cycle-sampling-policy-ferry.md) | Adaptive Sensor Duty-Cycle and Sampling Policy Ferry | adapt safe sensing profiles as energy, backlog and signal dynamics change |
| [UC-075](uc-075-offline-multi-robot-task-auction-mission-handoff.md) | Offline Multi-Robot Task Auction and Mission Handoff | allocate tasks among intermittent workers and re-auction failed assignments |
| [UC-076](uc-076-artifact-usage-policy-license-envelope-ferry.md) | Artifact Usage-Policy and License Envelope Ferry | bind exact cached artifacts to versioned usage-policy decisions |
| [UC-077](uc-077-deletion-tombstone-retention-expiry-ferry.md) | Deletion Tombstone and Retention-Expiry Ferry | propagate deletion/expiry so stale replicas cannot resurrect old content |
| [UC-078](uc-078-deadline-aware-opportunistic-edge-task-offloading.md) | Deadline-Aware Opportunistic Edge Task Offloading | choose local execution versus delayed edge offload under deadline/contact uncertainty |
| [UC-079](uc-079-intermittent-computation-checkpoint-resume-courier.md) | Intermittent Computation Checkpoint and Resume Courier | preserve in-progress compute across reboot, power loss and delayed migration |
| [UC-080](uc-080-condition-bound-physical-asset-history-courier.md) | Condition-Bound Physical Asset History Courier | keep temperature/humidity/shock evidence attached to a moving asset across partitions |
| [UC-081](uc-081-offline-distributed-ci-test-farm-courier.md) | Offline Distributed CI / Test Farm Courier | run exact commit/test jobs on intermittently connected heterogeneous workers |
| [UC-082](uc-082-threshold-guardian-offline-identity-recovery.md) | Threshold Guardian Offline Identity Recovery | recover a lost device identity through delayed M-of-N guardian approvals and explicit old-key revocation |
| [UC-083](uc-083-delay-tolerant-topic-subscription-change-notification-ferry.md) | Delay-Tolerant Topic Subscription and Change-Notification Ferry | deliver future topic updates across partitions without a permanent broker |
| [UC-084](uc-084-multi-robot-map-fragment-pose-graph-ferry.md) | Multi-Robot Map Fragment and Pose-Graph Ferry | discover and selectively exchange exact mapping fragments across intermittent robot contacts |
| [UC-085](uc-085-compatible-ai-model-variant-negotiation-distribution.md) | Compatible AI Model Variant Negotiation and Distribution | resolve a capability request to one exact runnable model variant under device/policy constraints |
| [UC-086](uc-086-delay-tolerant-multi-sensor-event-localization.md) | Delay-Tolerant Multi-Sensor Event Localization | combine delayed sensor observations to estimate a coarse event origin with explicit uncertainty |
| [UC-087](uc-087-offline-device-attestation-evidence-ferry.md) | Offline Device Attestation Evidence Ferry | carry measured-state evidence/results between attesters, verifiers and relying parties while disconnected |
| [UC-088](uc-088-delay-tolerant-web-api-fetch-courier.md) | Delay-Tolerant Web / API Fetch Courier | let an offline node request one bounded public Internet resource through a later gateway contact |
| [UC-089](uc-089-stateful-alarm-acknowledgement-escalation-courier.md) | Stateful Alarm Acknowledgement and Escalation Courier | preserve exact alarm/ack/clear/escalation state across partitions |
| [UC-090](uc-090-privacy-preserving-after-the-fact-witness-discovery.md) | Privacy-Preserving After-the-Fact Witness Discovery | move a bounded post-event query to private local histories and return only opt-in matches |
| [UC-091](uc-091-backup-retrievability-audit-challenge-courier.md) | Backup Retrievability Audit Challenge Courier | audit exact remote backup replicas with delayed compact challenge/response evidence |
| [UC-092](uc-092-opportunistic-internet-reachability-backhaul-observatory.md) | Opportunistic Internet Reachability and Backhaul Observatory | measure Internet/partial reachability from many intermittent vantage points and ferry summaries independently |
| [UC-093](uc-093-causal-event-timeline-reconstruction-ferry.md) | Causal Event Timeline Reconstruction Ferry | reconstruct happened-before/concurrent relationships from delayed distributed event fragments |
| [UC-094](uc-094-historical-sensor-query-to-data-courier.md) | Historical Sensor Query-to-Data Courier | move bounded historical queries to sensor archives instead of centralizing raw time series |
| [UC-095](uc-095-volunteer-relay-budget-fair-share-courier.md) | Volunteer Relay Budget and Fair-Share Courier | honor volunteer storage/energy/privacy budgets while preventing persistent flow starvation |
| [UC-096](uc-096-independent-reproducible-build-attestation-courier.md) | Independent Reproducible Build Attestation Courier | compare independently rebuilt exact artifacts through delayed provenance/digest evidence |
| [UC-097](uc-097-distributed-experiment-campaign-evidence-pack-courier.md) | Distributed Experiment Campaign and Evidence-Pack Courier | coordinate exact physical experiments and preserve result/evidence provenance across disconnected nodes |
| [UC-098](uc-098-delivery-provenance-relay-contribution-receipts.md) | Delivery Provenance and Relay-Contribution Receipts | record bounded bundle-progress evidence and actual relay contribution without turning it into student tracking |
| [UC-099](uc-099-raiatea-offline-document-ingestion-derived-artifact-courier.md) | Raiatea Offline Document Ingestion and Derived-Artifact Courier | derive OCR/chunks/embeddings/index artifacts across intermittent workers with exact source lineage |
| [UC-100](uc-100-privacy-preserving-demand-sketch-cache-rebalancing.md) | Privacy-Preserving Demand Sketch and Cache Rebalancing | exchange compact demand summaries to improve replica/eviction choices without central request histories |
| [UC-101](uc-101-distributed-ai-disagreement-scout-adjudication-courier.md) | Distributed AI Disagreement Scout and Adjudication Courier | use compact multi-model disagreement to select which samples need richer evidence or review |
| [UC-102](uc-102-opportunistic-groupcast-coverage-anti-entropy-campaign.md) | Opportunistic Groupcast Coverage and Anti-Entropy Campaign | spread one exact signed object to many intermittent nodes with bounded duplicates and explicit coverage evidence |
| [UC-103](uc-103-adaptive-temporary-relay-placement-coverage-gap-trial-planner.md) | Adaptive Temporary Relay Placement and Coverage-Gap Trial Planner | rank safe temporary relay checkpoints from measured evidence, then validate them physically |
| [UC-104](uc-104-exact-version-delta-artifact-ferry.md) | Exact Version-Delta Artifact Ferry | move a verified delta when the receiver already has the exact base artifact |
| [UC-105](uc-105-offline-threat-indicator-match-incident-triage-courier.md) | Offline Threat-Indicator Match and Incident-Triage Courier | send defensive indicators to local logs and return bounded triage before richer evidence |
| [UC-106](uc-106-signed-multilingual-emergency-bulletin-derivation-ferry.md) | Signed Multilingual Emergency Bulletin Derivation Ferry | preserve one authoritative bulletin while ferrying provenance-bound translations and accessible derivatives |
| [UC-107](uc-107-freshness-aware-offline-cache-revalidation-ferry.md) | Freshness-Aware Offline Cache Revalidation Ferry | make stale/fresh/unknown cache state explicit and revalidate compactly before retransferring content |
| [UC-108](uc-108-queue-pressure-backpressure-admission-control-courier.md) | Queue-Pressure Backpressure and Admission-Control Courier | propagate coarse downstream pressure so upstream nodes can defer, refuse or reroute before buffers overflow |
| [UC-109](uc-109-durability-aware-replica-retirement-safe-cache-gc.md) | Durability-Aware Replica Retirement and Safe Cache GC | reclaim cache space without silently retiring the last useful valid replicas or shard set |
| [UC-110](uc-110-near-duplicate-visual-evidence-dataset-representative-ferry.md) | Near-Duplicate Visual Evidence and Dataset Representative Ferry | exchange compact similarity evidence so large media/dataset transfers can prioritize representatives without losing exact provenance |
| [UC-111](uc-111-privacy-gated-local-redaction-egress-courier.md) | Privacy-Gated Local Redaction and Egress Courier | create a policy-bound reduced-disclosure derivative locally before data reaches Internet/cloud gateways |
| [UC-112](uc-112-cross-contact-resumable-large-object-transfer.md) | Cross-Contact Resumable Large-Object Transfer | persist verified partial progress so one exact object can complete across repeated interrupted rich-bearer encounters |
| [UC-113](uc-113-sensor-maintenance-ticket-repair-evidence-courier.md) | Sensor Maintenance Ticket and Repair-Evidence Courier | carry fault tickets to maintainers and return exact repair/inspection state across intermittent links |
| [UC-114](uc-114-privacy-preserving-dataset-overlap-contamination-audit.md) | Privacy-Preserving Dataset Overlap and Contamination Audit | compare distributed train/eval/benchmark corpora with compact fingerprints before revealing full data |
| [UC-115](uc-115-raiatea-schema-ontology-mapping-courier.md) | Raiatea Schema and Ontology Mapping Courier | exchange versioned mappings so disconnected corpora can interpret equivalent metadata consistently |
| [UC-116](uc-116-citizen-science-observation-verification-courier.md) | Citizen-Science Observation Verification Courier | ferry compact field claims first and request rich evidence only for uncertain or interesting observations |
| [UC-117](uc-117-offline-data-quality-rule-validation-report-ferry.md) | Offline Data-Quality Rule and Validation-Report Ferry | move exact validation rules to local data and return compact quality evidence instead of centralizing raw records |
| [UC-118](uc-118-delay-tolerant-digital-twin-state-reconciliation.md) | Delay-Tolerant Digital Twin State Reconciliation | keep physical-device state useful under partitions by making version, freshness and uncertainty explicit |
| [UC-119](uc-119-offline-media-provenance-content-credentials-courier.md) | Offline Media Provenance / Content Credentials Courier | carry verifiable provenance/derivation metadata separately from large media assets |
| [UC-120](uc-120-derived-artifact-invalidation-recompute-courier.md) | Derived-Artifact Invalidation and Recompute Courier | propagate dependency-aware stale state so Raiatea/AI derivatives are recomputed from exact current inputs |
| [UC-121](uc-121-offline-structured-form-case-file-reconciliation.md) | Offline Structured Form and Case-File Reconciliation Courier | merge concurrent field-level offline records while preserving explicit conflicts and provenance |
| [UC-122](uc-122-offline-collaborative-geospatial-feature-editing.md) | Offline Collaborative Geospatial Feature Editing and Conflict Merge | reconcile concurrent vector-map edits without losing geometry validity, provenance or unresolved conflicts |

## Current field priority

The first three physical experiments remain:

1. **UC-008 — Privacy-Preserving Network Observatory:** collect real contact opportunities before tuning routing around imagined mobility.
2. **UC-033 — Secure Rich-Bearer Handoff Bootstrap:** validate the recurring `LoRa discovery/control -> BLE/Wi-Fi/LAN bulk` transition.
3. **UC-023 — Delay-Tolerant Private Mailbox:** demonstrate a complete human-visible store-and-forward service.

Strong additions from UC-118–122:

- **UC-118 — Delay-Tolerant Digital Twin State Reconciliation:** strongest new physical IoT/robotics bridge because the student mesh can carry compact state versions while the twin exposes age and uncertainty instead of pretending stale state is current.
- **UC-120 — Derived-Artifact Invalidation and Recompute Courier:** strongest Raiatea/AI correctness addition because source changes can mark dependent OCR/chunks/embeddings/index artifacts stale before bulky replacements arrive.
- **UC-119 — Offline Media Provenance / Content Credentials Courier:** strongest evidence/media addition because cryptographic provenance can travel separately from photos/audio/video and remain distinct from heuristic AI detection.
- **UC-122 — Offline Collaborative Geospatial Feature Editing and Conflict Merge:** strong emergency/map teaching case because groups can edit synthetic vector features while disconnected and reconcile them through student relays.
- **UC-121 — Offline Structured Form and Case-File Reconciliation Courier:** strong offline-first operations case because field-level conflicts can be surfaced instead of silently discarded by last-write-wins.