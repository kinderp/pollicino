# UC-164 — Intermittent Split-Inference Activation Courier

## Problem solved
A small edge device may be unable to run an entire AI model, while sending the full raw input to a stronger machine may be inefficient. Split inference runs an initial model segment locally and sends an intermediate activation to another worker that completes the inference.

## Actors / nodes
Edge sensor/device, model-prefix runner, relay/store-and-forward nodes, stronger edge/workstation worker, result consumer.

## Why PollicinoNet fits
The control state is small: input hash, exact model hash, cut-layer ID, activation hash, codec version, expiry and result status. LoRa can carry that state while activations and model files use richer bearers. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: job descriptor, model/cut identifiers and result status.
- BLE/Wi-Fi/LAN: intermediate activations and returned result.
- Internet: optional remote inference worker.
- Physical transport: large model variants or activation batches.

## Software test now
Compare fully local inference, raw-input offload, several split points and compressed activations. Inject delayed contacts, duplicates, model-version changes and expired jobs. Measure bytes, emulator completion time, result equivalence and recomputation.

## Real hardware
Use 4–6 boards plus one constrained compute device and one stronger laptop/workstation. Run the prefix locally, transfer the activation during a later rich-bearer contact and complete the inference remotely.

## Messina scenario
A node in one school island performs the model prefix; a stronger machine in another island completes the job after the activation is relayed. This requires no permanent cloud path.

## Privacy / security
Intermediate activations are not automatically anonymous. Treat them as sensitive derived data, encrypt them in transit and bind them to exact input/model provenance.

## Difficulty
**High.**

## Distinct from existing cases
UC-057 moves a model toward local data, UC-078 offloads a whole task and UC-154 escalates uncertain cases. UC-164 partitions one inference pipeline and ferries the intermediate representation.

## Research signal
Split computing and DNN partitioning remain active edge-AI research areas in 2026. External performance results are design references only.
