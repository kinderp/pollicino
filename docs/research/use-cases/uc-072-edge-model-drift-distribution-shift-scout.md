# UC-072 — Edge Model Drift and Distribution-Shift Scout

## Idea

A model can remain bit-for-bit identical while the **world around it changes**. Sensors age, seasons change, camera viewpoints change, network traffic changes, or students use a system differently. Accuracy may degrade even though nothing is wrong with the model file.

This use case lets edge nodes compute small local drift/shift summaries and ferry only those compact warnings through PollicinoNet. Raw data stays local unless a later, explicitly authorized evidence request asks for a small sample.

## Problem solved

UC-038 benchmarks an exact model/runtime on devices. UC-032 selects uncertain samples for labeling. UC-057 moves approved inference toward local data. UC-072 addresses a different question:

> **has the local input/output distribution changed enough that we should investigate or re-evaluate the model?**

In a sparse network, edge nodes may be offline for days. Continuous telemetry is unrealistic and may expose too much data. We need compact, delayed signals that can answer:

- which model/input schema produced the summary?
- which time window or observation count does it cover?
- is there evidence of feature/output drift?
- how stale is the warning?
- do multiple nodes see the same shift or only one node?
- what exact evidence, if any, should be requested next?

## Actors / nodes

- edge inference nodes on student laptops/RPi/boards;
- sensor or camera nodes producing local observations;
- student relay/store-and-forward nodes;
- school AI evaluation node;
- optional teacher/reviewer who approves evidence retrieval;
- optional labeling workflow from UC-032.

## Why PollicinoNet fits

Drift summaries can be much smaller than raw datasets.

- **DISCOVERY:** `drift suspected`, model ID, coarse severity, time/window ID;
- **EXACT:** exact model hash/runtime/input-schema version, deterministic summary/sketch ID, window bounds, detector configuration and evidence references;
- **SEMANTIC:** labels such as `feature-shift`, `output-shift`, `uncertainty-rise`, used for triage rather than as authoritative diagnoses.

LoRa can carry tiny alerts or sketches. Wi-Fi/BLE/LAN can later move histograms, selected samples or benchmark packs. Store-carry-forward matters because the evaluator and affected node do not need simultaneous connectivity.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** drift alert, compact summary/sketch, model/schema IDs, evidence request/receipt;
- **BLE:** nearby histogram/sketch synchronization and selected small samples;
- **Wi-Fi/LAN:** richer evaluation data, approved examples, updated model/artifacts;
- **Internet:** optional authoritative model registry or evaluation service;
- **physical transport:** a laptop/SD card carries a larger approved evidence pack.

## What we can test now in software

Use public or synthetic datasets and create controlled distribution shifts such as:

- mean/variance shift in one sensor feature;
- new class frequency;
- gradual seasonal shift;
- sudden corrupted sensor range;
- model unchanged but preprocessing schema changed;
- one node drifting while others remain stable;
- detector false positive;
- delayed drift summary arriving after the condition has disappeared.

Then test:

- deterministic per-window summaries/histograms/sketches;
- duplicate/reordered summaries;
- model/schema mismatch rejection;
- multiple detector thresholds without pretending one threshold is universally correct;
- multi-node corroboration using UC-022;
- request a few exact samples only after policy/consent allows it;
- active-learning handoff to UC-032;
- compare raw-telemetry bytes versus summary-first workflow;
- evaluate stale warnings explicitly rather than treating them as current truth.

Useful metrics include detection delay in the simulator, bytes transmitted, false-positive/false-negative rate on synthetic shifts, time from alert to evidence retrieval, and fraction of raw data that never leaves the edge.

A key invariant is:

> a drift alert means “the local statistics changed under this detector/configuration”; it does not by itself prove that the model is wrong or that retraining is required.

## What requires real hardware

- 3–5 edge nodes running the same small model or deterministic inference pipeline;
- a harmless public/synthetic input stream or simple teaching sensors;
- one controlled physical change such as altered lighting, sensor placement or synthetic injected values;
- real LoRa carriage of compact drift state;
- richer-bearer retrieval of a small approved evidence set;
- measured bytes, latency and contact behavior.

Any claim about real-world model degradation must come from measured labeled evidence, not merely a drift detector firing.

## Messina teaching scenario

Deploy three identical environmental or image-classification exercises at controlled school checkpoints representing Messina, Villafranca/Rometta and Spadafora. All nodes start from the same pinned model and preprocessing schema. One node later receives a controlled input shift — for example, a changed sensor calibration profile or a deliberately different lighting condition.

Its node produces a compact `DriftSummary`. A student relay carries that summary to the school evaluator. The evaluator does not immediately demand the full dataset; it requests only a bounded evidence sample. Another relay later returns that sample over Wi-Fi/BLE, and the class decides whether the problem was real drift, sensor/configuration error or a harmless false alarm.

## Privacy / security

Drift summaries can leak information about local populations or behavior even without raw data.

- use public/synthetic data first;
- avoid fine-grained per-person statistics;
- bind every summary to exact model, preprocessing schema, detector config and time/window;
- apply minimum group/window sizes where aggregation could reveal individuals;
- treat evidence retrieval as a separate authorized step;
- do not broadcast raw samples over LoRa;
- retain only what is needed for the experiment;
- prevent an attacker from forging drift alerts that trigger costly retraining or data collection.

## Difficulty

**Medium–High.** The DTN transport is simple; the hard part is interpreting drift correctly, keeping provenance exact and avoiding overreaction to noisy statistics.

## Research signal

A Scientific Reports paper published on 2 May 2026 studies concept-drift detection and communication-efficient adaptation in distributed edge/federated environments, including client-side drift detection and selective communication. PollicinoNet does not need to reproduce that learning architecture: the useful idea is that local change detection can produce a compact event that deserves priority without continuously exporting raw data.

Reference:

- https://doi.org/10.1038/s41598-026-51535-6
