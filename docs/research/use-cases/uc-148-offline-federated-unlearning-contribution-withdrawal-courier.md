# UC-148 — Offline Federated Unlearning and Contribution-Withdrawal Courier

## Problem solved

A training contribution can become invalid after a model has already been produced: a synthetic participant may withdraw, a dataset partition may be corrected, or a benchmark slice may have been included by mistake. In an intermittent network the participant, model coordinator and workers holding relevant checkpoints may not be reachable at the same time.

UC-148 carries a small withdrawal request and keeps it tied to the exact contribution, dataset snapshot and model lineage. It also records what action was actually taken instead of reducing every outcome to “unlearned”.

## Actors / nodes

Synthetic data contributor, model coordinator, training/evaluation worker, checkpoint cache, verifier, student relay and optional FARO/Raiatea provenance store.

## Why PollicinoNet fits

The control state is small: contribution ID, dataset snapshot ID, target model hash, model lineage ID, request epoch, status and evidence reference. Large checkpoints and evaluation artifacts can wait for Wi-Fi, LAN or physical transport.

Store-and-forward is useful because the request must survive partitions and reach the relevant model branches even if the original participant is offline for hours or days.

Useful states include:

- `WITHDRAWAL_REQUESTED`
- `REQUEST_ACCEPTED`
- `AFFECTED_MODEL_IDENTIFIED`
- `RETRAIN_REQUIRED`
- `APPROXIMATE_UNLEARNING_REPORTED`
- `RETRAINED_FROM_CLEAN_SNAPSHOT`
- `VERIFICATION_PASSED`
- `VERIFICATION_INCONCLUSIVE`

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** request ID, model/contribution hashes and compact status.
- **BLE:** small manifests and evaluator summaries.
- **Wi-Fi/LAN:** checkpoints, evaluation artifacts and retraining outputs.
- **Internet:** optional public model registry or benchmark lookup.
- **Physical transport:** school-managed SSD/USB for very large checkpoints.

## What we can test now in software

Use only public or synthetic data. Train a small federated model with 3–5 virtual clients and record exact per-round lineage. Then withdraw one synthetic client or a known sample subset.

Compare:

1. clean retraining from a known checkpoint;
2. one or more approximate unlearning methods;
3. delayed requests arriving after 1, 5 and 20 model epochs;
4. duplicate requests;
5. stale model identifiers;
6. a late contribution from the already-withdrawn participant.

Measure model utility, distance from the clean-retrain baseline, request-to-action latency in the simulated DTN and control bytes.

These are experiment metrics, not proof that a real privacy obligation has been satisfied.

## What requires real hardware

Use 4–6 LoRa boards and at least three computers acting as intermittent learning clients. Keep one client disconnected while newer model rounds are produced, then ferry the withdrawal request and result evidence through real contacts.

Actual contact delay, transfer time and energy must be measured on the hardware before making physical-network claims.

## Messina teaching scenario

Split a public dataset among laptops in Messina, Villafranca and Rometta/Venetico-Spadafora. The shared model advances while one group is offline. That group later issues a **synthetic withdrawal** for its assigned partition.

Student-carried nodes relay only the compact request/status state; large model checkpoints move later over Wi-Fi or school-managed removable media.

## Privacy / security

Start only with public/synthetic data and synthetic identities. Keep raw samples off LoRa. Bind every request to the exact contribution and model lineage. Treat model checkpoints and updates as potentially sensitive. Preserve an audit trail with minimal identifiers.

A worker receipt means “this action was reported”, not “complete forgetting has been mathematically proven”. Keep `VERIFICATION_INCONCLUSIVE` as a valid result.

## Difficulty

**High.**

## Why this is distinct

UC-016 carries federated training rounds, UC-056 binds consent to data donation, UC-077 propagates deletion tombstones, UC-126 seals dataset snapshots and UC-145 handles late training contributions.

UC-148 handles the different problem of **withdrawing influence after distributed training has already happened**.

## Research signal

Federated unlearning and especially verifiable federated unlearning are active research topics in 2026. They are useful design references, but they do not establish that any PollicinoNet method already provides a legal or mathematical unlearning guarantee.

References:

- IEEE Internet Computing, 2026, “Toward Verifiable Federated Unlearning”
- IJCAI 2026, “FedUP: One-Shot Federated Unlearning via Centroid-Guided Plug-in Filters”
