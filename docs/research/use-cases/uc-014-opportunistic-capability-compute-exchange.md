# UC-014 — Opportunistic Capability and Compute Exchange

## Idea

Let nearby nodes advertise **what they can do**, not only what content they hold. A student-carried LoRa node can announce that its paired laptop/Raspberry Pi has a GPU, free storage, a camera, Internet access, a specific model, or the ability to execute an allow-listed job. A requester sends a compact job descriptor or rendezvous coordinate; large inputs and results move later over Wi-Fi/LAN/Internet or by physical carry.

A concrete Messina classroom scenario is a distributed group of student nodes across different towns: one node has a small sensor backlog, another is paired with a laptop able to run inference, and the school server has a stronger GPU. PollicinoNet can discover a suitable executor even when there is no permanent end-to-end path.

## Problem solved

In an intermittent network, the useful resource may be **compute, storage or connectivity** rather than a file. A node that cannot process a task locally should be able to discover another node that can, queue the task safely, and retrieve a verifiable result later.

## Actors / nodes

- student LoRa relay paired with a laptop, Raspberry Pi or other edge computer;
- fixed school server or GPU workstation;
- sensor/robot node creating a job;
- mobile relay carrying job/result coordinates;
- `PollicinoStore` instances holding exact input/output objects.

## Why PollicinoNet fits

`DISCOVERY` can carry compact capability hints and job rendezvous coordinates. `EXACT` can identify immutable job inputs and outputs by full hashes in the resolved manifest. Store-and-forward allows a job request, an executor advertisement and the final result to meet at different times. The scarce link does not need to transport a dataset or model if both sides can resolve the same content from a richer bearer or cache.

This is application-level scheduling. It does **not** require any change to the frozen LoRa PHY.

## Possible bearers

- **LoRa:** capability digest, job ID, priority, TTL, input/output coordinates, acceptance/status and compact authenticator;
- **BLE/Wi-Fi/LAN:** job input, result object, model or container/image transfer;
- **Internet:** remote artifact resolution or school-server execution;
- **physical transport:** a student-carried node can ferry the job manifest or exact artifacts between disconnected islands.

## What we can test now in software

- model nodes with different capabilities, battery/storage budgets and intermittent contact windows;
- define an idempotent `JobManifest` with exact input hashes and requested capability tags;
- select an executor under partitions and stale capability advertisements;
- retry a job without executing it twice;
- simulate executor disappearance and lease/TTL expiry;
- verify that the returned object matches the declared exact hash;
- compare strategies such as nearest executor, cheapest-transfer executor and already-cached-input executor;
- record task completion ratio, completion delay, scarce-link bytes, cache hits and duplicate work.

A first safe workload can be trivial: hash a file, compress a synthetic chunk, run a tiny classifier on a prepared dataset, or transform a non-sensitive image.

## What requires real hardware

- at least three real nodes with different paired capabilities;
- LoRa capability advertisement and job/status exchange;
- one real rich-link handover for the job input or result;
- measured end-to-end completion time, packet loss/RSSI/SNR for the radio segment and actual transferred bytes.

Do not infer field latency or reliability from the simulator.

## Privacy / security

Never execute arbitrary code received from an untrusted peer. Start with an allow-list of predefined jobs inside a sandbox. Job manifests should be authenticated, inputs encrypted when sensitive, and capability advertisements should reveal only what is necessary. A student device must be opt-in and must not expose personal files, usernames, precise location or unrestricted shell access.

## Difficulty

**High.** The PollicinoNet primitives fit well, but safe execution, leases, authorization, scheduling and failure recovery require careful design.

## Research signal

Recent mobile-edge work continues to treat **task placement, caching and communication cost together** rather than assuming that every task should go to the cloud. This use case adapts that systems question to an intermittent, store-carry-forward teaching network without importing any claimed performance result into PollicinoNet.
