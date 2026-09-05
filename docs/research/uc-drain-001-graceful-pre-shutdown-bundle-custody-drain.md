# UC-DRAIN-001 — Graceful pre-shutdown bundle/custody drain

Status: PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE, software-first

## Problem

`UC-ENERGY-001` tries to avoid exhausting the batteries of useful relay nodes. A different situation occurs when shutdown is already expected: the student is about to power the board off, battery is below a hard reserve, a node is entering maintenance, storage is failing, or a fixed relay is about to disappear.

The concrete question is:

> before a node becomes unavailable, can it use its last bounded contact opportunity to hand off the most important bundles/custody state to another authorized peer, improving end-to-end delivery compared with simply disappearing?

This is not a backup of user files (`UC-BACKUP-001`) and not general energy-aware routing. It is a **network-state evacuation/drain** with a known or predicted stop event.

## Actors / nodes

- Pollicino node approaching planned/unplanned shutdown;
- one or more nearby authorized peers;
- destination/gateway that may be reached only later;
- school/home node that can become a preferred stable custodian;
- local battery/storage/maintenance monitor;
- bundle/custody scheduler.

## Why PollicinoNet fits

Pollicino already has exact persistent chunks, PNB1 bundle governance, PNC1 custody and store-carry-forward. A drain can therefore remain a scheduling policy over existing objects rather than inventing another transport.

A minimal trigger can be local:

```text
shutdown_deadline_s
energy_reserve_state
storage_health
maintenance_requested
```

A minimal scheduler can begin with simple baselines:

1. do nothing;
2. FIFO drain;
3. earliest application deadline first;
4. highest priority first;
5. custody-first / least-replicated first.

Only measured failure of these policies would justify richer optimization.

## Possible bearers

- LoRa: last opportunistic handoff to another student/fixed node;
- BLE: nearby high-throughput local drain if both devices support it;
- Wi-Fi/LAN: preferred when a stable home/school node is available;
- physical carry: relevant before shutdown because the student may carry the node into a richer environment, but once powered off no further radio progress exists.

## What we can test immediately in software

Create a deterministic schedule where node B is a relay for many bundles but disappears at `t=1000`.

Give B:

- finite queued bytes;
- bundle priorities/deadlines;
- different replica counts;
- custody records;
- one short contact with C before shutdown;
- destination contacts that occur only after B disappears.

Compare the simple drain policies above.

Inject:

- planned shutdown with known deadline;
- surprise early shutdown;
- contact shorter than the queued state;
- destination already has some chunks;
- peer refuses custody;
- reboot during drain;
- low battery where retransmissions consume the remaining budget;
- stale duplicate contact after restart.

Metrics:

- bundles/objects rescued that would otherwise be lost or delayed;
- useful destination deliveries after the draining node disappears;
- scarce-link bytes spent during drain;
- duplicate bytes;
- custody correctness;
- energy proxy used by the final handoff;
- percentage of critical/deadline objects rescued;
- state left behind at shutdown.

## Messina student-network scenario

A very concrete student pilot is the end-of-day transition:

```text
school mesh
   |
student leaves school
   |
board battery/usage policy predicts shutdown before evening
   |
last contact with another student or school gateway
   |
important synthetic bundles are drained
   |
original board powers off
```

Another safe scenario is a fixed sensor relay scheduled for maintenance while students continue to carry data between logical `Rometta-like`, `Spadafora-like`, `Saponara-like` and `Villafranca-like` clusters.

No town label implies RF reachability.

## What requires real hardware

After HW-006:

- actual voltage/current thresholds and brownout behavior;
- time between low-battery trigger and real shutdown;
- flash/persistence integrity across sudden power loss;
- measured energy cost of a final LoRa/BLE/Wi-Fi handoff;
- battery impact of retries;
- real drain completion probability under measured contact windows.

A separate destructive/recovery test should intentionally cut power during checkpoint/custody updates and verify restart behavior.

## Privacy and security

- drain only bundles the receiving peer is authorized to store/forward;
- do not bypass application visibility/consent merely because a node is low on battery;
- preserve object identity and custody provenance across handoff;
- peer refusal must be explicit; a source must not delete state on an unconfirmed transfer;
- sensitive payloads require encryption independent of custody;
- the shutdown trigger itself should reveal no more personal/device usage information than needed.

## Difficulty

**Medium in software; medium-high on hardware** because power-loss timing and atomic persistence become real failure modes.

## Success / kill criteria

Continue if a simple bounded drain policy produces materially more successful post-shutdown delivery than no-drain, without excessive duplicate bytes or violating custody correctness.

Do not add complex predictive routing if `deadline/priority/custody-first` policies capture almost all benefit.

## Related-work note

DTN architecture has long treated custody/retention state as explicit protocol state. PollicinoNet already implements local custody. This use case asks a narrower operational question: how to use that state when a node has a known disappearance deadline.

## Physical evidence boundary

Synthetic shutdown time and energy are model inputs only. Real low-battery thresholds, final-contact capacity, battery life and drain success require physical measurements after HW-006. The frozen LoRa PHY remains unchanged.