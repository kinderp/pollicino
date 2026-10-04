# UC-160 — Intermittent AI Model Canary Rollout and Rollback Courier

## Problem solved
A candidate AI model can work in offline tests but fail on a particular edge device because of memory limits, runtime incompatibility or latency regression. Updating every disconnected node at once increases the rollout risk.

UC-160 studies a staged rollout: a small canary cohort receives an exact candidate model first, returns compact health evidence, and only then can the rollout expand, pause or roll back.

## Actors / nodes
Model publisher, canary devices, stable devices, student relay/store-and-forward nodes, evaluator and optional FARO evidence store.

## Why PollicinoNet fits
Rollout control is compact: exact model hash, runtime profile, rollout ID, cohort, previous stable model ID, health summary and decision state. LoRa can move this state while model weights move through Wi-Fi/LAN or physical storage. The frozen LoRa PHY remains unchanged.

## Bearers
LoRa for rollout state and health summaries; BLE for small configuration; Wi-Fi/LAN for models and evaluation bundles; Internet as optional registry; physical transport for large artifacts.

## What we can test now in software
Simulate 10–50 devices with intermittent contacts. Introduce an incompatible runtime, higher memory use, slower inference, changed output distribution and delayed health evidence. Compare all-at-once deployment with canary, pause and rollback.

## What requires real hardware
Use 4–6 LoRa boards plus at least two heterogeneous compute devices. Deliver the same candidate model to a canary subset and measure actual load success and inference latency before making performance claims.

## Messina scenario
Two devices in Rometta/Venetico form a canary cohort while devices in Messina, Villafranca and Spadafora remain on the stable model until promotion or rollback state is relayed.

## Privacy / security
Use public or synthetic evaluation data. Authenticate exact model hashes and rollout decisions. Keep the previous known-good model available for rollback. A small canary is not proof of general model safety.

## Difficulty
Medium–High.

## Distinct from existing cases
UC-038 evaluates model behavior, UC-069 stages firmware rollout and UC-085 negotiates model variants. UC-160 focuses on staged AI model deployment state across intermittent nodes.
