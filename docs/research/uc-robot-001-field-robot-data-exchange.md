# UC-ROBOT-001 — Field robot / drone delayed data exchange

Status: FUTURE USE CASE / RESEARCH

## Problem

A mobile robot, rover, drone or autonomous vehicle can operate temporarily outside a rich network. It may need to export observations and logs, receive new non-urgent tasks, advertise state, or rendezvous with a richer channel when it returns near a base station.

PollicinoNet is potentially useful for **delayed supervisory information and data products**, not for safety-critical closed-loop control.

Candidate objects:

- mission/task descriptor for a future operation;
- health/status summary;
- sensor/event observation;
- map or image manifest;
- small map patch;
- log reference;
- rendezvous coordinate for later Wi-Fi transfer;
- “data available” advertisement.

## Actors / nodes

- mobile robot/rover/drone;
- fixed base station;
- portable student relay;
- field sensor nodes;
- optional vehicle relay;
- Wi-Fi/Internet edge server.

## Why PollicinoNet fits

Robots create discontinuous contacts and large asymmetry between tiny control/status metadata and bulky collected data. PollicinoNet can keep those layers separate:

```text
LoRa / scarce link
status + task + reference + manifest

Wi-Fi / dock / LAN
images + maps + logs + datasets
```

Store-carry-forward also allows another mobile node to collect results when the robot never reaches the final gateway directly.

## Possible bearers

- LoRa for compact supervisory/status data;
- BLE for provisioning/close service;
- Wi-Fi for dock/nearby bulk transfer;
- Internet through a base station;
- physical robot/drone/vehicle movement as carry.

## What can be tested now in software

- simulated moving robot nodes and base stations;
- mission/status objects with TTL and priority;
- large observation manifests with later Wi-Fi handover;
- missed-return/contact scenarios;
- one mobile collector visiting multiple sensor clusters;
- Direct Delivery/Epidemic/Spray-and-Wait comparisons;
- simple planned-contact versus opportunistic routing.

No physical robot is needed to test these networking semantics.

## What requires real hardware

Substantial hardware evidence is required before operational claims:

- contact duration while moving;
- antenna orientation/body effects;
- LoRa range and loss during motion;
- actual Wi-Fi handover time;
- vehicle/drone power impact;
- safe integration with robot electronics;
- flight/vehicle operational constraints.

The current HW-006 LoRa gate remains prerequisite for radio claims, but a robot/drone campaign would need additional evidence beyond HW-006.

## Privacy / security

- authenticate task descriptors;
- reject replayed/stale commands;
- cryptographically bind collected data to mission/device provenance;
- minimize location leakage in public radio metadata;
- separate read-only observation relays from command authority;
- never allow an untrusted relay to gain vehicle control privileges.

## Safety boundary

**PollicinoNet must not be the primary real-time control or collision-avoidance path.** Loss, delay and reordering are normal DTN conditions. Safety-critical motion control must remain on independently validated local/control links.

## Implementation difficulty

**High** for real deployment; **medium** for simulation.

## Minimal measurable hypotheses

- H1: reference/manifest-first transfer reduces scarce-link traffic compared with attempting to move robot data products over the scarce bearer.
- H2: a mobile collector can increase eventual delivery from isolated sensor/robot nodes under synthetic contact schedules.
- H3: planned rendezvous with Wi-Fi can transfer bulky data while LoRa carries only supervisory state.

## Metrics

- task/status delivery ratio and latency;
- stale task rejection;
- observation manifest delivery;
- successful rich-link handovers;
- scarce-link bytes avoided;
- exact artifact verification;
- contact misses;
- security-policy rejection count.

## Gate decision

**RESEARCH.** The use case is credible and supported by DTN/UAV data-collection literature, but it does not justify robot-specific protocol work before software simulation shows a need beyond existing bundle/reference primitives.

## Related research precedent

UAV-assisted IoT collection literature treats mobile UAVs as flexible data collectors for distributed sensors; one survey is https://arxiv.org/abs/2211.09555 .