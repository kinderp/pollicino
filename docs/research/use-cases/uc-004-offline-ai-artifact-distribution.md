# UC-004 — Offline AI Artifact Distribution

## Idea

Distribute AI artifacts such as small models, LoRA adapters, tokenizer files, datasets, evaluation packs and model manifests across a disconnected network without pretending that LoRa is a bulk-transfer link. LoRa carries compact object identities, requests and availability hints; larger bytes move over Wi-Fi, Internet, LAN/NAS or physical carry.

## Problem solved

A school lab or rural edge node may need an updated model or dataset while connectivity is intermittent. Re-sending the whole artifact to every node is wasteful, especially when many chunks are already cached locally.

## Actors / nodes

- school model/dataset publisher;
- student PCs or edge nodes;
- student-carried PollicinoNet relays;
- home/school NAS or cache;
- optional edge inference devices.

## Why PollicinoNet fits

The case directly exercises content addressing, chunk inventory, exact reconstruction, store-and-forward and rich-link handover. Scarce-link traffic can answer: *which artifact/version is needed, who has it, and which chunks are missing?*

Recent research on edge-AI updates over LoRaWAN and federated LoRA reinforces the broader idea that model-update traffic deserves explicit bandwidth/energy-aware treatment, while PollicinoNet keeps the transport adapter separate from its core.

## Possible bearers

- **LoRa:** manifest coordinate, version, missing-set summary, priority and rendezvous;
- **BLE:** nearby control/authentication and small artifacts;
- **Wi-Fi/LAN/Internet:** model/dataset chunks;
- **physical transport:** USB/SSD/phone/portable cache can move large content between disconnected sites.

No PHY change is required or proposed.

## What we can test now in software

- content-addressed chunking of synthetic model/dataset files;
- inventory reconciliation between multiple caches;
- resumed transfer after disconnection;
- version/delta experiments between related artifacts;
- signed manifests and final hash verification;
- simulated student mobility and multi-source chunk retrieval;
- metrics: scarce-link TRC, cache hit ratio, bytes avoided, completion delay and verification failures.

## What requires real hardware

- LoRa exchange of compact manifest/request traffic;
- real handover to Wi-Fi/LAN/USB for bulk content;
- measured discovery success and end-to-end handoff delay.

Large-model transfer over LoRa is not an intended success criterion.

## Privacy / security

Signed manifests are important to reduce model-poisoning risk. Dataset licensing and personal-data restrictions must travel with the artifact metadata. Private artifacts should not expose stable public content identifiers when those identifiers leak sensitive membership or interests.

## Difficulty

**Medium to high.** The radio part is small; the difficult parts are chunk/version semantics, cache reconciliation, provenance and secure artifact distribution.
