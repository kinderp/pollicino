# UC-157 — Intermittent Teacher–Student Knowledge Distillation Courier

## Problem solved

A small edge device may run a lightweight student model but not a larger teacher model. When connectivity is intermittent, the student can request selected teacher guidance and use it later, without copying the full teacher model to the edge device.

## Actors / nodes

Student-model device, stronger teacher workstation, public benchmark data, student relay nodes, evaluator.

## Why PollicinoNet fits

The job metadata are compact: job ID, selected sample IDs, student version, teacher version, requested target type and result state. Larger sample and target bundles can move later over Wi-Fi, BLE or physical storage. The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** job ID, sample digest, model versions and result-ready state.
- **BLE:** small target bundles.
- **Wi-Fi/LAN:** sample batches, teacher outputs and checkpoints.
- **Internet:** optional teacher service.
- **Physical transport:** larger bundles.

## What we can test now in software

Use a public dataset with a small student model and a larger teacher model. Compare ordinary labels with teacher guidance, then add delayed responses, duplicate responses, a changed teacher version, a changed student version and expired jobs.

Measure student quality on a fixed public test set, transferred bytes, completed jobs, rejected stale guidance and compute cost.

## What requires real hardware

Use 4–6 LoRa boards, one modest computer and one stronger workstation. The student keeps running locally while teacher jobs are delayed. LoRa carries only compact job/status metadata; richer bearers carry larger data.

## Messina teaching scenario

A lightweight model runs on a student computer in Rometta/Venetico and a stronger teacher runs on a school workstation in Messina. Selected difficult public examples are queued for teacher guidance and the results return through later contacts.

## Privacy / security

Start with public or synthetic examples. Treat teacher outputs as data that may still reveal information about the source examples. Keep every returned target tied to the exact sample and teacher version.

## Difficulty

**High.**

## Why this is distinct

UC-032 carries active-learning labels, UC-016 carries federated training rounds and UC-145 handles delayed training contributions. UC-157 studies delayed teacher guidance for training a compact student model.

## Research signal

Knowledge distillation for edge systems remains active in 2026, including cloud-edge and hierarchical designs with compact student models.
