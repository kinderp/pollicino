# UC-RFMAP-001 — Privacy-bounded RF evidence survey and site planning

Status: PRIMARY / PHYSICAL-EVIDENCE INFRASTRUCTURE, software-first planning only until measured checkpoints exist

## Problem

A real student network cannot be planned responsibly from nominal LoRa range or synthetic town-to-town links. We need measured evidence about where controlled Pollicino contacts actually work, fail or enter a transition region.

The concrete question is:

> can supervised student/teacher campaigns produce privacy-bounded, replayable RF evidence that helps choose future fixed relay/gateway/checkpoint sites without turning ordinary student movement into location tracking?

This is distinct from `UC-TRACE-001`. TRACE studies **who encountered whom over time**. RFMAP studies **controlled radio outcomes at known experiment checkpoints/geometry** so RF replay and infrastructure planning can be calibrated.

## Actors / nodes

- two or more Pollicino LoRa boards used in controlled measurements;
- teacher/supervisor running the physical campaign;
- fixed candidate school/lab/territorial checkpoints with explicit permission;
- optional student teams carrying one test node during supervised sessions;
- evidence catalog / RF replay tooling;
- planning tool that consumes only measured or clearly synthetic matrices.

## Why PollicinoNet fits

The repository already has an RF evidence catalog, deterministic physical-trace replay and an explicit HW-006 evidence gate. RFMAP turns that infrastructure into a concrete use case: measurements are collected not merely to characterize a radio, but to decide whether a future network needs a fixed relay/gateway, where evidence is missing and which synthetic routing assumptions must be rejected.

The result should be an **evidence matrix**, not a decorative coverage circle.

## Possible bearers

- LoRa: the bearer being measured under the frozen campaign configuration;
- Wi-Fi/LAN: upload evidence logs after a supervised session;
- physical carry: move logs back to school when no rich link is present;
- BLE: optional local setup/configuration only, not a substitute for the LoRa measurement.

## What we can test immediately in software

Before any new RF measurement, use entirely synthetic matrices to validate the planning pipeline:

```text
checkpoint -> checkpoint
attempt count
success / unresolved
RSSI/SNR when actually recorded
frame size
TX power
geometry/evidence label
```

Software experiments can compare:

- naive circular-range assumption;
- synthetic measured-link matrix;
- greedy fixed-site selection from that matrix;
- robustness to one relay/site failure;
- confidence-aware planning where sparse cells remain UNKNOWN rather than inferred reachable.

Metrics:

- fraction of required logical pairs supported by evidence;
- number of candidate fixed sites selected;
- redundancy / single-point-of-failure count;
- number of UNKNOWN cells;
- sensitivity to removing one measured link;
- difference between model-only and evidence-constrained plans.

No synthetic gateway plan is a deployment claim.

## Messina student-network scenario

The long-term educational network may involve school, home-area and territorial clusters across the province. RFMAP does **not** ask students to continuously map their daily route.

Instead, later supervised campaigns can use named public/authorized checkpoints such as:

```text
school courtyard A
school floor B
approved outdoor checkpoint C
approved territorial fixed site D
```

Only after governance and permission could wider province checkpoints be added. Rometta, Spadafora, Saponara, Villafranca, Messina or other places may be scenario labels in software; they become physical evidence only when an explicit measured campaign records them.

## What requires real hardware

RFMAP is deliberately blocked from physical conclusions until hardware evidence exists.

The first required campaign remains the existing HW-006 sequence:

```text
42-byte frames / 2 dBm
same room
-> greater separation
-> one wall
-> multiple walls / floor
-> outdoor
```

After a transition region is actually observed, later campaigns may add:

- controlled geometry and antenna orientation;
- actual governance/control frame sizes;
- candidate fixed-site comparisons;
- repeated measurements at different times;
- explicit occupancy/interference context;
- per-site evidence confidence.

The PHY must not be changed merely to make a map look better.

## Privacy and security

- no continuous GPS collection from students;
- no publication of home addresses or ordinary commute traces;
- use authorized checkpoint IDs rather than personal locations;
- separate RF evidence from student identity;
- retain raw geometry only where needed for reproducibility and access-controlled appropriately;
- document antenna/device configuration and firmware provenance;
- prevent unauthenticated uploads from silently becoming trusted RF evidence.

## Difficulty

**Medium in software; medium-high operationally because measurement discipline and privacy matter more than algorithm complexity.**

## Success / kill criteria

Continue if controlled measurements materially reduce uncertainty compared with naive coverage assumptions and produce reproducible evidence suitable for replay/planning.

Reject any planning feature that silently fills UNKNOWN areas with guessed reachability or encourages collection of continuous student location traces.

## Related-work note

Coverage/gateway placement and empirical LoRa/LoRaWAN measurement are established research topics. Recent 2026 work also studies geometry-aware/digital-twin gateway placement, while real-world LoRaWAN studies emphasize measured RSSI/SNR/PDR. Those results are methodological references only: Pollicino's raw-LoRa/mesh configuration, frozen PHY and local terrain require their own evidence.

## Physical evidence boundary

This use case strengthens, rather than relaxes, HW-006. No real range, coverage, gateway count or territorial topology claim may be made without recorded physical measurements. The frozen LoRa PHY remains unchanged.