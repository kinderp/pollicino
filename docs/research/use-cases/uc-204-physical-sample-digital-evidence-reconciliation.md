# UC-204 — Physical Sample and Digital Sensor-Evidence Join

## Problem and concrete scenario
A school group collects a **safe, supervised** water or soil demonstration sample while nearby sensors record temperature, turbidity or moisture. The sample physically reaches a different classroom before the sensor logs arrive. Incorrectly matching a later lab result to the wrong sample produces a plausible but false scientific conclusion. We need to join **physical sample identity** with delayed digital observations, including uncertain capture time and incomplete provenance.

## Actors / nodes
Student sampling team under teacher supervision, labeled demonstration container, portable sensor board, LoRa relay/store-and-forward nodes, laboratory teacher and data reviewer. Messina scenario: a classroom-made water sample is carried between two school checkpoints while synthetic/bench sensor traces take a separate LoRa+Wi-Fi route; outdoor water sampling only with permissions and suitable safety procedures.

## Why PollicinoNet fits and precise contract
A `sample_manifest` contains random sample ID, coarse authorized site code (or bench source), collection-time *interval* with clock uncertainty, collection protocol hash, instrument/calibration IDs, sealed-container witness signatures and references to `observation_hash[]`. The sensor records and later `lab_result` may travel over different paths. A join is marked `MATCHED_VERIFIED`, `AMBIGUOUS`, `MISSING_SOURCE`, `SAMPLE_INTEGRITY_UNKNOWN` or `REJECTED`—never silently auto-matched by timestamp alone.

## Bearers
- **LoRa:** tiny sample ID, manifest digest, outstanding references and join result.
- **BLE:** sensor download at collection or laboratory.
- **Wi-Fi/Internet:** full time series, methods, images, signed lab report.
- **Physical transport:** the *actual labeled demonstration sample*, plus optional SD/USB media; no biological or hazardous materials.

## Software-only experiment (proposed; not run)
Simulate 30 samples, swapped labels, two clocks drifting, duplicates, wrong calibration, sample ID collision attempts, late lab results and missing sensor evidence. Compare naive nearest-timestamp join against exact manifest-based join. Record wrong joins (critical), unresolved joins, time-to-resolution, evidence bytes and false confidence. Ground truth is artificially defined; not a claim of environmental accuracy.

## Physical test and measurements needed
Four LoRa boards, two low-cost sensors, two supervised laboratory checkpoints and harmless labeled water cups. Separate the sample and digital data routes deliberately, introduce one known label swap and delayed data. Verify exact identities and measure actual arrival/contact times, sensor calibration and mismatch detection; do not infer pollutant concentration, potable safety or ecological health.

## Privacy, security, difficulty
**Medium–high.** No names of minors, precise home coordinates or health information. Signed manifests/hashes protect digital integrity but **cannot prove that the liquid in the container is unchanged**: use witnessed seals, protocol records and explicit uncertainty. Encrypt nonpublic sample details; authenticate laboratory reviewers.

## Distinction from existing catalog
UC-042 tracks physical asset custody, UC-171 compares water-quality instruments, UC-187 coordinates reproducible science, and UC-125 joins time series. **UC-204 reconciles one physical specimen with independently delayed digital evidence and exposes ambiguous identity**.

## Guardrails
Educational protocol only; never an official water-quality, forensic or food-safety determination. Frozen LoRa PHY/MAC unchanged; all physical claims require real validation.