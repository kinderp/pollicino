# UC-225 — Offline AI Dataset Poisoning Canary and Quarantine Courier

## Problem and practical application
A school AI dataset arrives by a student-carried device from a disconnected laboratory. Its exact hash matches the publisher's manifest, but it could still contain deliberately wrong labels or manipulated examples **created before signing**. A valid signature is evidence of origin/integrity, not evidence that a training set is safe. UC-225 adds a review gate and a small signed quarantine decision before offline training/import.

## Actors and Messina scenario
Two or three air-gapped PCs/Raspberry Pis in classroom labs (fictional site labels Messina, Villafranca, Venetico), an authorized dataset publisher, human teacher reviewer, local screening worker and 4–6 student relay boards. All training data are generated synthetic toy records; no actual pupil data. This could feed TheBitLab/FARO reproducible model experiments or Raiatea ingestion workflows.

## Why PollicinoNet and bearers
The large dataset can stay on a high-capacity bearer, while compact screening outcomes, exact evidence IDs and authorized quarantine decisions travel store-and-forward. Every outcome is bound to dataset hash, normalization/label-schema version, test suite revision and reviewer identity/role:
- **LoRa:** digest, scan-needed/request, quarantine epoch/status, revision IDs (never raw private samples).
- **BLE:** small screening summaries and permission metadata.
- **Wi-Fi/LAN/Internet:** authorized dataset and exact canary evaluation reports.
- **Physical encrypted USB/SD:** bulk transfer where allowed.
Training must not start solely because a digest is available or a stale ALLOW was cached.

## Software-only experiment (proposed, not executed)
Create a toy text/image classification dataset with deterministic seeded splits. Inject known label flips, duplicate clusters, a small targeted trigger pattern and benign-but-rare outliers. Compare (a) no screening, (b) hash/license check alone, (c) simple label-consistency/rule checks, (d) held-out canary tests plus human review. Include missing canary, scanner version mismatch, signed-but-poisoned source, false alarms, delayed quarantine arriving after import request, rollback and duplicate decisions. Explicit decisions: PENDING_SCAN, QUARANTINED, REVIEW_REQUIRED, APPROVED_FOR_SANDBOX_TEST and REVOKED. Assert fail-closed for new privileged import when risk evidence is unknown; measure detection on injected fixtures, false flags, review workload and transfer bytes. No detector can certify an arbitrary dataset clean.

## Real-hardware demonstration
2–3 supervised school computers, 4–6 LoRa boards and two controlled partitions. Deliver compact manifest before the dataset by LoRa, ferry synthetic dataset later using Wi-Fi/USB, then deliberately delay a signed QUARANTINE decision. Verify that post-decision training/export is blocked on every reconnected node and that already completed toy experiments are recorded as potentially affected, not magically undone. Measure real propagation delays and completed file transfer separately from ML detector results.

## Privacy, security, limitations and difficulty
**High.** Synthetic/public data only; no real malicious code or executable payload; treat received data as untrusted, sandbox parsers and ML workers, apply resource limits, authenticate reviewers and exact versions, rate-limit screening requests, and record uncertainty. Quarantine is not a claim of legal invalidity, proof of model contamination, or automatic machine unlearning.

## Nonduplication check
UC-114 audits *training/evaluation overlap*, UC-209 preserves annotator disagreement, UC-205 checks *licenses and consent*, UC-081 provides distributed CI, and UC-219 compares compute outputs. UC-225 is the distinct **maliciously or accidentally poisoned training-content admission** gate with seeded canary experiments and delayed quarantine propagation.

Reference: NIST AI 100-2e2025, Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations, https://csrc.nist.gov/pubs/ai/100/2/e2025/final
