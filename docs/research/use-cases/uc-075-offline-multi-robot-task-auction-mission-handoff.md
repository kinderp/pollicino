# UC-075 — Offline Multi-Robot Task Auction and Mission Handoff

## Idea

Let several intermittently connected robots or robot-like worker nodes decide **who should perform a task** without assuming a permanently reachable central coordinator.

UC-010 already gives a known robot an asynchronous mission mailbox. UC-014 discovers capabilities. UC-075 composes those ideas into a new question:

> when several capable nodes could do the job, how do they advertise bids, reach a bounded assignment and recover if the selected worker disappears?

The first implementation does not need real mobile robots. LEDs, simulated workers or stationary boards can represent task executors safely; physical robots come later.

## Problem solved

A fixed assignment is inefficient when nodes differ in:

- current queue length;
- battery/resource state;
- distance or expected contact opportunity;
- required capability;
- locally cached model/map/tool;
- temporary fault or unavailability.

A coordinator may also be disconnected from some workers. The task allocation therefore needs to tolerate delayed bids, duplicate messages and a winner that becomes unreachable.

## Actors / nodes

- task originator/coordinator;
- 2 or more robot/worker nodes;
- student relay/store-and-forward nodes;
- optional capability directory from UC-014/UC-067;
- optional trusted time/freshness from UC-020;
- optional quorum approval from UC-071 for sensitive demo actions;
- optional richer-bearer content cache for maps/models needed by a mission.

## Why PollicinoNet fits

Task descriptions and bids can be compact while mission assets may be large.

- **DISCOVERY:** `task available`, worker capability summary, bid invitation, worker health/availability;
- **EXACT:** task hash/version, bid ID, bidder identity, cost components, assignment epoch, winner token and mission result hash;
- **SEMANTIC:** labels like `inspect`, `carry`, `sample`, `compute`, used for matching but never as the authoritative mission identity.

Store-carry-forward is useful because bids need not arrive simultaneously. A relay can carry a task invitation to one worker and return its signed bid later. Rich bearers can then transfer maps, models or larger mission inputs.

The LoRa PHY remains frozen.

## Possible bearers

- **LoRa:** capability hints, task invitation, compact bids, assignment/cancel/re-auction state, progress/health summaries;
- **BLE:** nearby robot discovery and moderate control/state exchange;
- **Wi-Fi/LAN:** maps, models, logs and mission assets;
- **Internet:** optional fast path or remote dashboard;
- **physical transport:** a student relay carries pending auction/assignment objects between otherwise disconnected worker islands.

## What we can test now in software

Start with deterministic virtual workers and a simple auction rather than ML bidding.

Implement:

- exact `TaskOffer` with deadline, required capabilities and resource hints;
- signed `TaskBid` containing one or more transparent cost components;
- finite bid window with explicit uncertainty;
- deterministic winner selection;
- duplicate/reordered bid handling;
- late bid after assignment;
- worker goes offline after winning;
- task cancellation and re-auction;
- two coordinators accidentally advertising the same task;
- worker reboot with persisted assignment state;
- mission handoff from failing worker A to replacement B;
- dependency on an exact model/map artifact that the winning worker must fetch first;
- compare centralized immediate assignment, nearest-worker, lowest-queue and simple auction baselines.

Useful metrics include assignment latency, duplicate execution count, failed assignment rate, re-auction count, task completion time, fairness and control bytes.

Key invariants:

> one exact task must not silently become two independent missions because duplicate assignment messages arrived.

and

> a lower bid is only a scheduling preference; local robot safety constraints remain authoritative.

## What requires real hardware

Stage 1, safe tabletop test:

- 4–6 PollicinoNet boards;
- 2–3 boards act as worker nodes with LEDs or harmless scripted jobs;
- one task originator and one moving relay;
- deliberately delay one worker's bid and disconnect the winner after assignment;
- verify re-auction and idempotent execution.

Stage 2:

- 2 or more small educational robots in a controlled indoor area;
- missions limited to harmless actions such as reaching a marker, taking a sensor reading or carrying a light object;
- richer-bearer transfer of maps/assets if needed;
- real measurement of communication delay and mission completion.

Do not use this prototype for safety-critical navigation, public-space autonomous operation or any actuator where delayed/stale commands could cause harm.

## Messina teaching scenario

Three student groups represent worker islands in `Messina`, `Villafranca` and `Rometta/Venetico`. A synthetic mission asks for a temperature reading at a controlled checkpoint. Two worker nodes advertise the required sensor capability, but one has a longer queue and another lacks the latest calibration artifact.

The invitation and bids travel through student relays. The coordinator selects a winner, then that worker is intentionally made unavailable so the task is re-auctioned. The class checks whether only one final exact result is accepted.

A later robotics lab can replace virtual workers with small indoor robots without changing the delay-tolerant task/auction objects.

## Privacy / security

- use pseudonymous device identities rather than student names;
- authenticate tasks, bids, assignments and cancellations;
- scope who may create tasks and which worker capabilities may be invoked;
- never allow a relay to modify a bid or become the task authority merely by carrying it;
- protect sensitive location/mission metadata;
- rate-limit task creation to prevent queue exhaustion;
- make stale assignment and stale cancellation states explicit;
- keep human emergency/safety decisions outside the prototype.

## Difficulty

**High.** The basic auction is simple, but correctness under delayed bids, re-auction, duplicate delivery, worker failure and mission handoff is a substantial distributed-systems exercise.

## Why this is distinct from UC-010 and UC-014

- **UC-010:** queue a mission for a known intermittently connected robot.
- **UC-014:** discover available compute/storage/service capabilities.
- **UC-075:** choose among several candidate workers through delayed bids, create one exact assignment and recover if that assignment fails.

## Research signal

Multi-robot task allocation remains an active 2026 research area, including auction/consensus approaches designed for limited communication and event-triggered reallocation after faults or changing priorities. PollicinoNet should borrow the simple auction pattern first and validate its own delay/reorder behavior rather than importing optimization results from tightly coupled robot networks.

References:

- https://arxiv.org/abs/2605.21932
- https://arxiv.org/abs/2603.21545
- https://benrossano.com/projects/uncertainty_aware_mrta/
