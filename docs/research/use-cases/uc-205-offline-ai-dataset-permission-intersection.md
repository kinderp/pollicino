# UC-205 — Offline AI Dataset License and Consent Intersection Gate

## Problem and concrete scenario
Three disconnected school or edge-AI teams have different datasets. One is openly redistributable, another can be used only for a specific classroom experiment, and a third has a later withdrawal of permission. A network that can ferry all three objects must **not assume they can be mixed or republished**. A receiving team needs a decision with provenance and an explicit `UNKNOWN/STOP` state when a relevant authorization is absent.

## Actors / nodes
Dataset owners/publishers, student-controlled AI workstations, PollicinoNet relays, school research reviewer and dataset-mix policy evaluator. No student personal data are needed: tests use artificial image/text labels and synthetic policy fixtures.

## Why PollicinoNet fits and precise contract
Each exact dataset version is linked to an authenticated `permission_manifest`: content hash, publisher authority, permission scope, allowed operations (view/train/derive/redistribute), audience, expiry, policy epoch and revocation reference. A proposed `MIX_INTENT` names exact input hashes and planned operation. A deterministic evaluator can output `ALLOW_FOR_TEST`, `DENY`, `REQUIRES_REVIEW` or `UNKNOWN`. A delayed policy update invalidates earlier approvals for *future* operations; it cannot retroactively guarantee removal from already copied models or caches.

## Bearers
- **LoRa:** content/policy digests, revocation epochs, permission status and request IDs.
- **BLE:** close-range small policy and descriptor exchange.
- **Wi-Fi/LAN/Internet:** datasets, auditable policy records and review reports.
- **Physical USB/SD:** controlled bulk datasets, encrypted when not public.

## Software-only experiment (proposed; not run)
Use 4 local dataset versions and 3 simulated partitions. Fixtures: compatible open licenses, incompatible redistributable/nonredistributable permissions, missing manifest, revoked grant received late, replayed old permission, modified dataset hash, mixed model-training and redistribution intents. Assert *fail closed* on absence of evidence and exact per-version binding. Compare unauthorized operation count and false denials; keep reviewer override separately signed and scoped.

## Physical test and measurements needed
4–6 boards and 2–3 laptops at separate school labs. Distribute digests over LoRa and example datasets via Wi-Fi/USB; introduce a revocation in only one island, rejoin partitions, and verify policy convergence **before further artificial training/export**. Record actual dissemination delay and byte counts. Real legal compliance cannot be inferred from a technical demo.

## Privacy, security, difficulty
**High.** License expression is not a substitute for legal analysis; only explicitly machine-testable permission subsets may be automatically evaluated. Consent can be purpose-specific and revocable; retain only minimal authorization metadata and protect participant identity. Do not interpret 'permission to receive' as 'permission to train' or 'permission to publish'. Quarantine uncertain or incompatible datasets.

## Distinction from existing catalog
UC-076 ferries an individual object's usage-policy envelope, UC-056 captures data-donation provenance, UC-148 handles federated unlearning, and UC-139 audits deletion. **UC-205 decides whether a *combination of specific versions* is authorized for a *specific AI operation* under partitioned, potentially stale permissions.**

## Guardrails
Experiments use exclusively synthetic/public data and reviewed toy permissions. Does not automate legal decisions or guarantee machine unlearning; frozen LoRa PHY/MAC unchanged.