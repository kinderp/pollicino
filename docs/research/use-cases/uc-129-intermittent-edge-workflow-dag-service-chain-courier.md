# UC-129 — Intermittent Edge Workflow DAG and Service-Chain Courier

## Idea

Execute a multi-stage workflow across heterogeneous intermittently connected devices, where each stage may run on a different node and its output becomes the exact input of later stages.

Example: source document -> OCR -> classifier -> embedding -> Raiatea index.

## Problem solved

Single-task offload is not enough for applications with dependencies. A live central orchestrator can disappear while workers remain available at different times and places. We need workflow identity, dependencies, exact input/output hashes, retries, deadlines and cancellation to survive long partitions.

## Actors / nodes

Workflow requester/coordinator, student relay/store-and-forward nodes, heterogeneous laptop/Pi/workstation workers, artifact caches, optional Raiatea store and verifier.

## Why PollicinoNet fits

DAG/control metadata is compact while stage inputs and outputs can be large. LoRa carries workflow IDs, dependency readiness, capability requests, assignments and result hashes. BLE/Wi-Fi/LAN or physical carry moves large artifacts. The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: workflow/stage IDs, dependency state, capability request, assignment, compact status/result hash.
- BLE: small inputs and local handoff.
- Wi-Fi/LAN: images, models, document batches, checkpoints and stage artifacts.
- Internet: optional cloud worker or registry fast path.
- Physical transport: laptop/SSD/phone carrying large inputs between islands.

## What we can test now in software

Build a small DAG: public document -> OCR -> classify + embed -> merge -> index.

Inject duplicate completion, worker disappearance, out-of-order results, stale dependency versions, retry races, wrong output hashes, deadline expiry and cancellation.

Useful states include BLOCKED, READY, ASSIGNED, RUNNING_UNKNOWN, COMPLETED, FAILED, RETRYABLE, STALE_INPUT and CANCELLED.

Compare first-capable-worker, locality-first, deadline-aware, artifact-near-worker and UC-108 queue-pressure-aware policies.

## What requires real hardware

Use 3–5 compute devices with deliberately different capabilities plus 4–6 LoRa nodes. Interrupt connectivity between stages and let control state and artifacts arrive through different relays.

Do not claim latency or energy advantages until the workflow is measured end-to-end on the actual devices.

## Messina teaching scenario

A document is captured in Messina. A laptop near Villafranca performs OCR. An embedding-capable worker in Rometta/Venetico processes the text later. A school workstation creates the final index after the artifacts return.

Students can inspect the exact lineage from source hash to OCR, embedding and index fragment hashes.

## Privacy / security

Use opaque workflow/stage IDs on LoRa, preserve source-data policy through every stage, sandbox jobs, cap resource use, keep retries idempotent where possible and never let stale stage results silently overwrite newer attempts.

## Difficulty

High. A linear pipeline is easy; correct DAG execution with retries, versioned dependencies and intermittent resource placement is substantially harder.

## Why this is distinct

UC-014 discovers one compute capability; UC-078 chooses local versus delayed offload for one task; UC-079 checkpoints one computation; UC-099 is one specific Raiatea ingestion pipeline. UC-129 is a reusable dependency-aware execution model for arbitrary intermittent workflows.

## Research / implementation signal

2026 edge-workflow work continues to treat dependency analysis, resource-aware placement and end-to-end deadlines as first-class orchestration problems. ClusterLess studies those issues across federated edge clusters; PollicinoNet adds much longer disconnections.

Reference:

- https://arxiv.org/abs/2605.04310
