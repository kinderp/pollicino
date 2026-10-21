# UC-TRACE-001 — Privacy-preserving encounter observatory and contact-trace ferry

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING RESEARCH INFRASTRUCTURE

## Problem

A real PollicinoNet deployed among students cannot be evaluated only from invented mobility schedules. Before claiming that one routing policy, relay role or territorial pattern is better, the project needs evidence about when nodes actually encounter each other, how often contacts recur and how fragmented the temporal graph is.

The network can therefore carry a privacy-preserving summary of its own encounters back to a school analysis point. The goal is not to track students. The goal is to build a bounded experimental contact trace that can be replayed in the simulator and used to understand whether the synthetic mobility assumptions resemble reality.

This use case is deliberately separate from `UC-OPS-001`: OPS manages node state; TRACE measures temporal connectivity and routing opportunity.

## Actors / nodes

- student-carried Pollicino nodes;
- optional fixed classroom/lab nodes;
- school collection gateway;
- offline analysis workstation;
- optional DNATrace-style trace-analysis component, if/when such an integration contract is defined.

## Messina educational scenario

Use pseudonymous cohorts such as `cluster-west`, `cluster-hill`, `cluster-coast`, `school-hub`. Nodes record only bounded encounter facts, for example rotating-peer-token, coarse time bucket, bearer and a small link-quality/contact outcome summary.

```text
student nodes encounter during ordinary movement
             |
             v
      local bounded logs
             |
      store / carry / forward
             |
             v
        school gateway
             |
             v
 privacy-filtered temporal graph -> simulator replay
```

Actual home addresses, GPS trails and named student identities are out of scope.

## Why PollicinoNet fits

The experiment is useful precisely because connectivity is intermittent. Encounter summaries can themselves tolerate delay and be ferried through the same network being observed.

PollicinoNet already has the right primitives for:

- store-carry-forward;
- compact structured records;
- deduplication/reconciliation;
- finite storage;
- provenance/evidence classes;
- replay into synthetic contact windows.

The resulting trace can later become an evidence input for routing and topology experiments without changing the LoRa PHY.

## Possible bearers

- LoRa for the contact being observed and for summary ferrying;
- BLE for very short-range encounter experiments if separately enabled;
- Wi-Fi/LAN for draining logs at school/home;
- Internet only for optional archival/export;
- physical movement as the carry mechanism.

## What can be tested now in software

Before real boards we can create synthetic encounter logs and test:

1. raw pairwise logging versus time-bucketed aggregation;
2. rotating pseudonyms versus stable laboratory IDs;
3. local summarization before export;
4. finite trace buffers and loss policy;
5. duplicate encounter coalescing;
6. graph reconstruction from partial reports;
7. replay of the resulting trace into Direct Delivery, Spray-and-Wait, PRoPHET, Destination Recency/Interval/Service and RAPID research baselines;
8. sensitivity to missing nodes and missing trace segments.

A useful software gate is whether coarse summaries preserve enough temporal structure to reproduce routing conclusions without exporting fine-grained mobility histories.

## What requires real hardware

Real boards are required before claiming:

- actual encounter frequency;
- contact duration or useful-byte opportunity;
- real inter-contact distributions;
- real route/community structure;
- real link-quality correlation with place or movement;
- any routing advantage on the student network.

HW-006 remains the first RF gate. TRACE should begin only after the frozen campaign establishes the measurement method well enough to define what counts as a contact.

## Privacy / security

This use case is privacy-critical because human mobility traces are highly identifying even after apparent anonymization.

Requirements:

- explicit consent and school governance before field collection;
- no GPS required by the core experiment;
- no home address or named student identifier in trace payloads;
- rotating short-lived pseudonyms for field experiments;
- coarse time buckets where possible;
- local aggregation before export;
- short retention and deletion policy;
- access control on raw traces;
- publish only aggregate statistics or synthetic derivatives unless separately approved;
- avoid combining trace data with attendance, grades or other personal datasets.

## Implementation difficulty

**Medium-high.** The networking mechanics are straightforward; privacy-safe trace design, clock uncertainty, evidence labeling and reproducible replay are the hard parts.

## Minimal measurable hypotheses

- H1: privacy-filtered encounter summaries retain enough temporal structure to distinguish routing strategies in replay.
- H2: student mobility creates recurring temporal bridges that are materially different from uniform random contact schedules.
- H3: bounded local aggregation cuts trace overhead without materially changing the main delivery/latency conclusions.

## Metrics

- encounter reports generated / exported;
- bytes of trace overhead;
- unique temporal edges recovered;
- missing-edge rate under partial reporting;
- inter-contact distribution by pseudonymous cohort;
- routing-result difference between raw and privacy-filtered traces;
- retention/storage pressure;
- fraction of events suppressed by aggregation.

## Gate decision

**PROTOTYPE.** This is one of the strongest next experiments because it converts future physical deployment into reusable evidence while directly enforcing the rule that no real-network claim is made from synthetic topology alone.

## Related research precedent

Pocket Switched Network experiments have long used real human encounter traces to evaluate opportunistic forwarding. See Chaintreau et al., “Pocket Switched Networks: Real-world mobility and its consequences for opportunistic forwarding”, University of Cambridge Technical Report UCAM-CL-TR-617: https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-617.html .

Mobility privacy must be treated as a first-class constraint; de Montjoye et al. showed that even coarse spatiotemporal traces can be highly identifying: https://doi.org/10.1038/srep01376 .
