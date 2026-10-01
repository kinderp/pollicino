# UC-143 — Partition-Aware Liveness and Failure-Suspicion Courier

## Idea

Distinguish **"I have not heard from this node"** from **"this node is failed"** in a network where disconnection is normal.

Instead of turning a missed heartbeat into an immediate failure, nodes exchange compact liveness evidence, last-seen epochs and suspicion state. A node can move through states such as `ALIVE`, `SUSPECT`, `UNKNOWN/PARTITIONED`, `RECOVERED` and, only under an explicit local policy, `FAILED_FOR_THIS_SERVICE`.

## Problem solved

In a student-carried DTN, a board can disappear simply because its owner changed town, entered a building, powered the device down, lost battery or never met a relay. Treating absence as failure can trigger bad actions: duplicate jobs, unnecessary repair tickets, premature replica deletion or incorrect robot/sensor reassignment.

The useful question is therefore not "is node X online now?" but "what evidence do we currently have about X, how old is it, and what decisions are safe under that uncertainty?"

## Actors / nodes

Student relay nodes, fixed school/lab nodes, sensors, robots, service coordinators, optional clock-quality source from UC-123 and experiment observer.

## Why PollicinoNet fits

PollicinoNet already assumes intermittent connectivity, so it can carry **bounded liveness evidence** rather than requiring end-to-end reachability. A compact record can include node/service pseudonym, boot/session epoch, last direct contact, last indirect witness, freshness class, suspicion reason, evidence age and policy-specific decision state.

The mechanism is application/control-plane logic only. The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: compact liveness beacon, witness summary, boot epoch and suspicion/recovery state.
- BLE: local direct-proximity confirmation.
- Wi-Fi/LAN: richer diagnostics and logs after a node is reachable.
- Internet: optional external reachability evidence, never required for correctness.
- Physical transport: SD/log bundle or the device itself for later diagnosis.

## What we can test now in software

Simulate 20–100 virtual nodes with realistic partitions. Inject normal absence, hard power-off, reboot with a new boot epoch, stale relays, duplicate evidence, contradictory witnesses, clock uncertainty and delayed `RECOVERED` messages.

Compare naive fixed heartbeat timeout, timeout with explicit `UNKNOWN`, accrual/suspicion scoring based on observed inter-contact history, and service-specific policy where a node can be unavailable for one deadline-sensitive task without being declared globally failed.

Measure false-failure declarations, time spent in `UNKNOWN`, unnecessary task reassignment and number of bytes of liveness metadata.

## What requires real hardware

Use 6–10 LoRa boards. Deliberately power one node off, reboot another, keep one physically isolated for a period and let another move normally between groups. Record only the experiment contacts needed to evaluate the state machine.

The physical test must measure the actual inter-contact distribution before choosing thresholds. No timeout or detection accuracy should be claimed from simulation alone.

## Messina teaching scenario

Create three groups around Messina, Villafranca and Rometta/Venetico-Spadafora. A board absent for half a day must not automatically be labeled broken. When a relay later meets it, a new boot/session epoch or direct liveness record can clear suspicion and propagate `RECOVERED` through the network.

This is especially useful if student nodes later host cached content, sensor jobs or temporary services.

## Privacy / security

Use experiment-scoped pseudonyms, coarse time buckets when exact timing is unnecessary and no continuous location history. Authenticate liveness evidence so another node cannot cheaply forge state for a victim. Rate-limit witness propagation and distinguish direct observations from hearsay.

A node must never be punished or ranked personally because it is often unreachable; student mobility and device participation are voluntary experimental resources.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-008 observes contact opportunities. UC-062 carries crash diagnostics. UC-089 tracks alarm lifecycle. UC-113 creates maintenance tickets. UC-143 instead addresses the distributed-systems question of **failure suspicion under normal partitions**, before any diagnosis or repair workflow begins.

## Research / standards signal

Failure detectors in asynchronous systems commonly distinguish suspicion from certainty because timing alone cannot prove a remote process has failed. This becomes even more important in DTNs, where long disconnections are expected behavior rather than exceptional faults.

References:

- https://doi.org/10.1109/DSN.2004.1311885
- https://www.rfc-editor.org/rfc/rfc9171.html
