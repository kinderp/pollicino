# UC-118 — Delay-Tolerant Digital Twin State Reconciliation

## Idea

Maintain a useful digital representation of a disconnected sensor, robot or field device even when state updates arrive late, out of order or through different relay paths. The twin must make freshness and uncertainty explicit instead of pretending that its latest cached state is current.

The frozen LoRa PHY is unchanged.

## Problem solved

A school sensor, mobile robot or rural device may be physically operating while its digital twin at school has not heard from it for minutes or hours. During that gap:

- the physical state can change;
- multiple delayed updates can arrive out of order;
- a prediction may become less trustworthy as time passes;
- an operator can accidentally act on stale state.

The useful question is not only "what was the last value?" but "what exact device/version produced it, how old is it, and what do we still not know?"

## Actors / nodes

- physical node: sensor, robot or harmless actuator;
- digital-twin host on a laptop/Pi/server;
- relay/store-and-forward student nodes;
- optional edge predictor;
- operator/reviewer.

## Why PollicinoNet fits

Digital-twin control metadata is often much smaller than raw telemetry.

- **DISCOVERY:** twin/device ID, state class, freshness bucket, pending evidence.
- **EXACT:** device identity, state version, observation hash, firmware/config/calibration IDs, predecessor state and evidence references.
- **SEMANTIC:** labels such as "likely unchanged" or "needs refresh", which must never overwrite exact evidence.

LoRa can carry state digests, version counters and refresh requests. BLE/Wi-Fi/LAN can carry full snapshots, logs, images or map fragments. Physical transport can move a complete evidence pack.

## Possible bearers

- **LoRa:** state version, freshness/uncertainty class, compact critical delta, refresh request;
- **BLE:** nearby state snapshot or maintenance sync;
- **Wi-Fi/LAN:** full telemetry/history, robot map or larger state;
- **Internet:** optional cloud mirror when available;
- **physical transport:** removable-media evidence or a carried device.

## What we can test now in software

Build a small physical-twin simulator and a separate digital-twin process. Inject:

- delayed and reordered updates;
- duplicate updates;
- missing versions;
- reboot and sequence reset;
- conflicting updates from two relay paths;
- stale predictions;
- late correction of previously accepted state;
- a source/configuration change that makes an old state incomparable.

Compare policies such as full periodic sync, event-driven sync and risk/freshness-triggered sync. Measure bytes moved, version lag, time spent in UNKNOWN/stale state and incorrect stale-state assumptions.

The key invariant is: a twin may be incomplete or stale, but it must say so explicitly.

## What requires real hardware

Start with 4–6 PollicinoNet boards, one harmless temperature/humidity sensor or Romeo-like robot state source, one twin host and normal student relays.

A later test can deliberately disconnect the physical node, change its state, then reconnect through relays and verify that the twin converges to the exact measured state.

Any latency, range, PDR, energy or freshness claim must come from measured experiments, not simulation.

## Messina teaching scenario

A sensor or robot at one school/lab site is represented by a twin at the main lab. Students moving through Messina, Villafranca, Rometta/Venetico and Spadafora relay compact state updates. The twin dashboard shows both the last known state and its age/uncertainty.

This is especially useful for teaching that "last received" and "current" are not the same thing in distributed systems.

## Privacy / security

- do not put student identity or precise home location into twin state;
- authenticate state updates and bind them to one device/configuration version;
- prevent an old delayed update from silently replacing a newer state;
- keep operator commands separate from descriptive twin state;
- do not use the first prototype for safety-critical control;
- expire or coarsen long-term location/history where possible.

## Difficulty

**High.** The data model is manageable; the difficult part is correct freshness, conflict and uncertainty semantics under long partitions.

## Why this is distinct

UC-058 migrates a service and state between hosts; UC-083 distributes topic updates; UC-089 manages alarm state; UC-107 revalidates cached content. UC-118 models the continuing relationship between a **physical device and an intermittently synchronized digital representation**.

## Research / implementation signal

Recent work treats synchronization quality and update scheduling as first-class digital-twin problems under bandwidth or reliability constraints.

References:

- https://www.eurecom.fr/publication/8631
- https://ieeexplore.ieee.org/document/11571569/
- https://doi.org/10.3390/fi18030137
