# UC-057 — Model-to-Data Edge Inference Courier

## Idea

Instead of moving private/raw data toward a central AI service, move a **small, signed inference request and exact model/task identity toward the node that already holds the data**, run the analysis locally, and return only an allowed compact result.

In short:

```text
bring the model/task to the data
not the data to the model
```

This is request-driven analysis, not federated training.

## Problem solved

Some edge nodes may hold data that are too large, too private or too expensive to move: sensor windows, local image batches, document collections or other protected observations.

A conventional pipeline uploads the raw data to a central model. In a sparse network that may be impossible; in a privacy-sensitive system it may also be undesirable.

PollicinoNet can instead carry an exact analysis request to the data-holder and later ferry back a bounded result.

Examples:

- classify a batch of public/synthetic sensor windows without exporting them;
- ask a disconnected edge camera node for counts/categories rather than images;
- run a small quality/anomaly detector on a local dataset and return only flagged object hashes;
- execute a safe statistic/model on consented DNA/DNATrace-like synthetic data while leaving row-level data local;
- ask a Raiatea node for a tightly scoped classification distinct from free-form RAG.

## Actors / nodes

- requester/analyst node;
- data-holding edge node;
- student relay/store-and-forward nodes;
- model/artifact cache nodes;
- optional school server;
- optional authorization/credential source;
- optional UC-033 rich-bearer handoff path.

## Why PollicinoNet fits

The request and result can be tiny while model/data artifacts stay local or move only when explicitly needed.

- **DISCOVERY:** `inference capability available`, `model version available`, `job pending`, `result ready`;
- **EXACT:** request ID, model hash/version, input selector, allowed output schema, execution limits, policy/authorization and result hash;
- **SEMANTIC:** labels such as `anomaly-check` or `object-count`, never enough to authorize execution by themselves.

If the data node lacks the model, UC-024/UC-004 can locate it and UC-033 can move it over Wi-Fi/BLE. LoRa remains the compact control plane.

This differs from:

- **UC-014:** generic opportunistic compute exchange;
- **UC-016:** federated adapter/training rounds;
- **UC-007:** autonomous edge event scouting;
- **UC-046:** source-bound document/RAG answer capsules.

UC-057 specifically studies **request-driven analysis at the data location with constrained outputs**.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** inference request manifest, model/data capability IDs, job state, compact result metadata and result-ready notice;
- **BLE:** nearby model/result artifact exchange;
- **Wi-Fi/LAN:** model distribution, optional exact evidence retrieval and detailed logs;
- **Internet:** optional model source or ordinary fast path;
- **physical transport:** a relay carries model artifacts, requests and later results between disconnected sites.

## What we can test now in software

Use a tiny public/synthetic dataset and a small deterministic model first.

Implement:

- canonical `InferenceRequest` with exact model hash, task type and input selector;
- allow-listed model/runtime combinations only;
- output schema that explicitly limits what can leave the data node;
- local execution quota for CPU/RAM/time;
- duplicate/reordered request delivery without duplicate side effects;
- stale/wrong model rejection;
- result bound to request ID, model hash and input snapshot/version;
- requester receives only aggregate/classification output by default;
- optional exact evidence retrieval as a separate authorized step;
- negative test where a malicious request asks for row-level/raw output;
- negative test where model provenance/signature is invalid;
- delayed model acquisition through UC-024/UC-033;
- compare `move raw data` bytes versus `move request + model if missing + bounded result` bytes on the same synthetic workload;
- metrics: job turnaround, bytes per bearer, model-cache hit, rejected-output requests, stale-work count and result/evidence delay.

A key invariant is:

> remote analysis authority is narrower than arbitrary code execution: only approved models/tasks and approved output schemas may run against protected local data.

## What requires real hardware

- 3–4 Pollicino nodes;
- one laptop/Raspberry Pi/edge computer holding a local public/synthetic dataset;
- one requester that cannot directly reach it;
- one moving relay;
- a small real local inference workload;
- LoRa request/result metadata plus optional Wi-Fi/BLE model handoff;
- measured end-to-end job latency, contact usage and actual compute cost on the target device.

Do not use personal biometric/health/student-sensitive data for the first field tests.

## Messina teaching scenario

Place a small edge node in one disconnected group with a synthetic environmental dataset collected locally. A student in another group asks:

```text
model = exact tiny-classifier hash M
input = batch B17
output = class counts + flagged sample hashes only
```

A relay carries the request from `Rometta/Venetico` toward the data node. The model is already cached locally, so the raw batch never moves. A later relay returns the compact result.

A second experiment deliberately removes the model from the edge node so the network must first discover and ferry the exact model artifact over a richer bearer. The class compares bytes and turnaround against simply exporting the whole dataset.

## Privacy / security

Moving computation to data reduces raw-data movement but does not automatically make the result safe.

- authorize every analysis request;
- prohibit arbitrary code in the first profile;
- allow-list model/runtime/output schema;
- verify exact model identity/signature;
- impose local compute and storage quotas;
- treat output disclosure as a policy decision, not as a model choice;
- reject requests that attempt to recover raw rows/images through an overly detailed output;
- keep audit logs of request, model, input snapshot and released result;
- use public/synthetic data until disclosure controls are understood;
- do not claim formal differential privacy unless such a mechanism is explicitly implemented and measured.

## Difficulty

**High.** The network objects are compact; the difficult part is sandboxed execution, model provenance, data-version binding and output-disclosure control.

## Research signal

DataSHIELD uses the principle **“take the analysis to the data, not the data to the analyst”**: commands execute at data-holding sites and only controlled summary outputs return, while individual-level data remain server-side. PollicinoNet can explore a much smaller delay-tolerant edge version of that architectural principle using public/synthetic data first.

References:

- https://datashield.org/about/
- https://datashield.org/
