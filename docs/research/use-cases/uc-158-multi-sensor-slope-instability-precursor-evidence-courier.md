# UC-158 — Multi-Sensor Slope-Instability Precursor and Evidence Courier

## Problem solved
A remote environmental node may observe slow changes in moisture, tilt or vibration while lacking continuous Internet access. Instead of forwarding a complete stream, it can first emit a compact trend/event capsule and make richer evidence available later.

This is an educational sensing experiment, not a certified hazard-warning system.

## Actors / nodes
Environmental sensor nodes, an optional local edge rule, student relay/store-and-forward nodes, a school collector, optional witness sensors and a reviewer.

## Why PollicinoNet fits
The first useful state is compact: campaign ID, sensor epoch, coarse trend class, uncertainty, evidence-range ID, evidence hash and expiry. LoRa can carry that control state while high-rate series and images wait for BLE, Wi-Fi/LAN or physical transport. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: trend/event state, update/clear state and evidence locator.
- BLE: maintenance and short local evidence.
- Wi-Fi/LAN: detailed time series and photos.
- Internet: optional later analysis.
- Physical transport: long histories.

## Software test now
Generate synthetic normal and abnormal multi-sensor traces, missing samples, contradictory sensors and clock uncertainty. Compare raw streaming, fixed-threshold events and multi-sensor trend capsules. Measure synthetic false alarms, missed synthetic events, delay to review and bytes moved.

## Real hardware
Use 4–6 boards and a safe tabletop rig with moisture, IMU/tilt and vibration inputs. Induce only harmless known changes. Any field claim about sensing quality, radio coverage, battery life or real hazard detection requires separate physical measurements.

## Messina scenario
Student groups across Messina, Villafranca, Rometta/Venetico and Spadafora carry compact observation state between disconnected sensor islands. A collector requests the exact evidence window only when a suitable rich-bearer contact becomes available.

## Privacy / security
Use school-authorized sites or bench data, avoid private-property coordinates, authenticate event/update state and keep raw sensor observation separate from human interpretation.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-027 is post-event vibration logging, UC-086 is event localization and UC-144 is catchment rise-rate. UC-158 focuses on slow multi-sensor slope trends with delayed evidence.

## Research signal
LoRa-based rockfall and landslide monitoring remains active in 2026. External results are design references only and are not PollicinoNet performance claims.
