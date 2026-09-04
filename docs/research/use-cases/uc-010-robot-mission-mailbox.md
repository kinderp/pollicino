# UC-010 — Robot Mission Mailbox

## Idea

Treat a robot or small vehicle as an intermittently connected worker with a **mission mailbox**. Operators enqueue compact signed jobs; PollicinoNet carries mission IDs, priorities, expiry and acknowledgements over scarce links, while richer links later move maps, logs, images or software artifacts.

A concrete teaching demo could integrate a simple Romeo-class rover in the lab: the rover loses Wi-Fi, receives a queued non-safety-critical mission through a PollicinoNet relay, executes it locally, then returns a compact result summary before uploading richer evidence when Wi-Fi is available again.

## Problem solved

Robots and mobile devices often move in and out of connectivity. A permanent remote-control session is fragile and bandwidth-hungry. Many useful tasks can instead be represented as idempotent jobs that survive disconnections and are acknowledged later.

## Actors / nodes

- operator/teacher station;
- robot or rover;
- student-carried relay nodes;
- optional fixed school gateway;
- optional camera/sensor payload on the robot.

## Why PollicinoNet fits

PollicinoNet already supports store-and-forward, TTL, duplicate suppression, exact objects and opportunistic handover. Mission envelopes are small enough for scarce-link control, while photos/video/logs naturally move later via BLE/Wi-Fi/LAN/Internet. This exercises the network layer without modifying the frozen LoRa PHY.

## Possible bearers

- **LoRa:** mission coordinate/envelope, status, progress code, compact telemetry, acknowledgement;
- **BLE:** close-range mission/result exchange;
- **Wi-Fi/Internet:** maps, images, logs, software and larger datasets;
- **physical transport:** carried storage or a relay node can move queued jobs/results between disconnected islands.

## What we can test now in software

- robot mission queue with unique IDs, TTL and priorities;
- idempotency: receiving the same mission twice must not execute it twice;
- acknowledgement and retry policies;
- simulated connectivity loss during mission delivery and result return;
- exact-result manifests for logs/evidence;
- distinction between `mission accepted`, `started`, `completed`, `failed` and `expired`;
- multi-hop relay of mission/result envelopes.

## What requires real hardware

- controlled rover on a safe indoor course;
- real LoRa delivery of non-critical jobs and status messages;
- measured latency, packet loss and queue behavior during movement;
- Wi-Fi/BLE handover for richer result data;
- later experiments with a vehicle or drone only under the relevant safety and legal constraints.

The experimental network must **not** be used as the sole emergency-stop or collision-avoidance channel. Those functions remain local/safety-rated.

## Privacy / security

Require authenticated commands, authorization by robot/mission class, replay protection, expiry and a clear audit log. Do not expose camera evidence or precise movement traces in public LoRa frames. A compromised relay must not be able to invent a valid mission.

## Difficulty

**Medium–High.** The mailbox/state-machine logic is approachable; secure command authorization and safe physical integration need care.
