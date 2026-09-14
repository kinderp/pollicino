# UC-061 — Named Computation and Result Cache

## Idea

Treat a deterministic computation almost like content: if the **exact same approved computation over the exact same inputs** has already been executed somewhere, another node can discover and reuse the verified result instead of recomputing it.

The computation is identified by an exact descriptor such as:

```text
operation + runtime/model hash + input hashes + parameters + output schema
```

The corresponding result can then be cached, ferried and reused through PollicinoNet.

This composes UC-014 compute exchange, UC-024 content-need rendezvous and UC-057 model-to-data inference, but adds a distinct question: **when is a computation result itself safely reusable as a content-addressed object?**

## Problem solved

Sparse edge networks may have very little compute, battery or contact time. Two students or sensors may independently request the same expensive transform, model inference, archive conversion or reproducible analysis.

A normal opportunistic scheduler may execute the same work twice. PollicinoNet can first ask whether an exact valid result already exists nearby or on a relay. Only on a cache miss does the network seek an executor.

## Actors / nodes

- requester node;
- result-cache nodes;
- student relay/store-and-forward nodes;
- laptop/Raspberry Pi/GPU executor;
- optional data-holding edge node;
- optional school server or authoritative artifact store.

## Why PollicinoNet fits

The result lookup can be tiny even when execution/output is expensive.

- **DISCOVERY:** compact `ComputationNeed`, capability hints and `result available` reply;
- **EXACT:** operation ID, runtime/model hash, exact input roots, deterministic parameters, output schema, result hash and provenance;
- **SEMANTIC:** friendly labels such as `thumbnail`, `tiny-classifier`, `compile`, `extract-text`, never sufficient to declare a cache hit.

A cache hit is accepted only when the exact computation identity matches. LoRa remains the scarce control plane; results and inputs move over richer bearers.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** computation key/digest, cache availability, executor capability, job/result status;
- **BLE:** small result/input transfer nearby;
- **Wi-Fi/LAN:** datasets, models, build artifacts and larger results;
- **Internet:** optional authoritative cache or remote executor;
- **physical transport:** student-carried cache/storage moves exact result objects between disconnected groups.

## What we can test now in software

Start with deterministic harmless operations such as hashing, thumbnail generation, compression, source build/test, or a tiny fixed classifier.

Implement:

- canonical `ComputationKey` over operation/runtime/input/parameter/output-schema identity;
- local result cache plus remote `ResultNeed` discovery;
- exact result hash and provenance verification;
- cache hit versus compute miss path;
- duplicate concurrent requests collapsing onto one execution;
- stale runtime/model causing a deliberate cache miss;
- corrupted result rejection;
- non-deterministic operation marked explicitly as non-reusable or bounded by a seed/environment identity;
- execution failure cached only as policy-defined diagnostic state, never confused with a valid result;
- result eviction under storage pressure;
- integration with UC-014 executor discovery and UC-024 result retrieval;
- compare `always recompute`, `local cache only` and `opportunistic distributed result cache` on identical synthetic contact traces;
- metrics: cache-hit ratio, avoided executions, bytes moved, completion delay, false-hit count, duplicate-work count and storage pressure.

A key invariant is:

> a semantic similarity is never a computation cache hit; reuse requires exact identity of every input and execution factor declared relevant by the operation contract.

## What requires real hardware

- 3–4 LoRa nodes paired with at least two compute-capable devices;
- one deterministic job repeated by disconnected requesters;
- one cache carrier that later meets another requester;
- LoRa result-availability exchange;
- one real Wi-Fi/BLE result handoff;
- measurements of compute time/energy proxy, bytes transferred, cache-hit timing and actual contact windows.

Do not claim energy or latency savings until the same workload is measured with and without reuse on real devices.

## Messina teaching scenario

Two student groups in different coarse zones both need the same exact software build artifact or the same tiny AI inference result set for a prepared public dataset. Group A computes it first and stores the result under an exact `ComputationKey`.

A student relay later carries only the cache advertisement or the result itself toward Group B. Group B first asks for the exact computation result. If a verified cache hit exists, it retrieves the result over Wi-Fi; otherwise PollicinoNet falls back to UC-014 and schedules the job on an available executor.

A useful second exercise changes one compiler flag, model version or input hash and demonstrates that the old result must **not** be reused.

## Privacy / security

- only cache results from allow-listed deterministic operations in the first profile;
- include all security-relevant execution inputs in the computation key;
- verify result hashes and producer/runtime provenance;
- avoid broadcasting sensitive input names or model prompts; use opaque exact IDs where possible;
- treat a cache as storage, not as authority to disclose a result;
- enforce authorization before returning private outputs;
- separate public build/test artifacts from sensitive inference results;
- sandbox actual execution through UC-014/UC-057 rules;
- never reuse a result merely because a semantic label looks similar.

## Difficulty

**High.** The transport objects are compact, but defining a safe computation identity, determinism boundary, authorization and invalidation rules is subtle.

## Research / deployment signal

Build systems such as Bazel already separate an **action cache** from a content-addressed store so exact build actions can reuse verified outputs rather than recomputing them. Current edge research also studies joint caching, service placement and AI inference reuse under constrained wireless resources. UC-061 adapts the exact-result-reuse principle to a disruption-tolerant network where cache discovery itself may be delayed.

References:

- https://bazel.build/remote/caching
- https://doi.org/10.1109/JIOT.2026.3695862
- https://arxiv.org/abs/2608.01126
