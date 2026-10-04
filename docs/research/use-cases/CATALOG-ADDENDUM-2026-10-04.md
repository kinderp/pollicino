# PollicinoNet use-case catalog addendum — 2026-10-04

This cumulative addendum indexes the use cases added after UC-147 on the documentation branch. Core constraints remain unchanged: the LoRa PHY is frozen; LoRa is primarily a compact discovery/control bearer; bulk data belongs on richer bearers or physical transport; physical performance claims require real measurements.

| ID | Use case | Short purpose |
|---|---|---|
| [UC-148](uc-148-offline-federated-unlearning-contribution-withdrawal-courier.md) | Offline Federated Unlearning and Contribution-Withdrawal Courier | carry delayed contribution-withdrawal requests and preserve exact model-lineage action state |
| [UC-149](uc-149-raiatea-source-status-answer-reassessment-courier.md) | Raiatea Source-Status and Answer-Reassessment Courier | reassess cached answers when previously used evidence later changes status |
| [UC-150](uc-150-distributed-visual-survey-mosaic-courier.md) | Distributed Visual Survey Mosaic Courier | advertise survey coverage compactly and retrieve imagery needed to repair mosaic gaps |
| [UC-151](uc-151-physical-storage-bundle-session.md) | Physical-Storage Bundle Session | use school-managed physical storage as a documented delayed bulk bearer |
| [UC-152](uc-152-privacy-aware-cache-inventory-set-reconciliation-courier.md) | Privacy-Aware Cache Inventory and Set-Reconciliation Courier | discover differences between large cache inventories before requesting missing content |
| [UC-153](uc-153-goal-oriented-freshness-aoi-sensor-update-courier.md) | Goal-Oriented Freshness / AoI-Aware Sensor Update Courier | prioritize updates by destination freshness and task value rather than forwarding every stale sample |
| [UC-154](uc-154-uncertainty-gated-edge-ai-escalation-expert-return-courier.md) | Uncertainty-Gated Edge AI Escalation and Expert-Return Courier | let a local model abstain and asynchronously escalate only uncertain cases |
| [UC-155](uc-155-raiatea-vector-index-shard-merge-compaction-courier.md) | Raiatea Vector-Index Shard Merge and Compaction Courier | consolidate compatible independently-built vector-index shards while preserving lineage |
| [UC-156](uc-156-offline-secure-group-membership-rekey-epoch-courier.md) | Offline Secure Group Membership and Rekey-Epoch Courier | converge dynamic encrypted group membership and group epochs across partitions |
| [UC-157](uc-157-intermittent-teacher-student-knowledge-distillation-courier.md) | Intermittent Teacher–Student Knowledge Distillation Courier | ferry selected teacher guidance to compact edge models without deploying the teacher everywhere |
| [UC-158](uc-158-multi-sensor-slope-instability-precursor-evidence-courier.md) | Multi-Sensor Slope-Instability Precursor and Evidence Courier | carry compact slope/sensor trend state first and retrieve richer evidence later |
| [UC-159](uc-159-priority-preemption-resumable-bulk-interruption-courier.md) | Priority Preemption and Resumable Bulk-Interruption Courier | let bounded high-priority traffic interrupt bulk transfer without discarding verified progress |
| [UC-160](uc-160-intermittent-ai-model-canary-rollout-rollback-courier.md) | Intermittent AI Model Canary Rollout and Rollback Courier | stage exact AI model versions through canary cohorts with delayed promote/pause/rollback state |
| [UC-161](uc-161-modality-aware-federated-update-heterogeneous-sensor-courier.md) | Modality-Aware Federated Update Courier for Heterogeneous Sensors | keep delayed learning contributions bound to the sensor modalities and model version that produced them |
| [UC-162](uc-162-selective-restore-dependency-closure-recovery-plan-courier.md) | Selective Restore Dependency-Closure and Recovery-Plan Courier | restore only the minimal verified project/data closure from distributed intermittent caches |

## Priority from the 2026-10-04 batch

1. **UC-159** for the strongest core-network experiment: priority inversion, preemption, anti-starvation and resumable bulk transfer can be measured on the existing LoRa + rich-bearer teaching setup.
2. **UC-158** for the strongest local field/IoT experiment: a safe tabletop multi-sensor precursor campaign maps naturally to rural and Peloritani scenarios without claiming certified hazard detection.
3. **UC-160** for the strongest edge-AI/MLOps experiment: canary, delayed health evidence and rollback are concrete even when devices are disconnected for long periods.

**UC-161** is the strongest research-oriented heterogeneous-AI case. **UC-162** is the strongest new backup/recovery case.

## Physical-validation reminder

No entry in this addendum changes the frozen LoRa PHY. Range, PDR, RSSI/SNR interpretation, throughput, contact duration, energy, field reliability and detection quality remain measurement questions for real hardware trials.
