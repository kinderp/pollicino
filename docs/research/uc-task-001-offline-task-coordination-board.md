# UC-TASK-001 — Offline task and volunteer coordination board

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING, EMERGENCY-ADJACENT

## Problem

A disconnected group may need to create, claim, complete and reopen small tasks while different clusters are temporarily partitioned. A plain broadcast is not enough: two nodes can claim the same job while disconnected, a completed task can reappear from stale state, or a deadline can pass before a delayed update arrives.

The concrete networking problem is therefore **reconciling a small task state machine under partitions**, with explicit conflict, lease and deadline semantics.

This is different from `UC-EMERG-001` (publish an authenticated notice) and `UC-ASSET-001` (reserve a physical resource). A task is work to be performed and progresses through a lifecycle.

## Actors / nodes

- task authority/referee, initially a school or laboratory node;
- student/volunteer nodes able to claim tasks;
- student-carried relays;
- optional fixed sensor/checkpoint nodes that can acknowledge completion;
- optional Civil Protection exercise coordinator in a future separately governed drill.

## Messina educational scenario

Start with harmless laboratory tasks such as:

- collect a public sensor reading from checkpoint `S3`;
- carry a configuration fixture to a fixed lab node;
- verify that a public information card exists at a checkpoint;
- return a signed synthetic completion token by the next school morning.

Students in pseudonymous territorial clusters receive and carry task cards during normal movement. The next morning's school mixing phase reconciles claims/completions.

A later research scenario can model a Civil Protection drill with synthetic tasks such as `inspect-zone-A-marker` or `deliver-public-bulletin-B`, but PollicinoNet must not be presented as an operational emergency-dispatch system without independent validation and authorization.

## Why PollicinoNet fits

Task cards are compact but their state changes matter. PollicinoNet already studies:

- store-carry-forward;
- deadlines distinct from transport TTL;
- signed/provenance-aware objects;
- reconciliation of partial state;
- finite storage and priority scheduling;
- repeated school/territorial mixing;
- explicit time uncertainty (`UC-TIME-001`) when lease/deadline logic needs it.

This use case can also discriminate simple reconciliation policies before any CRDT or new protocol is justified.

## Possible bearers

- LoRa for task IDs, state transitions, claim/complete tokens and acknowledgements;
- BLE for local checkpoint interaction if useful;
- Wi-Fi/LAN for richer forms, maps or evidence;
- Internet for optional authoritative synchronization;
- physical movement as the delayed bridge between clusters.

## What can be tested now in software

Use a minimal state machine such as:

```text
OPEN -> CLAIMED -> DONE
  |        |
  |        +-> EXPIRED -> OPEN
  +--------------------> CANCELLED
```

Test, in order:

1. authoritative-hub baseline: only the hub resolves competing claims;
2. generation-number baseline with first-valid-claim semantics;
3. bounded leases with explicit clock uncertainty;
4. concurrent offline claims and delayed merge;
5. task completion arriving before a stale claim;
6. cancellation/reopen propagation;
7. priority/deadline scheduling under scarce contact bytes;
8. duplicate and replayed completion tokens;
9. task relevance filters by role/topic/coarse zone;
10. optional CRDT-like reconciliation only if simpler policies fail a measured requirement.

A useful experiment is to partition three student clusters for an afternoon, inject conflicting claims, and measure how many invalid/double claims remain when the school mixing hub is reached the next morning.

## What requires real hardware

Boards are needed before claiming:

- real task-delivery or completion latency;
- whether students encounter enough relay opportunities for a useful workflow;
- actual bytes exchanged during a contact;
- checkpoint usability over LoRa/BLE;
- battery cost of task scanning/relay;
- behavior during a real supervised field drill.

HW-006 remains the first RF gate.

## Privacy / security

- task origin and important state transitions must be authenticated;
- use role/pseudonym identifiers rather than named students on the shared network;
- avoid exact home addresses or sensitive infrastructure coordinates;
- do not publish a per-student movement/history log from task progress;
- expiry/lease logic must fail safely when time is uncertain;
- replayed `DONE`, `CANCELLED` or old-generation states must not resurrect work;
- operational emergency tasks require an authoritative source and separate governance;
- no safety-critical instruction should depend only on this experimental DTN.

## Implementation difficulty

**Medium.** The message sizes are small. Correct conflict, causality, lease and authority semantics are the important work.

## Minimal measurable hypotheses

- H1: a bounded task lifecycle can converge across afternoon partitions using existing bundle/reconciliation primitives.
- H2: explicit generation + lease semantics prevent most double-work without requiring a general-purpose distributed database protocol.
- H3: application deadline and priority materially change which tasks remain useful under scarce contacts.

## Metrics

- tasks delivered before deadline;
- claim conflicts created/resolved;
- duplicate work count;
- stale-state resurrection count;
- convergence time after partitions join;
- bytes per task transition;
- relay forwards/storage;
- invalid/replayed transition rejection;
- fraction of tasks completed before the next school mixing phase.

## Success / kill criterion

**Continue** if a simple generation/lease design safely resolves synthetic partitions and provides a workload that distinguishes routing/scheduling choices.

**Reject/defer** any more complex replicated-state mechanism if the authoritative/simple baseline performs equivalently for the target scale.

## Gate decision

**PROTOTYPE / CONTINUE.** This is one of the strongest new student-network workloads because it is useful in class, measurable, and later extensible to supervised emergency exercises without requiring that the experimental network become a safety system.

## Related precedent

Recent emergency-management research explicitly studies offline/weakly connected mobile nodes and eventual state convergence, including CRDT-based replication, while noting timestamp/delete/causality challenges: https://doi.org/10.5324/b816jf45 .

Disaster-response literature also treats volunteer-to-task assignment as a real coordination problem; that motivates the application need but does not validate PollicinoNet for operational response.
