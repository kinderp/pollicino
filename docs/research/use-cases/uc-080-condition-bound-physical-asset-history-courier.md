# UC-080 — Condition-Bound Physical Asset History Courier

## Idea

Bind a moving physical asset to a delay-tolerant history of **temperature, humidity, shock or other condition evidence**, so that the asset can travel through disconnected custody points while compact alerts move immediately and the complete sensor log catches up later.

A cold-chain style scenario is the clearest example, but the first experiments should use only harmless school objects: an insulated box with an ice pack, a box of electronics, 3D-print filament or a sensor kit. No medical, food-safety or regulated logistics claim is made.

## Problem solved

UC-042 records who had an asset. UC-031 records calibration provenance. UC-003 ferries sensor data. A missing piece is the **continuity of condition history for an asset that itself is moving**.

Examples:

- a box should remain within a chosen teaching temperature band;
- a fragile kit should flag a shock event;
- humidity-sensitive material should record prolonged exposure;
- one custodian receives the asset before the previous full sensor log has synchronized;
- a compact alert says `temperature excursion occurred`, while the exact time series is still on another node.

The receiver must be able to distinguish `condition OK`, `known excursion`, `log incomplete` and `unknown` rather than silently treating missing data as safe.

## Actors / nodes

- physical training asset or container;
- attached/companion sensor node;
- student/teacher custodians;
- relay/store-and-forward nodes;
- school verifier/inventory node;
- optional UC-042 custody ledger;
- optional UC-031 calibration provenance source;
- optional UC-022 multi-witness corroboration.

## Why PollicinoNet fits

Condition evidence naturally has two layers:

- a **small urgent summary** that fits a scarce control bearer;
- a **larger exact evidence log** that can arrive later.

Use the information contracts as follows:

- **DISCOVERY:** asset condition update available, log gap, excursion class, evidence holder;
- **EXACT:** asset ID, sensor ID, calibration version, sample-range hash, excursion event hash, custody-event link and log segment identity;
- **SEMANTIC:** labels such as `cold`, `humid`, `shock`, useful for human triage but never a replacement for the measured data.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** asset ID, current state, excursion alert, log-range summary, missing-range request and exact hashes;
- **BLE:** nearby sensor sync and moderate log retrieval;
- **Wi-Fi/LAN:** full time series, photos and calibration documents;
- **Internet:** optional later synchronization with an inventory/analysis service;
- **physical transport:** the asset and its sensor physically move between disconnected areas.

## What we can test now in software

Generate synthetic time-series logs and link them to a synthetic custody chain.

Test at least:

- normal condition history;
- one short excursion;
- one long excursion;
- missing log interval;
- delayed segment arriving out of order;
- duplicated log segment;
- sensor reboot with a new boot/session ID;
- stale calibration metadata;
- two sensors disagreeing on the same interval;
- custody handover that occurs before all prior evidence arrives;
- forged `all-clear` summary that does not match the exact log hash;
- retention policy where high-rate samples expire but signed excursion summaries remain.

Useful states should be explicit:

```text
OK_VERIFIED
EXCURSION_VERIFIED
INCOMPLETE_EVIDENCE
CALIBRATION_UNKNOWN
CONFLICTING_EVIDENCE
```

Useful metrics include time-to-excursion-awareness, evidence completion delay, missing-range count, bytes per bearer, custody-to-evidence lag and false `OK` decisions prevented by the explicit unknown state.

## What requires real hardware

A safe first experiment needs only:

- 3–5 LoRa nodes;
- a harmless physical box/container;
- one or two temperature/humidity sensors;
- optional simple accelerometer for shock events;
- several controlled handovers;
- intentional network partitions;
- a Wi-Fi/BLE retrieval step for the full log.

A useful teaching setup is an insulated lunch-style box with a reusable ice pack and no food/medicine. Students can deliberately open it for different durations and compare the compact excursion event with the later exact sensor log.

Do not claim food safety, pharmaceutical compliance, cold-chain certification or sensor accuracy beyond what is actually calibrated and measured.

## Messina teaching scenario

Prepare a training container at school and give it an exact asset ID. It passes through controlled checkpoints representing `Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora` or simply through separated school groups before any province-wide trial.

The attached sensor records temperature/humidity locally. One group deliberately creates a harmless condition excursion. The next custodian may receive only a compact PollicinoNet alert before the full log arrives through a later student relay.

At the end, the class reconstructs both:

- the custody chain;
- the exact condition timeline and any gaps.

The important lesson is that **missing evidence is not the same as evidence of normal conditions**.

## Privacy / security

Condition history can reveal logistics/movement patterns even when the payload is not personally sensitive.

- use coarse checkpoint labels rather than home coordinates;
- separate private custodian identity from public asset-condition state;
- authenticate excursion summaries and exact log manifests;
- link evidence to the exact asset/sensor identity;
- preserve calibration version and boot/session boundaries;
- reject silent gap filling;
- encrypt detailed logs if they include sensitive location or operational metadata;
- use only synthetic/harmless assets in student experiments.

## Difficulty

**Medium–High.** The sensor logging is easy; the useful research work is continuity across custody changes, delayed evidence, gaps, calibration state and explicit handling of uncertainty.

## Why this is distinct from nearby use cases

- **UC-003:** collects sensor data from a mostly fixed remote source.
- **UC-031:** binds calibration/provenance to sensor measurements.
- **UC-042:** records physical custody handovers.
- **UC-080:** binds **continuous condition evidence to a moving physical asset** across delayed handovers and incomplete synchronization.

## Research signal

Cold-chain and rural logistics research continues to combine IoT condition sensing, traceability and resilience to connectivity disruption. A 2026 cold-chain logistics study explicitly combines environmental monitoring with outage-resilient traceability. PollicinoNet should use the domain only as a falsifiable teaching workflow and should not inherit compliance or reliability claims from external systems.

Reference:

- https://doi.org/10.1117/12.3115495
