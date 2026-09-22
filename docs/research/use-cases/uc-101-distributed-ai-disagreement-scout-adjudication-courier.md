# UC-101 — Distributed AI Disagreement Scout and Adjudication Courier

## Idea

Run the **same bounded observation or sample** through multiple edge models/nodes and ferry only compact predictions plus uncertainty/disagreement metadata first. If the models agree strongly, no large evidence transfer may be needed; if they disagree, PollicinoNet escalates the case to a stronger model, a human reviewer or a richer evidence transfer.

The pattern is:

```text
cheap local opinions first -> disagreement signal -> selective escalation
```

This is useful when edge nodes have different models, quantizations or sensors and the network cannot afford to move every raw sample immediately.

## Problem solved

Edge AI deployments can fail in two expensive ways:

- shipping every raw input wastes bandwidth/storage;
- trusting one local model hides uncertainty and device-specific errors.

A network of student devices may naturally contain different model variants, runtimes and hardware. That heterogeneity can be used as a **diagnostic signal** rather than treated only as a deployment problem.

We need a mechanism that answers:

> Do independent edge opinions agree enough to leave the case local, or should this exact case be escalated for better evidence/review?

## Actors / nodes

- sample/observation source node;
- two or more edge inference nodes;
- student relay/store-and-forward nodes;
- optional stronger edge/GPU adjudicator;
- optional human reviewer;
- evidence/provenance collector.

## Why PollicinoNet fits

Predictions and model identities are small; the raw image/audio/log or high-dimensional feature evidence can be much larger.

- **DISCOVERY:** node advertises an inference capability/profile;
- **EXACT:** sample hash, model hash/variant, preprocessing hash, output schema and vote/result;
- **SEMANTIC:** `agree`, `disagree`, `uncertain`, `needs-human-review` or `needs-rich-evidence` derive from exact results and a declared policy.

LoRa can therefore carry model/result summaries while Wi-Fi/BLE/physical transport carries only the evidence selected for escalation.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** sample/evidence hash, model ID/hash, compact label/score bucket, disagreement status and adjudication request;
- **BLE:** small thumbnails/features or nearby model handoff;
- **Wi-Fi/LAN:** full image/audio/log, larger model, explanations and adjudication evidence;
- **Internet:** optional access to a remote reference model when explicitly allowed;
- **physical transport:** phone/laptop/SD carries samples selected for later review.

## What we can test now in software

Use a public or synthetic dataset and several intentionally heterogeneous models, for example:

- small quantized model;
- larger local model;
- alternative architecture;
- deliberately degraded/stale model;
- simple non-ML rule as a diversity baseline.

Define an `EdgeOpinion`:

```text
sample_hash
model_hash
preprocess_hash
output_schema
prediction
confidence_or_score_bucket_optional
uncertainty_summary_optional
runtime_profile
```

Define an `AdjudicationPolicy` such as:

```text
minimum_independent_opinions
agreement_rule
disagreement_threshold
escalation_target
max_evidence_bytes
expiry
```

Test:

- all models agree correctly;
- all models agree incorrectly on a crafted/synthetic case;
- one model disagrees;
- two weak models disagree with a stronger model;
- result arrives after adjudication already happened;
- same model duplicated under two node identities;
- stale model version;
- preprocessing mismatch;
- sample hash mismatch;
- escalation target unavailable;
- human review result arrives days later;
- active-learning handoff to UC-032 for selected disagreement cases.

Useful metrics include disagreement rate, percentage of samples escalated, bytes of raw evidence transferred, delay to adjudication, diversity of model variants, error rate inside `agree` versus `disagree` subsets and false reassurance caused by correlated agreement.

The last metric is essential: **agreement is not proof of correctness**.

## What requires real hardware

A first physical experiment can use:

- 3–5 LoRa nodes;
- two heterogeneous laptops/Pi/phones running different small models;
- one more capable adjudication machine;
- a public image/sensor dataset replayed locally.

The initial experiment should not involve safety-critical classification. The network can deliberately isolate the three inference nodes, then allow relay contacts to ferry compact opinions before rich evidence is selectively moved.

Later, a harmless real sensor/camera task can be added, but accuracy, latency, energy and bandwidth savings must be measured from the real setup.

## Messina teaching scenario

Different student groups in Messina, Villafranca and Rometta/Venetico run different approved local model variants on the same public test samples. A PollicinoNet relay carries only compact opinions between groups.

For one sample:

```text
model-A -> class 3
model-B -> class 3
model-C -> class 7
```

The disagreement policy marks the sample for adjudication. Only that sample, not the entire dataset, is later transferred to the school workstation over Wi-Fi/physical transport.

Students can then compare:

- network cost with and without selective escalation;
- whether disagreement predicts errors;
- cases where all models agree but are still wrong;
- effect of model diversity and quantization.

## Privacy / security

- never send raw sensitive samples over LoRa;
- bind every opinion to exact sample/model/preprocessing hashes;
- do not expose model outputs for personal/medical/legal/student-evaluation data in the first profile;
- use public/synthetic datasets initially;
- enforce independence rules so one model copied onto three nodes does not masquerade as three independent witnesses;
- treat confidence as model output, not a calibrated guarantee unless calibration was separately validated;
- preserve an explicit `UNKNOWN/UNRESOLVED` state;
- cap evidence size and adjudication fan-out;
- avoid using disagreement alone for safety decisions;
- human review remains an external decision, not automatically trusted merely because it is human.

## Difficulty

**Medium-high.** Basic vote exchange is easy; meaningful independence, uncertainty, correlated-error detection and selective escalation policy are the real research work.

## Why this is distinct from nearby use cases

- **UC-022:** corroborates multiple observations/witnesses of an event; UC-101 compares multiple *model interpretations* of the same exact sample/evidence.
- **UC-032:** chooses informative samples for labeling; UC-101 can produce one signal that feeds that selection.
- **UC-038:** evaluates model variants systematically; UC-101 is an operational selective-escalation workflow.
- **UC-057:** moves inference toward data; UC-101 combines several returned opinions and decides whether further evidence/compute is justified.
- **UC-072:** detects distribution drift over time; UC-101 focuses on per-sample disagreement.

## Research / implementation signal

Recent 2026 work continues to use ensemble disagreement as a practical uncertainty/triage signal, including workflows that defer uncertain cases for review. At the same time, other 2026 work warns that correlated models can agree while still being wrong. That is exactly the constraint PollicinoNet should encode: disagreement can trigger escalation, but agreement must never be treated as proof of truth.

References:

- https://doi.org/10.3390/make8080233
- https://doi.org/10.1145/3786319
- https://www.roboticscenter.ai/research/papers/harnessing-disagreement-detecting-correlated-agreement-blindness-in-multi-agent-triage-2607
