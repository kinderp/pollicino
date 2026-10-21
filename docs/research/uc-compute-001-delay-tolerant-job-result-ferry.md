# UC-COMPUTE-001 — Delay-tolerant edge job and result ferry

Status: RESEARCH / PROTOTYPE

## Summary

A small disconnected node may know *what computation it wants* but lack the CPU/GPU, data or power to perform it locally. PollicinoNet can carry a compact, authenticated job descriptor toward a school/home/vehicle compute node and later carry back the result or a result reference. Large inputs/models/results are resolved over Wi-Fi/LAN/Internet when available rather than being forced through LoRa.

This differs from `UC-AI-001`, which synchronizes AI artifacts. `UC-COMPUTE-001` moves **work requests and result state**.

## Problem solved

Examples include:

- a sensor cluster requests aggregation/anomaly analysis;
- a student field experiment asks a school computer to process a dataset;
- a robot carries an image-analysis job reference to a later Wi-Fi/edge station;
- an AI-capable home node executes a prompt/inference task whose model is already local;
- a disconnected kiosk submits a periodic indexing/validation job and receives only a compact result.

The application tolerates minutes/hours of delay; it is not interactive remote computing.

## Actors / nodes

- low-power requester node;
- student-carried relay nodes;
- school/home compute gateway;
- optional GPU/AI worker;
- rich storage/model source;
- result consumer.

## Messina educational scenario

A field/sensor node creates job `J42`: process dataset hash `D7` with analysis recipe `R3`. A student node carries the job descriptor to school. The school worker already has `D7`, executes the authorized sandboxed task and publishes result hash/reference `O42`. A later student encounter returns `O42` toward the originating cluster; the full result is downloaded on Wi-Fi if it is large.

The experiment uses pseudonymous clusters and synthetic workloads; it assumes no town-to-town LoRa link.

## Why PollicinoNet fits

A job descriptor has DTN-friendly properties:

- compact asynchronous unit of work;
- content-addressed input/output references;
- explicit expiry/deadline;
- custody and store-carry-forward;
- duplicate suppression/idempotency;
- priority scheduling;
- provenance and exact result identity;
- rich-link handover for bulk data.

RFC 4838 explicitly recommends structuring DTN application data as self-contained asynchronous units rather than conversational request/response sequences; job descriptors are a natural example.

## Bearers

- LoRa: job descriptor, input/result hashes, queue/receipt state;
- BLE: local handoff to a nearby worker;
- Wi-Fi/LAN: input datasets, output payloads and local model access;
- Internet: optional remote worker/artifact repository;
- physical carry: mobile nodes ferry pending jobs/results between isolated and compute-rich clusters.

## What we can test now in software

Model workers with finite queues/capabilities and jobs with creation time, deadline, required capability, input availability and estimated cost. Compare:

1. execute only when requester directly reaches worker;
2. DTN relay of job descriptors;
3. capability-filtered relay;
4. job deduplication/idempotency;
5. result bytes over scarce link versus result-reference-only return.

Metrics:

- job completion before deadline;
- queue delay;
- duplicate executions prevented;
- job/control wire bytes;
- result-reference versus result-payload bytes;
- number of physical carries;
- worker utilization;
- failed jobs due to missing inputs/capabilities;
- eventual result retrieval success.

This workload can later give a concrete application utility for RAPID-like routing experiments, but only after the deadline/utility semantics are preregistered.

## Hardware required later

Real boards/compute nodes become necessary to measure:

- energy cost of generating/verifying job metadata;
- real handoff latency and retry behavior;
- worker execution time/power for selected tasks;
- practical queue behavior after device restarts;
- real LoRa-to-Wi-Fi/worker handover.

Real-time robotics, safety control or latency-critical inference is explicitly out of scope.

## Privacy and security

Compute requests can be dangerous if arbitrary code is accepted.

Minimum boundary:

- no arbitrary shell/code execution from unauthenticated jobs;
- use a fixed recipe/capability registry or sandboxed allowed workload;
- authenticate/authorize submitters;
- quotas on job rate, CPU/GPU time and storage;
- content-addressed immutable inputs where possible;
- encrypted private inputs/results end-to-end;
- deterministic job IDs/idempotency to prevent duplicate execution;
- do not expose prompts, student data or private dataset names in broadcast metadata.

## Difficulty

**High.**

Transport is comparatively simple; safe scheduling, capability negotiation and sandboxed execution create the complexity.

## Research context

Mobile/edge-computing research extensively studies task offloading under resource, latency and reliability constraints. PollicinoNet's distinct question is whether a useful subset of those workloads remains meaningful when the network itself is delay-tolerant and physical carry is part of the path.

## Success criteria

Continue if relay/capability-aware job ferrying completes materially more delay-tolerant work than direct-only access without excessive metadata, duplicate execution or security complexity.

## Decision

**RESEARCH / PROTOTYPE.**

Keep it above the generic Pollicino object/bundle layer. Do not add a compute protocol to core until multiple real workloads need common semantics.
