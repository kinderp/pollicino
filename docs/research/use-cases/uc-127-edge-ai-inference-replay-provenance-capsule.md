# UC-127 — Edge AI Inference Replay and Provenance Capsule

## Idea

Attach a compact provenance capsule to an AI result so another node can later understand what produced it and, when possible, replay the computation.

The capsule carries exact identifiers rather than the full model or input over LoRa.

## Problem solved

An edge node may report a classification or generated result long before the original input, model or runtime is available to the reviewer.

Later we may need to know:
- which exact model and quantization produced the result;
- which input version was used;
- which preprocessing, prompt template or parameters mattered;
- whether the runtime was deterministic;
- whether the result can be replayed exactly, approximately, or not at all.

## Actors / nodes

Edge-AI producer, student relay/store-and-forward nodes, model/artifact cache, reviewer, optional replay worker, and optional Raiatea evidence store.

## Why PollicinoNet fits

The capsule is small even when model and input are large.

A minimal capsule can bind:
- inference ID;
- input hash or evidence reference;
- model hash;
- tokenizer or preprocessor hash;
- runtime ID and version;
- quantization/configuration ID;
- inference parameters;
- seed when relevant;
- retrieval references when used;
- output hash;
- determinism class.

DISCOVERY can advertise replay capability and artifact availability. EXACT carries hashes and versions. SEMANTIC labels remain only human-friendly descriptions.

## Possible bearers

- LoRa: inference ID, compact result summary, capsule hash and replay status;
- BLE: small capsule or nearby input;
- Wi-Fi/LAN: model, input, traces and full output;
- Internet: optional artifact access;
- physical transport: laptop or storage device carrying large replay artifacts.

## What we can test now in software

Start with deterministic tasks before LLM generation:
1. fixed image classifier;
2. fixed text embedding;
3. deterministic transform;
4. local LLM with pinned model, runtime and parameters.

Test:
- exact replay on the same runtime;
- replay after one parameter changes;
- wrong model hash;
- tokenizer or preprocessor change;
- missing input;
- same model on a different backend;
- nondeterministic operation;
- retrieval input changed since the original inference;
- stale cached result from UC-061.

Use explicit states such as REPLAY_EXACT, REPLAY_DIFFERENT, REPLAY_UNAVAILABLE, NONDETERMINISTIC and INSUFFICIENT_EVIDENCE.

A central rule is: provenance can explain how an output was produced; it does not prove that the output is correct.

## What requires real hardware

Use at least two genuinely different compute devices, for example two student laptops or a laptop and a Raspberry Pi-class host.

Run the same pinned inference on both where possible, exchange only capsule metadata over LoRa, then move missing model or input artifacts over Wi-Fi and attempt replay.

Any claim of bit-exact reproducibility must be demonstrated on the measured runtime and hardware combination.

## Messina teaching scenario

One student node performs a harmless classification on a public sample while offline and sends only sample hash, model hash, compact result and capsule hash through PollicinoNet.

Another group receives the claim later, obtains the referenced model and input over Wi-Fi or physical carry, and tries to replay it.

Students can then see the difference between same semantic model name, same exact model artifact, same runtime/configuration and same output bytes.

## Privacy / security

Keep private raw inputs off LoRa, use hashes or opaque references where possible, bind the capsule to exact model/runtime/input identities, preserve source-data usage constraints, and remember that hashes can still identify known content.

## Difficulty

High. Capturing metadata is easy; defining the true replay boundary for nondeterministic models and heterogeneous runtimes is difficult.

## Why this is distinct

UC-038 coordinates benchmark rounds across devices. UC-061 reuses exact deterministic cached computation results. UC-101 uses disagreement to decide what needs review. UC-119 carries provenance for media assets. UC-127 carries per-inference execution provenance and replay evidence for AI outputs.

## Research / implementation signal

GenAI observability and inference provenance are becoming explicit engineering concerns. OpenTelemetry defines GenAI model, request and response attributes, while 2026 work explores inference provenance and deterministic replay.

References:

- https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
- https://opentelemetry.io/blog/2026/genai-observability/
- https://arxiv.org/abs/2602.00182
