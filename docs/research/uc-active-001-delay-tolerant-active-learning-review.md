# UC-ACTIVE-001 — Delay-tolerant active-learning / expert-review ferry

Status: RESEARCH / SOFTWARE PROTOTYPE, candidate child of AI + CITSCI + ROBOT

## Problem

An edge model running on a sensor, robot or companion device may know that it is uncertain about a particular observation. The rich sample may be too large for LoRa and an expert or stronger model may be reachable only hours later at school/home.

The concrete question is:

> can the edge node carry only a compact uncertainty/query/reference now, obtain a human or stronger-model label later, and return that label to the originating model without requiring continuous connectivity?

This is distinct from `UC-FL-001`: FL exchanges model contributions/updates. ACTIVE exchanges **which examples need review and the resulting label/verdict**, potentially without sending any gradient or model update over PollicinoNet.

## Actors / nodes

- edge inference node or robot/companion device;
- student-carried Pollicino relay;
- teacher/expert/reviewer or stronger school/home AI service;
- local storage containing the rich sample;
- optional Raiatea/content resolver for authorized sample retrieval;
- experiment recorder tracking label value, delay and model generation.

## Why PollicinoNet fits

Active learning naturally produces small control objects:

- sample hash/reference;
- model generation/fingerprint;
- uncertainty score or reason code;
- requested label vocabulary;
- expiry/deadline;
- returned label/review state.

The large image/audio/dataset item can stay on local storage and be retrieved later over Wi-Fi/LAN using existing content/reference patterns. Store-carry-forward handles the query and label when no end-to-end path exists.

## Possible bearers

- LoRa: compact uncertain-sample query and returned label/verdict;
- BLE: edge device/robot to Pollicino relay handoff;
- Wi-Fi/LAN: rich sample retrieval and expert/strong-model review;
- Internet: optional remote review service if explicitly authorized;
- physical carry: student mobility transports the review request and answer between disconnected environments.

## What we can test immediately in software

Use a small public/synthetic classification task and a toy edge model. Compare:

1. no additional labels;
2. random sample review under the same label budget;
3. simple uncertainty-threshold review;
4. only later, richer selection if uncertainty sampling fails.

Model explicit delay:

```text
edge flags sample at generation G
query is carried for hours
review happens later
label returns when edge may already be at generation G+n
```

Measure:

- model accuracy/F1 improvement per reviewed sample;
- useful labels per LoRa/control byte;
- query-to-label round-trip delay;
- stale labels caused by model/schema changes;
- duplicate query suppression;
- expert label budget consumed;
- fraction of rich samples that never need to cross LoRa.

The first experiment can keep all rich samples local/in-memory and simulate only references.

## Messina student-network scenario

A citizen-science or robotics exercise produces harmless, public-domain observations. An edge model in a logical territorial cluster marks a few uncertain samples. A student carries their compact references to the school hub, where a teacher or workstation reviews them. The resulting labels are then carried back during a later school/territorial phase.

No face, voice, health or other sensitive classification should be used in the first pilot. Public plant/object/synthetic sensor categories are safer.

## What requires real hardware

Later hardware experiments require:

- actual on-device/companion inference latency and energy;
- capture/hash/reference generation cost;
- BLE/LoRa handoff timing;
- Wi-Fi retrieval of the rich sample;
- persistence across reboot;
- real label-return delay in a supervised pilot;
- measurement of whether the query traffic is small enough to be worthwhile on the actual contact windows.

HW-006 remains required for any LoRa capacity claim; model-inference energy needs a separate compute/energy gate.

## Privacy and security

- begin with public/synthetic data and non-sensitive labels;
- content references must obey authorization and rights constraints;
- do not expose rich samples over LoRa merely because a reference exists;
- bind every label to sample hash + model/schema generation;
- authenticate reviewer provenance where labels matter;
- reject replayed labels for a different sample/generation;
- treat human labels as fallible evidence, not cryptographic truth.

## Difficulty

**Medium-high.** The network objects are simple; the hard part is defining whether delayed labels still improve the application.

## Success / kill criteria

Continue if a simple uncertainty-based policy improves the toy/target model more per scarce communication/reviewer effort than random review and if delayed labels can be bound safely to the correct sample/model generation.

If delayed review is usually too stale, or rich sample retrieval dominates all cost, keep the use case as a negative result and do not add AI-specific network protocol features.

## Related-work note

Human-in-the-loop active learning and edge adaptation are established research areas. Recent work continues to study lightweight edge agents that request limited human labels under distribution shift. PollicinoNet's research question is narrower: whether **delay-tolerant transport of review requests/labels** is useful when the edge and reviewer are not continuously connected.

## Physical evidence boundary

No real edge-AI accuracy, energy, LoRa capacity or student-network benefit is claimed from the software prototype. The frozen LoRa PHY remains unchanged.