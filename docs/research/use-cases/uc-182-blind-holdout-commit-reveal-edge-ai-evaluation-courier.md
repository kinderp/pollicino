# UC-182 — Blind-Holdout Commit–Reveal Edge-AI Evaluation Courier

## Problem solved
Disconnected students can run AI benchmarks on different machines, but comparing scores fairly is hard if reference labels or the final evaluation answers become visible **before** every participant has irreversibly submitted predictions. Network delay also means a late valid submission can arrive after scores are published.

UC-182 defines a **bounded, educational blind evaluation round**: publish an exact task/model/runtime manifest; keep reference labels at an authorized evaluator; bind each participant's submitted predictions before releasing the references; later score and reconcile delayed evidence.

## Actors / nodes
School benchmark coordinator, student laptops/Pi/edge models, label-holding evaluator, relay/store-and-forward boards, result verifier, optional FARO/AI benchmark registry.

## Why PollicinoNet fits
LoRa can carry `round_id + prediction_commitment + receipt/state`, while actual predictions, datasets, model weights and scores travel on BLE/Wi-Fi/LAN or physically. Asynchronous receipt and delayed scoring are the natural operation.

## Example state machine
```text
ROUND_OPEN -> SUBMISSION_COMMITTED -> SUBMISSION_SEALED
SUBMISSION_SEALED -> LABELS_REVEALED -> SCORED -> AUDITED
late order uncertain -> TIMING_UNPROVABLE (not silently accepted)
```
Bind commitments to **round_id, sample-order hash, model/runtime version, prediction artifact hash and random nonce**. The evaluator must protect labels by separate access control; a hash commitment alone cannot conceal low-entropy answers. To close a round offline, require a signed deadline/window rule and durable pre-reveal evidence (trusted time/witness/receipt), or explicitly mark ordering unknown. Do not claim cryptographic fairness simply because a digest exists.

## Possible bearers
- **LoRa:** round open/close status, commitment ID, status and exact score summary after evaluation.
- **BLE:** small prediction/submission bundles.
- **Wi-Fi/LAN:** predictions, sealed reference labels, evaluation evidence and model/dataset artifacts.
- **Internet:** optional final leaderboard/dashboard only after authorized reveal.
- **Physical:** SSD or student device carries large benchmark packs/evidence.

## Software tests now
Use public/synthetic classification examples, partition into 4 virtual students and one private evaluator. Compare normal free-form reporting vs pre-reveal commitments; inject a student who modifies predictions after seeing labels, reordered/duplicated commitments, conflicting submissions, a score arriving before evidence, wrong manifest/model, nonce reuse, partitions that prevent trustworthy closure and stale label version.

Metrics: incorrectly accepted post-reveal edits, valid completed rounds, indeterminate timing count, reproducibility, completion delay and bytes per bearer. Also combine with UC-114 contamination screening; commitment controls submission order, **not pretraining contamination or a compromised evaluator**.

## Hardware experiment — Messina
**4–6 relay boards** and 3–5 student PCs/Pi (different runtimes). A lab holds the reference labels offline. Students' prediction commitments move through the relay network among school/public checkpoints; large artifacts cross only when a richer bearer is available. Artificially delay one group past reveal and verify it is rejected or explicitly unresolved according to policy.

## Privacy / security
Begin with public/synthetic test data. Keep labels and prediction details under authorization. Sign exact round state; handle replay, equivocation and clock uncertainty. No high-stakes student assessment or rankings. Record that exposure to hidden labels, a colluding evaluator, or insufficient timing evidence invalidate fairness claims.

## Difficulty
**High** (provenance and temporal ordering are harder than hashing).

## Relationship to previous use cases
- **UC-038** compares exact edge-model results; **UC-182** adds **pre-reveal commitment, blind scoring and delayed fairness accounting**.
- **UC-114** audits training/evaluation overlap, **UC-126** seals distributed dataset cuts, **UC-127** supports exact inference replay. None by itself establishes whether a submitted prediction preceded label disclosure.
- **UC-064** can help detect contradictory signed round state.

## Validation boundary
Software tests validate honest participants/declared threat models and state-machine invariants. Real multi-device timing and link measurements require hardware. This is a classroom benchmark integrity experiment, not a formally proven secure competition protocol.
