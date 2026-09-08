# UC-032 — Active-Learning Label Courier

## Idea

Let edge devices keep most raw data local, select only the **most uncertain or informative samples** for human review, and use PollicinoNet to ferry compact label requests and later the returned labels across intermittent connectivity.

The model does not need every raw sample to cross LoRa. LoRa is primarily the coordination/control bearer.

## Problem solved

Edge-AI systems often collect far more sensor/image/audio examples than a teacher, expert or annotator can review. Many samples are routine and add little value; a small uncertain subset may be much more useful for improving a model or dataset.

In an intermittently connected network the edge node can therefore ask:

```text
sample X is uncertain
model version = M
requested label schema = L
priority = P
```

A richer bearer or physical data mule later brings the exact sample to an authorized reviewer. The compact label result can return even through a scarce bearer if its size and measured conditions allow it.

## Actors / nodes

- edge-AI/sensor nodes generating candidate samples;
- student laptops/phones acting as relays;
- teacher/expert/annotator node;
- school dataset/model registry;
- optional stronger edge/server model used to rank uncertainty;
- optional multiple annotators for disagreement experiments.

## Why PollicinoNet fits

The useful network object is not the whole dataset but a small **review request** tied to exact evidence.

- **DISCOVERY:** sample/request ID, uncertainty bucket, model/schema version and availability of pending review;
- **EXACT:** exact sample hash, label-schema hash, annotator response, provenance and model version that generated the request;
- **SEMANTIC:** labels/classes and human explanations, clearly separated from the raw evidence object.

LoRa can carry compact label requests, priorities and returned labels. BLE/Wi-Fi/LAN/Internet or physical carry moves images, audio or other large evidence.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** label-request ID, uncertainty/priority, model/schema version, compact label/receipt where appropriate;
- **BLE:** nearby evidence exchange;
- **Wi-Fi/LAN:** image/audio/sample transfer and model/dataset synchronization;
- **Internet:** optional connection to a central annotation tool;
- **physical transport:** student node carries selected evidence from offline edge nodes to an annotator.

## What we can test now in software

- use a small public or synthetic dataset;
- train a tiny baseline classifier or use deterministic mock confidence scores;
- select only the top-N uncertain/informative samples for review;
- represent each review request as `sample hash + model version + schema version + priority`;
- simulate partitions and delayed delivery to the annotator;
- return labels out of order and after the originating model has changed;
- prove that a label for schema/model/sample mismatch is rejected or explicitly migrated;
- test duplicate requests and persistent de-duplication;
- simulate two annotators who disagree and preserve both labels/provenance instead of silently majority-voting;
- compare random labeling with uncertainty-driven selection by annotation count and downstream model/dataset utility, without attributing any gain to LoRa;
- integrate UC-024 for exact evidence retrieval and UC-022 for multi-witness/annotator disagreement;
- treat UC-016 separately: UC-032 moves **label tasks/results**, while UC-016 coordinates model/adapter updates.

A core invariant is:

> a semantic label is meaningful only when bound to the exact sample and label-schema version it refers to.

## What requires real hardware

The protocol can be validated deeply before hardware. Later experiments may use:

- 3–4 PollicinoNet nodes;
- one small camera/IMU/environmental sensor or a laptop replaying a fixed public dataset;
- one disconnected edge node that queues uncertain samples;
- a moving student relay;
- one annotator node;
- measured delay from label request to evidence retrieval to returned label;
- real LoRa control messages and richer-bearer evidence handover.

Start with public/synthetic data. Do not collect identifiable student images/audio merely to make the experiment more realistic.

## Messina teaching scenario

A class can distribute a harmless public image or sensor dataset among several nodes. Each node runs the same tiny model but sees a different subset. It generates a few uncertain sample IDs. Students carrying relay boards move between network islands and bring those label requests to a teacher/annotator node.

The teacher labels selected samples; the label records later travel back to the originating dataset replicas. The class can then inspect exactly which sample/version each label affected and whether delayed labels became stale after a model/schema change.

A later environmental version could use non-personal sensor anomalies from school/rural nodes around the province rather than images of people.

## Privacy / security

Raw samples can contain personal or sensitive information. Therefore:

- start with public/synthetic datasets;
- send only minimal metadata over discovery;
- encrypt exact evidence in transit/storage;
- authorize who may retrieve a sample and who may label it;
- keep annotator provenance separate from real-world identity when possible;
- never assume federated/local processing automatically guarantees privacy;
- define retention/deletion rules for evidence once the labeling task is complete.

A malicious label is a data-poisoning vector, so labels need authenticated provenance and review policy.

## Difficulty

**Medium–High.** The basic queue is easy; the interesting work is version binding, evidence retrieval, disagreement/provenance and safe integration with an actual model/dataset pipeline.

## Research signal

Recent work continues to study selective relabeling, active-learning-style data selection and intermittent edge/federated learning. These directions reinforce the idea that scarce human/network resources should be spent on informative samples rather than indiscriminate dataset transfer.

References:

- https://doi.org/10.1007/s41060-025-00751-w
- https://doi.org/10.1007/s11276-025-03903-9
- https://www.nature.com/articles/s41598-026-59680-8
