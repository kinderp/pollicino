# UC-140 — Delayed Ground-Truth and Edge-Calibration Feedback Courier

## Idea

Let an edge model make a prediction now, then attach the real outcome or reviewed label later when ground truth becomes available through a different route or at a different time.

## Problem solved

Edge-AI feedback is often delayed: a classification may be reviewed later, an anomaly confirmed only after inspection, a robot prediction judged after a mission, or a forecast scored only when the future observation arrives. If predictions and later labels are not bound to the exact sample/model/inference, calibration statistics become unreliable.

## Actors / nodes

Sample source, edge inference node, student relay/store-and-forward nodes, human or sensor ground-truth source, calibration/evaluation worker, optional model registry and Raiatea evidence store.

## Why PollicinoNet fits

The feedback record is tiny: sample/evidence hash, inference ID, exact model/preprocessor hash, prediction/confidence bucket, label/outcome ID, label source/type, label time with uncertainty, review status and calibration epoch. LoRa can ferry these records independently of the larger sample.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: inference ID, compact prediction, later label/outcome and calibration status.
- BLE: small evidence snippets or reviewer handoff.
- Wi-Fi/LAN: raw samples, full outputs, recalibration datasets and updated models.
- Internet: optional remote reviewer/public benchmark.
- Physical transport: labeled examples on phone/laptop/SD.

## What we can test now in software

Use a public dataset with known labels but deliberately delay label release. Test out-of-order labels, old-model labels, corrected labels, missing labels, duplicate reviewers, reviewer disagreement, uncalibrated confidence and distribution shift.

Measure label latency, fraction eventually labeled, Expected Calibration Error, Brier score where appropriate, selective risk/coverage, calibration by model version and bytes moved before/after evidence escalation.

Automatic online retraining should be a later, separately gated step.

## What requires real hardware

Use 4–6 LoRa nodes plus at least two compute/reviewer devices. Replay public image or sensor samples at different nodes; emit predictions immediately; release labels later from another node and ferry them through relay contacts. A second safe experiment can classify controlled light/sensor states with known ground truth.

## Messina teaching scenario

Groups in Messina, Villafranca and Rometta/Venetico run an approved classifier on public samples. Labels are held at school or by a group in Spadafora and released later. Student relay nodes ferry compact labels back. Students can then plot label delay and compare confidence with observed correctness.

## Privacy / security

Use public/synthetic data first, keep sensitive raw samples off LoRa, bind labels to exact sample and inference IDs, distinguish ground truth from human review/proxy labels/pseudo-labels, preserve disagreement, and do not use the first profile for high-stakes student evaluation, medical or legal decisions.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-032 chooses samples for active learning; UC-140 closes the loop when labels arrive. UC-038 runs planned evaluation rounds. UC-072 detects drift without immediate labels. UC-101 uses model disagreement for triage. UC-127 makes one inference replayable.

## Research signal

Delayed labels and delayed feedback remain active 2026 research topics in online learning. PollicinoNet provides a concrete setting in which feedback delay is caused by real connectivity partitions.

References:

- https://arxiv.org/abs/2606.22950
- https://www.ijcai.org/proceedings/2026/503
- https://aclanthology.org/2026.acl-long.259/
