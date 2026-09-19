# UC-084 — Multi-Robot Map Fragment and Pose-Graph Ferry

## Idea

Let robots or mobile mapping nodes explore different areas while disconnected, then exchange **compact map metadata first and large map fragments later** when a richer bearer or physical rendezvous becomes available.

The goal is not to stream LiDAR/camera data over LoRa. LoRa carries only small descriptors, map-fragment identities, overlap hints and merge state; occupancy grids, point clouds, images or submaps move later over Wi-Fi/LAN/BLE or by physical carry.

## Problem solved

UC-075 allocates tasks among multiple robots, but after separate robots perform those tasks they may each hold only a partial view of the environment.

A collaborative mapping workflow needs to answer:

- which robot has a map fragment I have not seen?
- do two fragments probably overlap?
- which exact fragment/version produced this loop-closure hint?
- can merge work continue even if the robots meet hours later?
- what happens when two candidate merges conflict?
- can we avoid moving every raw scan merely to discover that a merge is unnecessary?

This is especially relevant when communication is intermittent or constrained.

## Actors / nodes

- two or more robots or mapping devices;
- optional fixed school/lab mapping node;
- student relay/store-and-forward nodes;
- optional edge computer that performs expensive map merging;
- optional UC-075 mission coordinator;
- optional UC-061 computation-result cache for deterministic preprocessing results.

## Why PollicinoNet fits

Map data is large, but coordination state can be compact.

- **DISCOVERY:** map/session ID, coarse area, descriptor availability, approximate overlap hint, fragment count;
- **EXACT:** fragment hash, map-session/version ID, coordinate-frame identity, calibration hash, pose-constraint identity and merge-result hash;
- **SEMANTIC:** labels such as `corridor-A`, `lab-west`, `robot-2-session-3`, useful for humans but not authoritative for fusion.

LoRa can tell peers that useful mapping evidence exists. Rich bearers transport only the exact fragments selected for merge.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** fragment/session IDs, descriptor hashes, coarse bounding region, overlap candidate, pose-constraint summary, merge status;
- **BLE:** nearby exchange of descriptors and small map summaries;
- **Wi-Fi/LAN:** occupancy grids, point clouds, image keyframes, calibration data and full pose-graph fragments;
- **Internet:** optional fast path to a central mapping workstation;
- **physical transport:** robot/laptop/SD card carries full mapping data between disconnected islands.

## What we can test now in software

Start without real robots by replaying two or more public/synthetic trajectories and map fragments.

Define a `MapFragmentManifest` with at least:

```text
robot_id
map_session_id
fragment_id
fragment_hash
frame_id
calibration_hash
coarse_region
descriptor_hash
created_checkpoint
```

and optional `MergeConstraint` objects:

```text
fragment_a
fragment_b
constraint_type
relative_pose
uncertainty
producer
constraint_hash
```

Test:

- two robots produce non-overlapping fragments;
- overlapping fragments are discovered only after delayed descriptor exchange;
- descriptors suggest an overlap but exact verification rejects it;
- one robot reprocesses a fragment under a new calibration/version;
- map fragments arrive before their metadata or vice versa;
- duplicate fragment transfer is suppressed;
- conflicting loop-closure candidates are preserved instead of silently overwritten;
- only selected keyframes/submaps are requested after a compact overlap hint;
- a central merge node disappears and a different edge node continues the job;
- large map evidence remains unavailable while the control plane still converges.

Metrics include bytes moved before a useful merge candidate is found, selected-fragment ratio, time-to-merge-candidate, redundant transfer, unresolved conflict count and final merge-evidence completeness.

A useful invariant is:

> a merge result is never treated as authoritative unless it identifies the exact input fragments, coordinate frames and calibration versions that produced it.

## What requires real hardware

The first physical experiment does not require expensive LiDAR:

- two small robots, phones or laptops moving through different parts of a controlled indoor environment;
- 2–4 LoRa nodes for discovery/control;
- Wi-Fi for actual map/image transfer;
- one workstation for merge visualization.

A safe progression is:

1. replay pre-recorded maps on stationary machines;
2. collect simple occupancy/image maps with supervised indoor robots;
3. only later test autonomous mapping behavior.

Real robot motion must remain slow, supervised and physically bounded.

## Messina teaching scenario

Use a school building or lab as a controlled map. One Romeo-class robot explores one corridor while another device explores another room. The devices are deliberately prevented from using continuous Wi-Fi.

A student relay later brings their compact fragment inventories together over PollicinoNet. Only when a plausible overlap is detected is a rich bearer opened to move the selected fragments. The class can then compare:

```text
transfer-everything
vs
advertise-first / request-selected-fragments
```

No outdoor autonomous navigation is needed for the first experiment.

## Privacy / security

Maps can reveal sensitive physical layouts.

- use school/lab spaces explicitly approved for the experiment;
- avoid private homes, faces, readable documents and precise security-sensitive layouts;
- do not broadcast detailed coordinates or raw imagery over LoRa;
- bind calibration and coordinate-frame identities exactly;
- authenticate fragment producers when results influence later robot planning;
- treat third-party map fragments as untrusted until validated;
- never let an unverified merge directly drive unsafe autonomous motion.

## Difficulty

**High.** The PollicinoNet metadata path is manageable; robust map fusion, coordinate-frame handling and false-overlap rejection are the hard parts.

## Why this is distinct from nearby use cases

- **UC-010:** queues missions for one robot.
- **UC-075:** allocates missions among several robots.
- **UC-060:** ferries visual survey evidence without collaborative map state.
- **UC-084:** makes **partial robot maps and pose constraints themselves delay-tolerant collaborative artifacts**.

## Research / implementation signal

Recent multi-robot SLAM work continues to focus on communication-efficient map merging and asynchronous collaboration under constrained links. A September 2026 IJRR paper on Commerge explicitly treats map exchange bandwidth as a central bottleneck, while 2026 work on asynchronous collaborative LiDAR SLAM studies pose-graph cooperation under latency and packet loss. PollicinoNet should not import their performance claims; the useful signal is that compact discovery followed by selective exact map transfer is a real robotics problem.

References:

- https://doi.org/10.1177/02783649261464202
- https://doi.org/10.1109/LRA.2026.3655282
