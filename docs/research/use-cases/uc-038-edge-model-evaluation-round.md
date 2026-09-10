# UC-038 — Edge Model Evaluation Round

## Idea

Use PollicinoNet to coordinate **repeatable AI/model benchmarks across disconnected or intermittently connected student devices** without trying to send whole models or datasets over LoRa.

A compact signed benchmark manifest identifies the exact model, dataset/task set, runtime and metrics. Each participating node runs the benchmark locally when it has the required artifacts, stores the raw result as an exact object, and later returns a compact result summary through store-and-forward.

## Problem solved

When several students have different laptops, Raspberry Pi-class devices or local AI runtimes, it is hard to answer questions such as:

- which model actually runs acceptably on which hardware?
- did a runtime/model update improve or regress latency or memory use?
- are two reported scores comparable, or were they produced from different prompts/model revisions?
- can a benchmark campaign finish even when devices are not online at the same time?

UC-038 turns benchmark work into a delay-tolerant round rather than a live centrally connected job.

## Actors / nodes

- student laptops or edge-AI devices;
- optional Raspberry Pi / Jetson-class teaching nodes;
- school benchmark coordinator;
- student LoRa nodes acting as relay/store-and-forward carriers;
- optional NAS/server that already stores model/dataset artifacts;
- optional Raiatea node holding benchmark instructions or evaluation documents.

## Why PollicinoNet fits

The useful control information is compact and exact:

- **DISCOVERY:** `node N can run benchmark family B and may already hold model M`;
- **EXACT:** benchmark manifest hash, model hash/version, dataset/eval-set hash, runtime version, result object hash;
- **SEMANTIC:** labels such as `small Italian model`, `coding benchmark` or `classroom assistant`, never a substitute for exact identity.

The large model/dataset stays on local storage or moves through UC-004/UC-024/UC-033 over Wi-Fi/LAN/Internet/physical carry. LoRa only coordinates the round and carries compact result summaries when appropriate.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** benchmark-round advertisement, participant status, exact manifest/root hashes, compact metrics and completion acknowledgement;
- **BLE:** short-range result synchronization or small manifests;
- **Wi-Fi/LAN:** model/dataset/result artifact transfer;
- **Internet:** optional artifact acquisition or external evaluator when policy permits;
- **physical transport:** USB/SSD/student-carried device for large model/dataset movement.

## What we can test now in software

Create a canonical `BenchmarkRound` object with fields such as:

```text
round_id
benchmark_manifest_hash
model_hash
runtime_id + version
dataset_hash
hardware_profile_hash
required_metrics
result_schema_version
expiry
```

Then simulate or run locally:

- 3–5 heterogeneous virtual/device profiles;
- duplicate round delivery;
- one node missing the model;
- one node with the wrong model revision;
- one stale runtime;
- late benchmark completion after a network partition;
- result replay from an earlier round;
- result schema mismatch;
- exact raw-result object plus compact signed summary;
- comparison only when manifest/model/runtime bindings are compatible.

Useful metrics include round completion rate, turnaround time, bytes carried on scarce vs rich bearers, stale-result rejection and benchmark reproducibility.

## What requires real hardware

- at least two genuinely different compute devices;
- real local inference/runtime measurements;
- measured latency/throughput/memory/energy only when instrumentation supports it;
- repeated runs to distinguish measurement noise from real model/runtime differences;
- real LoRa relay of benchmark control/result metadata if we want to validate the complete PollicinoNet path.

Simulation must not be presented as evidence of physical model performance or radio behavior.

## Messina teaching scenario

Give several students the same small public benchmark pack but different local model/runtime combinations. Some students can run the benchmark at home, others at school, and some devices may not have Internet.

Their PollicinoNet nodes exchange only the exact round identity and compact result envelopes. A student travelling between Rometta, Spadafora, Venetico, Milazzo or Messina can physically carry pending result objects or rich-bearer opportunities while LoRa maintains the control-plane state.

At school the coordinator can build a reproducible matrix:

```text
exact model × exact runtime × hardware profile × exact benchmark
```

without assuming all nodes were online together.

## Privacy / security

- use public/synthetic evaluation data first;
- never include private prompts in a benchmark round unless explicitly authorized and encrypted;
- bind every result to exact model/runtime/dataset identities;
- sign result envelopes when provenance matters;
- do not trust self-reported hardware or scores blindly for high-stakes claims;
- retain raw result objects where independent verification is needed;
- keep cloud evaluation optional and policy-gated.

## Difficulty

**Medium–High.** The benchmark itself is straightforward; the harder part is making cross-device results reproducible, comparable and delay-tolerant while keeping model/dataset transfer off the scarce bearer.

## Research signal

A May 2026 study benchmarked 25 open-source language models on Raspberry Pi-class and laptop hardware and explicitly measured efficiency and pedagogical quality, showing how strongly deployment behavior can vary across edge devices. Independent 2026 benchmark harness work also emphasizes pinned runtimes, raw result retention and repeatable measurements on real devices.

References:

- https://arxiv.org/abs/2605.03111
- https://github.com/john-rocky/edge-llm-bench
