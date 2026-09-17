# UC-074 — Adaptive Sensor Duty-Cycle and Sampling Policy Ferry

## Idea

Let remote sensor nodes adjust their **ongoing sampling/transmission policy** when battery, backlog, environmental change or network opportunity changes, even if the control path is intermittent.

UC-053 sends a bounded sampling campaign such as "measure every 5 minutes for one hour". UC-074 focuses instead on a longer-lived feedback loop: a node can move between safe policy profiles such as `economy`, `normal`, `high-detail` and `backlog-protect` as conditions evolve.

## Problem solved

A fixed sensing rate is often a bad compromise. Sampling too often wastes energy and storage when nothing changes; sampling too slowly can miss useful detail. In a disrupted network, high-rate sensing can also create a backlog that cannot be ferried out in time.

The system therefore needs a safe way to say things like:

- reduce routine sampling while battery is low;
- temporarily increase detail after a locally detected event;
- reduce transmission frequency when the queue is growing faster than the collector can drain it;
- restore the normal profile when energy/network conditions recover.

The remote network may deliver policy changes late or out of order, so local safety/resource ceilings must always win.

## Actors / nodes

- harmless environmental/teaching sensor nodes;
- student relay/store-and-forward nodes;
- teacher/research coordinator;
- optional UC-003/UC-045 data collector;
- optional UC-031 calibration state;
- optional UC-052 low-voltage energy-budget simulator;
- optional school server for later analysis.

## Why PollicinoNet fits

The policy state is tiny, while the resulting measurements may be much larger.

- **DISCOVERY:** battery/backlog class, active policy profile, `policy update available`;
- **EXACT:** policy ID/version, allowed sensor channels, min/max interval, duration/expiry, local resource ceilings and authorization;
- **SEMANTIC:** human labels like `economy` or `storm-follow-up`, never a substitute for the exact bounded policy.

Store-carry-forward lets a new policy arrive without requiring a live cloud connection. The node can continue operating under the last valid locally safe profile while disconnected.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** policy ID/version, compact resource summary, mode transition, acceptance/rejection and small aggregate status;
- **BLE:** nearby configuration and diagnostics;
- **Wi-Fi/LAN:** full telemetry/history and detailed policy snapshots;
- **Internet:** optional fast path to a coordinator;
- **physical transport:** a relay carries delayed policy updates and later retrieves the resulting data.

## What we can test now in software

Build a deterministic sensor emulator with battery budget, storage queue and a changing synthetic signal.

Compare:

- fixed-rate sensing;
- local-only adaptive sensing;
- coordinator-driven policy epochs;
- hybrid mode where local rules can become more conservative than the remote request but never less safe.

Test:

- policy update arrives late;
- old policy arrives after a newer one;
- duplicate policy delivery;
- battery suddenly drops;
- backlog crosses a threshold;
- signal becomes rapidly changing, then quiet again;
- node reboots while a temporary high-detail mode is active;
- calibration version changes;
- stale authorization or time state;
- malicious request asks for a sample/transmit rate above local limits.

Metrics can include sample count, queue growth, simulated energy use, missed synthetic events, time spent in each policy, stale-policy window and bytes per bearer.

A key invariant is:

> network policy may request a mode, but the sensor's local resource/safety envelope is authoritative.

## What requires real hardware

- 3–5 LoRa boards;
- at least two harmless sensors such as temperature/humidity/light;
- one node with deliberately constrained battery/power-bank budget or a measured power model;
- controlled changes in the sensed signal, for example moving a light source or changing indoor/outdoor placement;
- a moving relay that delays policy updates;
- measurement of real current/energy if energy claims are made.

Do not convert simulated battery savings into physical claims. Real power consumption must be measured on the actual boards and sensor configuration.

## Messina teaching scenario

Place teaching sensors at several controlled checkpoints representing `school`, `Rometta/Venetico` and `Spadafora`. During quiet periods the nodes use a low-detail profile. A synthetic event causes one node to request or locally enter a short high-detail profile, while another node with a growing backlog moves to `backlog-protect` until a student courier drains it.

The class can compare how the same policy behaves under different measured contact opportunities without collecting student home trajectories.

## Privacy / security

- keep precise sensor locations private when they identify homes or sensitive sites;
- authenticate every policy epoch;
- bind policies to exact device/group identities and versions;
- enforce min/max sampling/transmission limits locally;
- do not let a remote policy silently enable a new sensor modality such as microphone/camera;
- separate permission to change sampling policy from firmware/configuration authority;
- expose only coarse battery/backlog classes when exact values are unnecessary;
- preserve an audit trail of accepted/rejected transitions.

## Difficulty

**Medium–High.** The logic is small, but useful evaluation requires a real feedback loop, delayed updates, local safety overrides and eventually measured energy rather than simulated estimates.

## Why this is distinct from UC-053

UC-053 is a finite task: **run this bounded sampling campaign**. UC-074 is a control problem: **which safe long-lived sensing policy should the node be in now, and how do delayed policy epochs converge?**

## Research signal

Adaptive acquisition remains an active 2026 edge/IoT topic. Recent work reports load-aware sampling-frequency adjustment to avoid processing backlog, while other 2026 studies investigate adaptive sensing/transmission to reduce energy and telemetry volume. These results motivate the problem but are not performance claims for PollicinoNet.

References:

- https://journals.sagepub.com/doi/10.3233/FAIA260383
- https://ph03.tci-thaijo.org/index.php/JEIT/article/view/4648
- https://researchportal.ip-paris.fr/en/publications/mobility-entropyaware-adaptive-uwb-sampling-for-energy-efficient-/
