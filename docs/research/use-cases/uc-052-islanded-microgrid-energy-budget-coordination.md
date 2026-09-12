# UC-052 — Islanded Microgrid Energy Budget and Flexible-Load Coordination

## Idea

Use PollicinoNet to coordinate **small, non-safety-critical energy budgets and flexible loads when connectivity is intermittent**, starting with a low-voltage classroom microgrid emulator rather than any real electrical grid.

Nodes advertise compact energy state and requests such as “battery low”, “surplus available”, “load can wait” or “run this harmless load after the next energy window”. Relays can carry these updates when there is no permanent backhaul.

## Problem solved

In a small rural/off-grid system, energy availability and communication availability can both be intermittent. A central cloud controller may be unreachable exactly when local decisions are needed.

The research problem is not to control the electricity grid over LoRa. It is much narrower:

```text
How can disconnected nodes share enough delayed state
for low-risk flexible loads to make better local decisions?
```

Examples include a sensor gateway deciding when to upload data, a battery-powered hotspot delaying a non-urgent sync, or a classroom solar/battery emulator choosing which LEDs/fans/test loads to run first.

## Actors / nodes

- low-voltage energy-source emulator or small solar/battery teaching kit;
- battery/storage node;
- harmless flexible-load nodes such as LEDs, fans or USB test loads;
- student relay/store-and-forward nodes;
- school coordinator/dashboard node;
- optional sensor/data-mule nodes whose jobs consume energy;
- optional UC-026 action-ticket issuer for tightly scoped actuation.

## Why PollicinoNet fits

Energy state changes over time but many coordination messages are tiny.

- **DISCOVERY:** `energy-state available`, `flexible-load request`, `surplus window`;
- **EXACT:** node ID, energy/battery bucket, observation epoch, request ID, priority class, allowed action and expiry;
- **SEMANTIC:** labels such as `critical`, `deferrable`, `best-effort`, which must be backed by exact policy rather than free-form interpretation.

LoRa can carry compact telemetry and coordination intents. Wi-Fi/LAN can move detailed logs and firmware. Physical mobility can ferry state between isolated rural nodes.

The design is useful precisely because it can tolerate stale/delayed information, provided local safety bounds are never delegated to the network.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** energy bucket, battery state, queue pressure, load-request ID, priority, expiry and compact authorization;
- **BLE:** nearby setup/diagnostics and short-range device coordination;
- **Wi-Fi/LAN:** detailed energy traces, dashboards and bulk configuration;
- **Internet:** optional remote monitoring when present;
- **physical transport:** a mobile node carries delayed energy/queue summaries between isolated sites.

## What we can test now in software

Build a discrete-time microgrid simulator with no real power hardware.

- simulate solar/energy production traces, battery state and several flexible loads;
- define hard local bounds that networking can never override;
- let nodes publish delayed/stale energy summaries;
- compare `run immediately`, `local-only heuristic` and `delay-tolerant coordinated` policies;
- simulate communication partitions and relay-carried updates;
- model a load request expiring before the coordination message arrives;
- test duplicate, reordered and forged load requests;
- integrate UC-020 freshness so stale energy state is explicit;
- integrate UC-026 one-use action tickets for a harmless actuation command;
- integrate UC-045 when a mobile collector must choose between data transfer and conserving energy;
- record unmet flexible-load requests, battery-floor violations in the simulator, stale-decision count, message bytes and energy-state age.

A key invariant is:

> local electrical safety and battery protection remain local deterministic constraints; delayed network coordination may optimize only within those bounds.

## What requires real hardware

Only after the simulator is stable:

- a **low-voltage DC** bench setup, for example USB power banks, small solar emulator/panel, LEDs/fans/resistive test loads and instrumented microcontrollers;
- 3–5 LoRa nodes with deliberately intermittent connectivity;
- measured battery/voltage/current telemetry from the teaching setup;
- repeated runs with the same scripted energy/load profile;
- comparison of at least two coordination policies;
- real measurements of communication energy overhead and action delay if instrumentation allows.

Do not connect the prototype to mains wiring, household circuits, EV charging, generators, medical equipment or any safety-critical power system.

## Messina teaching scenario

Create three classroom “energy islands” representing a school node, a rural sensor node and a temporary offline hotspot. Each has a small battery budget and one harmless flexible task.

Example:

```text
Node A: must keep sensor logging alive
Node B: can delay a Wi-Fi content sync
Node C: can run an LED/fan demo when surplus exists
```

Student relays move energy-state summaries between the islands. The class compares what happens when all flexible tasks run immediately versus when delayed information is used to schedule only non-critical work.

A later outdoor experiment could use small solar-powered sensor nodes in a controlled school setting, without making claims about rural-grid reliability.

## Privacy / security

Energy telemetry can reveal occupancy, equipment use and operational patterns.

- use synthetic or coarse energy buckets where exact values are unnecessary;
- authenticate control/action messages;
- keep actuation allow-listed and locally bounded;
- reject stale/replayed action requests;
- separate read-only telemetry from permission to change a load;
- do not expose detailed household/user consumption in student experiments;
- never allow an AI or remote relay to override local safety constraints.

## Difficulty

**High.** The messaging is small, but correct control boundaries, freshness, safe hardware experimentation and meaningful comparison baselines require discipline.

## Research signal

Recent smart-grid research continues to combine LPWAN/LoRa communication with local resilience and demand-response/energy-management architectures. A 2026 Sensors study describes hybrid LoRaWAN/LoRaMESH communication for smart-grid energy management and demand-response applications; 2026 microgrid work also continues to study demand-side management under variable renewable generation. Those systems do not establish PollicinoNet performance. They do show that delayed/local energy coordination is a concrete application domain worth reproducing first in a safe low-voltage emulator.

References:

- https://doi.org/10.3390/s26051714
- https://doi.org/10.1016/j.ecmx.2026.101656
