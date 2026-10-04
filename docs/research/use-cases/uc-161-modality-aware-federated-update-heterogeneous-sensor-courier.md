# UC-161 — Modality-Aware Federated Update Courier for Heterogeneous Sensors

## Problem solved
Different edge clients may have different sensors. One group may have environmental sensors, another an IMU, another camera-derived public features. A generic learning round can waste communication if it treats every client as identical.

UC-161 keeps each delayed learning contribution bound to its modality set, base-model version and experiment snapshot.

## Actors / nodes
Heterogeneous sensor clients, student relay nodes, a learning coordinator and evaluator.

## Why PollicinoNet fits
The capability metadata are small: modality set, model version, experiment snapshot, update identifier and compatibility state. LoRa carries those small descriptors while larger model data stays on Wi-Fi/LAN or physical transport. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: capability and update descriptors.
- BLE: small nearby exchanges.
- Wi-Fi/LAN: larger model data.
- Internet: optional coordinator.
- Physical transport: large checkpoints.

## Software test now
Use a public multi-sensor dataset and emulate clients with different modality subsets. Compare one-size-fits-all aggregation with modality-aware grouping. Add long delays, missing modalities and clients that reconnect late. Measure model quality, transferred bytes and compatible versus rejected contributions.

## Real hardware
Use 4–6 LoRa boards and deliberately different sensor kits. Different student groups can expose different modality sets. Any communication or energy benefit must be measured on the selected hardware.

## Messina scenario
Groups in Messina, Villafranca, Rometta/Venetico and Spadafora operate different sensor kits. Student relays move the small capability and update descriptors; rich bearers move the larger learning artifacts.

## Privacy / security
Start with public or synthetic datasets and pseudonymous experiment IDs. Avoid broadcasting detailed device capability more widely than needed.

## Difficulty
**High.**

## Distinct from existing cases
UC-016 covers generic federated adapter rounds, UC-145 late training contributions and UC-157 delayed teacher guidance. UC-161 focuses on heterogeneous sensor modalities.

## Research signal
Recent 2026 work studies federated learning where IoT clients differ in available modalities and compute resources.
