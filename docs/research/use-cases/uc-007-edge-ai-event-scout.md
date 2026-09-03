# UC-007 — Edge AI Event Scout

## Idea

Run a small classifier or anomaly detector near the data source and send only a compact event description over LoRa, while retaining the exact raw evidence locally for later retrieval over Wi-Fi/Internet or by physical carry.

Examples suitable for teaching include synthetic machine-vibration anomalies, environmental threshold events, image classes from a prepared non-personal dataset, or robot/sensor state classification.

## Problem solved

Raw audio, images and dense sensor streams are too expensive for a scarce link. Often the remote side first needs to know that *something interesting happened*, not receive every source byte immediately.

## Actors / nodes

- sensor/edge node or nearby phone/PC running the model;
- LoRa relay nodes;
- school/server verifier;
- optional cache storing the exact raw object;
- later rich-link consumer of the raw evidence.

## Why PollicinoNet fits

It naturally separates a compact `SEMANTIC` event from an `EXACT` evidence object. The event can carry a scoped coordinate for the raw evidence, which is fetched later only when policy and bandwidth permit. Authoritative records remain exact; the AI output is explicitly a prediction, not ground truth.

## Possible bearers

- **LoRa:** event class, confidence bucket, timestamp window, evidence coordinate and priority;
- **BLE/Wi-Fi:** nearby raw-evidence or model exchange;
- **Internet:** later retrieval and model update;
- **physical transport:** raw evidence or model cache can be carried offline.

No PHY change is required or proposed.

## What we can test now in software

- generate synthetic event/evidence pairs;
- compare raw-data cost with compact event descriptors;
- test `SEMANTIC` event + `EXACT` evidence linkage;
- simulate false positives, reclassification and expired evidence;
- verify that a later exact fetch resolves to the expected content hash;
- measure scarce-link TRC, event latency, evidence-fetch rate and cache hit rate.

## What requires real hardware

- an edge device able to run a tiny model or delegate inference to a nearby phone/PC;
- real sensor/camera input using non-personal test scenes;
- measured end-to-end event latency and LoRa packet delivery.

The current LoRa PHY remains unchanged; model execution is an application/edge concern.

## Privacy / security

Do not use face recognition, biometric classification or covert monitoring. Raw evidence should remain local by default and require explicit authorization for retrieval. A model result can leak sensitive information even if the raw sample is not transmitted, so event schemas must be privacy-reviewed.

## Difficulty

**High.** The networking primitives are manageable, but safe model selection, semantic/exact separation and evidence lifecycle need careful design.
