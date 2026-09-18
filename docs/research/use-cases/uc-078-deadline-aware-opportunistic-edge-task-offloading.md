# UC-078 — Deadline-Aware Opportunistic Edge Task Offloading

## Idea

Let a constrained PollicinoNet node decide whether a job should run **locally now**, wait for a likely future contact, or be offloaded to a more capable edge node when connectivity is intermittent.

The important point is not merely finding a computer. UC-014 already covers capability/compute discovery. UC-078 adds the decision problem created by delay-tolerant networking:

> is waiting for an uncertain future contact still worth it given this job's deadline, input size, expected compute cost and result-return path?

The first experiments should use harmless deterministic jobs such as hashing, compression, image resizing or small public-model inference. Safety-critical robot control stays local and is explicitly out of scope.

## Problem solved

A sensor, robot or low-power board may have a task that is expensive locally but easy on a nearby laptop/Raspberry Pi. In a normal edge-computing system the node can offload immediately. In PollicinoNet the next suitable edge contact may happen minutes or hours later and may be shorter than expected.

A naive policy can fail in both directions:

- always execute locally and waste energy/time even when a useful edge contact is imminent;
- always wait for the edge and miss the deadline when the expected contact never happens;
- send the input but fail to retrieve the result before expiry;
- offload to a busy edge node when another node would have completed locally sooner.

## Actors / nodes

- constrained requester: MCU, Raspberry Pi, sensor node or robot companion computer;
- student relay/data-mule nodes;
- one or more edge workers such as school laptops or Raspberry Pis;
- optional school coordinator/cache;
- UC-008 contact-history source;
- UC-014 capability advertisements;
- optional UC-061 exact result cache.

## Why PollicinoNet fits

The decision can use compact control information while the heavy bytes move only when a suitable bearer exists.

- **DISCOVERY:** edge capability, queue class, coarse expected-contact hint, task class;
- **EXACT:** job ID, input/content hash, exact runtime/model/version, deadline/expiry, result hash and execution receipt;
- **SEMANTIC:** labels such as `small-inference`, `compression` or `batch-analysis`, useful for scheduling but never a substitute for the exact job contract.

PollicinoNet is useful because both the request and the eventual result can survive disconnection, move through relays and arrive at different times.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact job descriptor, capability/queue summary, deadline, accept/reject state, result-ready notification and exact hashes;
- **BLE:** nearby job negotiation or modest payload transfer;
- **Wi-Fi/LAN:** input artifacts, model/runtime assets and result transfer;
- **Internet:** optional fast path to an authorized edge/cloud worker;
- **physical transport:** a student node carries the queued job or result between disconnected islands.

## What we can test now in software

Add task-offloading decisions to the existing mobility/contact simulator.

Represent every job with at least:

```text
job_id
input_hash
runtime_or_model_id
estimated_local_cost
estimated_remote_cost
input_bytes
result_bytes
deadline
privacy_class
idempotency_key
```

Compare simple baselines before any predictive/AI policy:

- local-only;
- first-capable-edge;
- wait-until-threshold then fall back local;
- deadline-aware expected completion time;
- risk-bounded offload using contact-history distributions from UC-008;
- cache-aware offload that checks UC-061 before recomputing.

Inject:

- missed contacts;
- shorter-than-expected contacts;
- edge queue congestion;
- duplicate delivery of the same job;
- requester reboot while a job is remote;
- result arriving after deadline;
- exact runtime/model mismatch;
- sensitive inputs that policy forbids from leaving the originating node.

Useful metrics include deadline success rate, wasted offloads, duplicate execution, bytes carried per bearer, local-vs-remote compute time, queue delay and energy only when the underlying energy model is measured or clearly synthetic.

A key invariant is:

> the network may delay or duplicate an offload request, but one exact logical job must remain idempotent and its result must be bound to the exact input/runtime contract.

## What requires real hardware

First physical experiment:

- 2 constrained requester nodes;
- 1–2 edge workers with deliberately different capabilities/queues;
- 1 student relay;
- deterministic jobs whose correct result is easy to verify;
- controlled periods where no direct requester-edge path exists;
- compare local-only with one simple deadline-aware offload policy on the same workload.

Measure actual contact duration, transfer time, execution time and result-return delay. Do not claim an energy advantage unless power is measured on the real devices.

A later experiment can use a harmless inference workload or a Romeo companion-compute task, but never move real-time safety or motor-stop logic off the robot.

## Messina teaching scenario

Place requester nodes in two classroom/home-lab islands represented as `Rometta/Venetico` and `Spadafora`, with a stronger edge worker at school. A student's node periodically becomes the courier.

Each requester receives jobs with different deadlines. Some are cheap enough to execute locally; others would benefit from the school worker if the courier arrives soon enough. Students compare policies using the same measured contact trace from UC-008 rather than assuming a permanent path.

The exercise makes the tradeoff visible: a faster computer is not automatically the faster *system* when the transport path is intermittent.

## Privacy / security

Task metadata and inputs may be sensitive.

- do not broadcast filenames, personal queries or raw sensor contents in LoRa advertisements;
- use opaque job IDs and exact content hashes;
- authorize which worker may see which privacy class;
- encrypt payloads end-to-end when relays are not trusted with content;
- pin runtime/model/version so a result cannot silently come from a different computation;
- sign or authenticate result envelopes;
- treat worker-reported completion as evidence, not blind authority, when output can be independently verified;
- never offload safety-critical control loops or actions whose delay could harm people/property.

## Difficulty

**High.** The queueing code is straightforward; the difficult part is making a decision under uncertain future contacts while preserving exact job identity, idempotency, privacy and a realistic return path.

## Why this is distinct from nearby use cases

- **UC-014:** discovers and uses available compute/storage capabilities.
- **UC-057:** sends an approved model/analysis toward data that should remain local.
- **UC-061:** reuses an already computed exact result.
- **UC-078:** decides **local execution versus waiting/offloading under deadline and contact uncertainty**, including the delayed result path.

## Research signal

Recent 2026 work explicitly studies deadline-aware task offloading when edge connectivity is disruption-tolerant or intermittent. Firefly models future DTN contacts and uses them to choose whether constrained IoT jobs should be offloaded; other work studies deadline-aware offloading under unstable mobile-edge links. These are useful problem references, not PollicinoNet performance claims.

References:

- https://doi.org/10.1109/OJCOMS.2026.3672750
- https://ispublishing.com/index.php/aici/article/view/228
