# PollicinoNet use-case catalog addendum — 2026-10-07

This cumulative addendum indexes use cases added after UC-147. Core constraints remain unchanged: frozen LoRa PHY, compact control over LoRa, bulk over richer bearers or physical transport, and no physical-performance claims without measurements.

| ID | Use case | Short purpose |
|---|---|---|
| UC-148 | Offline Federated Unlearning | delayed contribution withdrawal |
| UC-149 | Raiatea Source-Status Reassessment | reassess answers when evidence changes |
| UC-150 | Distributed Visual Survey Mosaic | repair survey coverage gaps |
| UC-151 | Physical-Storage Bundle Session | managed physical bulk bearer |
| UC-152 | Privacy-Aware Set Reconciliation | find cache differences compactly |
| UC-153 | AoI-Aware Sensor Update | prioritize useful fresh state |
| UC-154 | Uncertainty-Gated AI Escalation | escalate only uncertain cases |
| UC-155 | Raiatea Vector-Index Merge | consolidate compatible shards |
| UC-156 | Offline Secure Group Rekey | converge group membership epochs |
| UC-157 | Intermittent Knowledge Distillation | ferry teacher guidance |
| UC-158 | Slope-Instability Evidence Courier | carry compact sensor trends |
| UC-159 | Priority Preemption + Resume | interrupt bulk without losing progress |
| UC-160 | AI Model Canary Rollout | staged promote/pause/rollback |
| UC-161 | Modality-Aware Federated Update | bind updates to sensor modalities |
| UC-162 | Selective Restore Closure | restore only needed dependencies |
| [UC-163](uc-163-failure-domain-aware-replica-placement-correlated-loss-repair-courier.md) | Failure-Domain-Aware Replica Placement | spread replicas across coarse operational domains |
| [UC-164](uc-164-intermittent-split-inference-activation-courier.md) | Intermittent Split-Inference Activation Courier | ferry intermediate AI activations between compute tiers |
| [UC-165](uc-165-prepositioned-sealed-release-package-courier.md) | Prepositioned Sealed-Release Package Courier | stage encrypted bulk early and release later with compact authorization |
| [UC-166](uc-166-opportunistic-colocation-sensor-cross-calibration-courier.md) | Opportunistic Co-Location Sensor Cross-Calibration | create calibration evidence during brief reference co-location |
| [UC-167](uc-167-one-way-no-return-path-bundle-drop-courier.md) | One-Way / No-Return-Path Bundle Drop Courier | exploit outbound-only contacts and return receipts later |
| [UC-168](uc-168-explicit-custody-commitment-responsibility-handoff-courier.md) | Explicit Custody Commitment and Responsibility-Handoff Courier | transfer bounded storage/retry responsibility between holders |
| [UC-169](uc-169-privacy-bounded-encounter-probability-routing-courier.md) | Privacy-Bounded Encounter-Probability Routing | decentralized forwarding from coarse encounter history |
| [UC-170](uc-170-offline-security-algorithm-migration-courier.md) | Offline Security-Algorithm Migration | staged security-profile migration across mixed offline devices |
| [UC-171](uc-171-coastal-water-quality-cross-validation-courier.md) | Coastal Water-Quality Cross-Validation | reconcile field sensing with delayed reference evidence |
| [UC-172](uc-172-event-log-snapshot-compaction-courier.md) | Event-Log Snapshot and Compaction | bound long offline histories with snapshot plus tail |
| [UC-173](uc-173-privacy-bounded-temporal-reachability-contact-path-query.md) | Privacy-Bounded Temporal Reachability and Contact-Path Query | answer bounded post-hoc path questions without centralizing full encounter logs |
| [UC-174](uc-174-application-layer-energy-aware-rendezvous-window-courier.md) | Application-Layer Energy-Aware Rendezvous Window Courier | expose coarse service windows to trade availability against measured energy |
| [UC-175](uc-175-idempotent-side-effect-command-duplicate-suppression-courier.md) | Idempotent Side-Effect Command and Duplicate-Suppression Courier | make retries and multi-path duplicates safe for bounded actions |
| [UC-176](uc-176-event-triggered-cooperative-burst-capture-courier.md) | Event-Triggered Cooperative Burst-Capture Courier | trigger short multi-sensor high-rate evidence capture only when needed |
| [UC-177](uc-177-delay-tolerant-differential-privacy-budget-query-admission-courier.md) | Delay-Tolerant Differential-Privacy Budget and Query-Admission Courier | prevent conflicting privacy-budget admission while analytics authorities are partitioned |

## Priority from the 2026-10-07 batch
1. **UC-173** — strongest network-observatory/DNATrace experiment: query temporal reachability while keeping raw encounter histories local.
2. **UC-175** — strongest robot/IoT reliability case: retries and multi-path delivery become safe for side-effecting commands through explicit idempotency state.
3. **UC-176** — strongest physical sensing experiment: a small trigger activates bounded cooperative burst capture, while rich evidence is ferried later.

UC-174 is the strongest energy/rendezvous case but requires real energy instrumentation before any saving claim. UC-177 is the strongest new privacy-research case and should begin with synthetic/public data only.

## Physical-validation reminder
No entry changes the frozen LoRa PHY. Range, PDR, RSSI/SNR interpretation, throughput, contact duration, energy, application reliability, capture alignment and sensing quality remain real-hardware measurement questions.
