# UC-145 — Late AI Training Contribution Handling

## Problem solved
A training result can return after the shared model has already changed. The system should know which model version produced that result before deciding whether to use it.

## Actors / nodes
Training laptops, coordinator, student relay nodes, result cache and evaluator.

## Why PollicinoNet fits
The metadata is small: base-model ID, data-snapshot ID, result ID and age/epoch. Large AI artifacts stay on richer bearers. The frozen LoRa PHY is unchanged.

## Possible bearers
LoRa for compact metadata; BLE for small artifacts; Wi-Fi/LAN for larger model results; Internet when available; physical transport for large files.

## What we can test now in software
Use public datasets and intentionally delay some training results. Compare immediate use, age-limited use and recomputation. Record the age of each contribution and the resulting experiment metrics.

## What requires real hardware
Use 4–6 LoRa boards plus at least three laptops. Keep one compute client disconnected, then let its result return after newer training epochs exist.

## Messina teaching scenario
Groups in Messina, Villafranca, Rometta/Venetico and Spadafora can produce results at different times and relay the small contribution metadata through the student network.

## Privacy / security
Use public or synthetic data first. Keep exact model/data identifiers with each contribution and avoid associating model quality with student identity.

## Difficulty
**High.**

## Why this is distinct
UC-016 moves federated-learning artifacts; UC-145 focuses specifically on deciding what to do when a legitimate contribution returns late relative to the current model state.

## Research signal
Asynchronous federated learning research in 2026 continues to treat model-update staleness as a central design problem.

References:
- https://doi.org/10.3233/FAIA251139
- https://doi.org/10.1016/j.infsof.2026.108177
