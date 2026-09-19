# UC-085 — Compatible AI Model Variant Negotiation and Distribution

## Idea

Let a node ask for **an AI capability it can actually run**, rather than hard-coding one exact model file in advance.

A requester advertises a bounded device/runtime profile and a task requirement. Nearby caches may hold several exact variants of the same model family: different quantizations, runtimes, context sizes or hardware targets. PollicinoNet first resolves the request to one exact compatible artifact, then transfers that artifact over a richer bearer.

## Problem solved

UC-004 distributes AI artifacts, but assumes the desired artifact is already known. In a heterogeneous student network that assumption often fails:

- one laptop can run a 7B quantized model while a Raspberry Pi cannot;
- one device supports ONNX, another GGUF, another only a smaller model;
- two caches hold different quantizations of the same logical model;
- a requested variant may fit storage but exceed RAM;
- the model may be technically compatible but disallowed by usage policy;
- a stale capability advertisement may select a model that no longer fits because local memory is occupied.

The problem becomes **semantic capability request → exact artifact resolution → verified transfer**.

## Actors / nodes

- requester device: laptop, Raspberry Pi, lab PC or later a constrained edge node;
- student relay/store-and-forward nodes;
- AI artifact caches;
- optional model registry/Raiatea metadata node;
- optional UC-038 benchmark/evaluation evidence;
- optional UC-076 usage-policy/licensing envelope;
- optional UC-004 artifact distribution path.

## Why PollicinoNet fits

The negotiation metadata is small even when model files are huge.

- **DISCOVERY:** task family, runtime class, rough RAM/storage/accelerator capability, available model-family variants;
- **SEMANTIC:** `text-embedding`, `small-chat`, `vision-classifier`, minimum quality tier or context requirement;
- **EXACT:** chosen model artifact hash, model version, quantization, tokenizer hash, runtime/version, policy ID and compatibility manifest.

LoRa should never carry model weights. It can carry compact capability and availability information, then bootstrap Wi-Fi/LAN/BLE for the exact artifact.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** capability summary, model-family/variant availability, request ID, selected exact artifact identity, policy/version status;
- **BLE:** nearby manifest exchange and small configuration files;
- **Wi-Fi/LAN:** model weights, tokenizer, runtime bundle and benchmark evidence;
- **Internet:** optional retrieval from the authoritative registry when reachable;
- **physical transport:** SSD/laptop/cache physically carries large model variants between islands.

## What we can test now in software

Create a synthetic `DeviceProfile`:

```text
device_id
runtime_allowlist
architecture
ram_budget
storage_budget
accelerator_class
max_artifact_size
supported_quantization_classes
policy_context
```

and a `ModelVariantManifest`:

```text
model_family
artifact_hash
model_version
format
quantization
runtime_constraints
minimum_ram
artifact_size
context_limit
tokenizer_hash
license_policy_id
benchmark_evidence_refs
```

Then implement a deterministic resolver and test:

- several variants satisfy the request;
- no variant fits RAM;
- only a policy-forbidden variant fits;
- stale device capability causes a failed handoff;
- model file arrives without its exact tokenizer/runtime metadata;
- two caches advertise the same exact hash;
- one cache advertises a corrupted artifact;
- a newer model version is available but exceeds constraints;
- requester accepts a lower-cost fallback only if its policy explicitly allows that fallback;
- model family is requested semantically, but execution begins only after exact artifact resolution and hash verification.

Useful metrics include resolution success rate, false-compatible selections, negotiation bytes, time-to-first-compatible-provider, duplicate transfer, artifact-verification failure and fallback frequency.

A useful invariant is:

> semantic model selection may be flexible; execution must bind to one exact model/runtime/tokenizer identity.

## What requires real hardware

The first experiment can use common lab hardware rather than LoRa-capable AI accelerators:

- one normal laptop;
- one Raspberry Pi or weaker PC;
- 3–4 LoRa control nodes;
- two caches with deliberately different small public model variants;
- Wi-Fi/LAN for model transfer.

Use tiny public models or synthetic artifacts first so the experiment is about negotiation correctness, not benchmark performance.

Later, the same mechanism can use real on-device LLM or vision variants.

## Messina teaching scenario

Prepare three islands: `school`, `Rometta/Venetico`, `Spadafora`. The school cache holds three variants of the same educational model family. A student node away from school requests `small-chat` with a known RAM/runtime budget but does not know which artifact exists.

A relay transports the request. The cache replies with one exact compatible manifest. The weights later move by Wi-Fi when the devices meet. A second run deliberately changes the requester profile so the first choice becomes invalid and the resolver must choose another exact variant or return `NO_COMPATIBLE_ARTIFACT`.

## Privacy / security

Capability metadata can fingerprint a device.

- advertise only coarse capability classes where possible;
- avoid exposing exact hardware serials or unnecessary installed-software inventories;
- model availability does not imply authorization to redistribute it;
- enforce UC-076 usage policy/licensing decisions separately;
- verify exact artifact/tokenizer/runtime hashes before execution;
- do not trust benchmark labels supplied by an unknown cache without provenance;
- never silently substitute a different model when an exact safety/quality requirement was requested;
- treat model metadata and manifests as signed/authenticated where they affect execution.

## Difficulty

**Medium–High.** Basic matching is straightforward. The difficult parts are exact compatibility semantics, stale device state, policy constraints and preventing semantic fallback from becoming silent artifact substitution.

## Why this is distinct from nearby use cases

- **UC-004:** moves a known model/dataset artifact.
- **UC-038:** measures model/runtime performance on heterogeneous devices.
- **UC-057:** sends inference work toward data rather than moving private data.
- **UC-076:** constrains artifact usage rights.
- **UC-085:** resolves a **capability-level request into one exact runnable model variant** under device and policy constraints.

## Research / implementation signal

On-device AI increasingly depends on matching model configuration and quantization to heterogeneous resource budgets. A 2026 systematic study evaluates quantized LLM variants against memory, compute and power constraints, while the 2026 SWEET system explicitly selects quantization/execution patterns according to device capacity, accuracy and time constraints. PollicinoNet can study the disconnected discovery/distribution side without importing their performance claims.

References:

- https://arxiv.org/abs/2505.15030
- https://doi.org/10.3389/fcpxs.2026.1801157
