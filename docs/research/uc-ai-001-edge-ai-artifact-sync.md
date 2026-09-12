# UC-AI-001 — Edge AI model, adapter and dataset artifact synchronization

Status: DOMAIN-SPECIFIC USE CASE / RESEARCH + PROTOTYPE

## Problem

AI work increasingly produces large, versioned artifacts that may be present on different machines: model checkpoints, quantized variants, LoRA/adapters, embedding indexes, dataset shards, evaluation fixtures and manifests.

When portable/student nodes meet, the scarce network should normally exchange **identity, version, compatibility and availability metadata**, not multi-gigabyte model files. Later, home/school Wi-Fi, Internet or a local server can retrieve the exact artifact or missing shards.

Small adapters, indexes or patches may sometimes be worth carrying directly if the contact permits.

## Actors / nodes

- student/developer workstation;
- school AI lab/server;
- home GPU/server/NAS;
- portable Pollicino node;
- trusted peer cache;
- optional model/dataset registry or Internet provider.

## Why PollicinoNet fits

This case is related to UC-CONTENT-001 but adds AI-specific constraints:

- exact model/dataset version matters;
- compatibility between base model and adapter matters;
- artifacts have dependency graphs;
- large shared bases make delta/chunk reuse attractive;
- a tiny manifest may unlock a huge artifact already present locally;
- provenance and license/redistribution rights matter.

PollicinoNet can carry compact object identities and reconcile chunk availability while rich bearers move the heavy artifact.

## Possible bearers

- LoRa for tiny availability/version/reference messages only;
- BLE for close-range discovery;
- Wi-Fi/Wi-Fi Direct for adapters/small shards and local peer sync;
- Internet/LAN/NAS for large model/dataset retrieval;
- physical movement for delayed metadata and possibly removable-storage handoff.

## What can be tested now in software

Use synthetic, redistributable fixtures rather than real copyrighted/restricted model weights when unnecessary.

Test:

1. base-model + adapter dependency manifests;
2. two nodes with overlapping model shards;
3. exact version compatibility checks;
4. reference-only versus manifest versus missing-chunk transfer;
5. wanted-list for a model/dataset version;
6. update from version N to N+1 with high chunk overlap;
7. later rich-path resolution.

A useful benchmark asks: **how many scarce-link bytes are required to cause the correct AI artifact to become available later?**

## What requires real hardware

No LoRa hardware is required to validate the artifact/reconciliation model. Hardware is required only before claims about real reference capacity, contact usefulness or energy.

GPU hardware may be useful later to validate that a retrieved model/adapter pair actually loads and produces the expected artifact identity, but that is separate from the LoRa physical gate.

## Privacy / security

- model/dataset availability can reveal project activity;
- private fine-tunes and datasets must not be advertised with stable public identifiers;
- licenses and redistribution policy must be preserved;
- exact hashes/signatures are required before loading artifacts;
- untrusted model artifacts are executable-like supply-chain inputs and require provenance/sandbox policy;
- private dataset shards require encryption/access control.

## Implementation difficulty

**Medium** for synthetic manifests/reconciliation; **high** for a production artifact registry with licensing, signatures and secure loading.

## Minimal measurable hypotheses

- H1: dependency-aware manifests prevent useless transfer of adapters whose required base model is unavailable.
- H2: chunk reconciliation materially reduces rich-link bytes when model/dataset versions overlap heavily.
- H3: scarce-link reference exchange can trigger later correct artifact resolution with tiny on-air cost.

## Metrics

- correct artifact/version resolution rate;
- incompatible dependency attempts rejected;
- scarce-link reference/manifest bytes;
- rich-link bytes avoided through cache/chunk reuse;
- exact hash/signature verification;
- time until artifact becomes usable;
- rights/provenance policy violations prevented.

## Gate decision

**RESEARCH + PROTOTYPE as a child of UC-CONTENT-001.** This use case is valuable for workloads and integration testing but does not yet justify a new networking abstraction. Promote AI-specific protocol state only if generic content manifests cannot express measured needs.