# UC-154 — Uncertainty-Gated Edge AI Escalation and Expert-Return Courier

## Problem solved

A small edge model can answer easy cases locally, but forcing it to answer every case is risky. Sending every sample to a larger model or human reviewer is also wasteful when connectivity is intermittent.

UC-154 creates an asynchronous cascade:

```text
small local model
  -> confident: local result
  -> uncertain: escalation capsule
       -> stronger edge/cloud model or human reviewer
       -> delayed result returns later
```

The key is that escalation and the eventual answer stay bound to the exact sample, model version and policy that produced the uncertainty decision.

## Actors / nodes

- constrained edge device or laptop running a small model;
- student relay/store-and-forward nodes;
- stronger school workstation / local GPU / optional Internet model;
- optional human reviewer;
- result consumer;
- Raiatea/FARO provenance store when relevant.

## Why PollicinoNet fits

Only a small fraction of cases should need escalation. The control plane can therefore carry compact metadata:

- inference ID;
- sample hash or selector;
- local model hash/version;
- uncertainty/confidence summary;
- escalation reason;
- deadline/priority;
- allowed destination class;
- returned decision/status.

Large samples, images, audio or document evidence remain on BLE/Wi-Fi/LAN or physical media.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** inference/escalation ID, compact uncertainty, route/status and result-ready signal.
- **BLE:** small feature/evidence bundles.
- **Wi-Fi/LAN:** selected samples, embeddings, richer model outputs and review material.
- **Internet:** optional higher-tier model or expert service when policy permits.
- **Physical transport:** selected evidence and result packages between disconnected sites.

## What we can test now in software

Use a public image, text or sensor dataset and two models of deliberately different capability.

Implement:

1. local inference;
2. calibrated or intentionally simple escalation threshold;
3. exact escalation capsule;
4. delayed stronger-model or human-label response;
5. visible `LOCAL`, `ESCALATED`, `ANSWERED`, `EXPIRED` and `UNRESOLVED` states.

Test:

- low/high thresholds;
- link unavailable for long periods;
- late answer after the user has already accepted a provisional result;
- stale local model version;
- stronger model also abstains;
- duplicate escalations;
- evidence unavailable when the escalation reaches the expert;
- privacy policy that forbids exporting the raw sample.

Measure fraction escalated, accuracy/error on a public ground-truth set, time-to-provisional-result, time-to-final-result, bytes per tier and unresolved fraction.

Confidence must not be assumed calibrated unless measured.

## What requires real hardware

Use 4–6 LoRa boards, one weaker compute device and one stronger workstation. The weak node processes a public/synthetic stream while the stronger node is intermittently reachable.

Keep LoRa to compact control/status. Move only selected evidence over Wi-Fi/BLE during real encounters.

Measure real contact delay and transfer cost before claiming networking benefits.

## Messina teaching scenario

A small model runs on a laptop/Pi associated with a Rometta/Venetico group. Straightforward public sensor/image examples are handled locally.

Only uncertain cases become escalation jobs. Student relays carry those jobs toward a stronger school workstation in Messina; detailed evidence moves over Wi-Fi when a suitable contact occurs. The answer can return through a different relay.

This creates a visible experiment in which model quality and network availability interact without requiring every sample to leave the edge.

## Privacy / security

Start with public/synthetic data. A confidence score, embedding or soft output can still reveal information about the input and should not be treated as anonymous.

The escalation policy must include an explicit allowed-output/evidence policy. Bind every returned answer to the exact request, sample and model/reviewer identity. Human review should remain distinguishable from model review.

No safety-critical action should depend on this experimental cascade.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-057 moves an approved model/task to private data. UC-078 decides local execution versus task offload. UC-101 uses disagreement among models to select samples. UC-140 attaches delayed ground truth to past predictions.

UC-154 focuses on **a persistent asynchronous cascade where a local model may abstain and a stronger model or human expert returns a later answer**.

## Research signal

Edge–cloud–expert cascades and uncertainty-gated split inference are active in 2026.

References:

- Q. Hou et al., “Reliable LLM-based edge-cloud-expert cascades for telecom knowledge systems,” IEEE Transactions on Communications, 5 June 2026.
- “Uncertainty-Gated Split Inference with Online Threshold Adaptation for Edge-IoT Under Dynamic Networks,” IEEE Internet of Things Journal, early access, 18 August 2026, DOI: 10.1109/JIOT.2026.3725141.
