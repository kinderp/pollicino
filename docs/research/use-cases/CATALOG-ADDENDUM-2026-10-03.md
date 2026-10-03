# PollicinoNet use-case catalog addendum — 2026-10-03

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

## Priority from the 2026-10-03 batch

1. **UC-153** for a real sensor/relay field experiment using the same contact infrastructure as the network observatory.
2. **UC-154** for an immediately testable edge-AI service where uncertainty determines whether a case is escalated.
3. **UC-156** for a core security/state-convergence experiment using reviewed group-messaging implementations.

**UC-155** is the strongest new Raiatea infrastructure case. **UC-157** is a promising second-phase AI research case.
