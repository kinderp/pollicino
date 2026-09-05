# UC-GAME-001 — Opportunistic relay challenge for teaching and field testing

Status: PROTOTYPE / EDUCATIONAL TEST HARNESS

## Problem

A real student network needs repeatable traffic that is safe, understandable and engaging enough to run during a supervised field pilot. Pure synthetic background packets are useful for benchmarks but do not test whether students can actually carry, exchange and interpret network state.

An opportunistic relay challenge turns store-carry-forward into a small game: signed test tokens or puzzle fragments must reach one or more **logical roles/cohorts** and return to a referee before a deadline. The game generates known, harmless traffic while teaching why a DTN can work without a continuous route.

This is not `UC-TRACE-001`: TRACE observes the temporal graph. GAME creates a controlled application workload that can later be evaluated using TRACE.

## Actors / nodes

- school referee node;
- student-carried Pollicino nodes grouped into pseudonymous teams/cohorts;
- optional fixed classroom/lab checkpoint nodes;
- optional teacher dashboard using aggregate results only.

## Messina educational scenario

At school in the morning the referee emits test token `T7` with a rule such as:

```text
visit three distinct pseudonymous relay roles
then return to the referee before the next school morning
```

or distributes different puzzle fragments that must converge at school the next day.

Students do **not** travel specifically to chase geographic checkpoints. The exercise uses ordinary school/home movement and logical encounter roles. Public town names may label synthetic cohorts, but the score must never reward distance from home or reveal where a student lives.

## Why PollicinoNet fits

The challenge directly exercises:

- stable object identity;
- duplicate/replay rejection;
- store-carry-forward;
- hop/custody history or bounded proof tokens;
- application deadline;
- morning mesh versus afternoon DTN lifecycle;
- finite storage and scheduling when several tokens compete;
- later Wi-Fi results upload without changing token identity.

Because the expected token graph is known, the game can also become a reproducible acceptance test for cross-bearer behavior.

## Possible bearers

- LoRa for tokens, puzzle fragments and acknowledgements;
- BLE for optional close checkpoint interaction;
- Wi-Fi/LAN at school/home for dashboards or rich hints;
- Internet optional for teacher-side aggregation;
- physical movement as the main carry mechanism.

## What can be tested now in software

1. signed unique game-token fixtures;
2. required distinct-role visits without geographic location;
3. deadline/expiry;
4. replayed or cloned token attempts;
5. two teams exchange the same fragment;
6. referee unavailable until next morning;
7. controlled load levels: 1, 10, 100 tokens;
8. compare Direct Delivery, Spray-and-Wait, PRoPHET and destination-recency strategies;
9. score only application completion, while separately recording network bytes/forwards;
10. verify that `CONNECTED_MESH -> OPPORTUNISTIC_DTN -> RICH_HOME` transitions do not mutate token identity.

A useful first software scenario is a known temporal graph where exactly one physical-carry bridge is needed; the game should succeed only when the token survives that partition.

## What requires real hardware

After HW-006 and school/privacy governance, boards are required to learn:

- whether the exercise is understandable and practical for students;
- actual encounter opportunities under normal movement;
- device handling/reboot robustness;
- battery impact;
- real token-delivery latency;
- real LoRa/BLE contact behavior;
- whether a controlled workload is enough to reproduce simulator expectations.

## Privacy / security / safety

- no GPS required;
- no home address or exact route in token payloads;
- pseudonymous teams and short-lived identifiers;
- no public per-student mobility leaderboard;
- score application events, not distance or movement speed;
- do not incentivize students to travel, approach unsafe areas or alter normal routes;
- signed/referee-issued tokens to limit cheating/replay;
- do not infer social relationships from relay chains;
- aggregate/de-identify teaching results;
- first pilot should use only synthetic content.

## Implementation difficulty

**Low-medium.** The network objects are intentionally simple. Most work is safe game design, token validity and a small referee/score harness.

## Minimal measurable hypotheses

- H1: a game workload produces controlled, explainable store-carry-forward traffic suitable for a first student field experiment.
- H2: students can observe the difference between contemporaneous mesh delivery and delayed physical carry without needing a continuous Internet path.
- H3: the same token fixtures can be replayed in simulation and on later physical traces, making the exercise useful as both teaching and validation.

## Metrics

- challenge completion rate;
- completion latency;
- number of distinct relay roles visited;
- forwards/copies per token;
- LoRa bytes per completed challenge;
- replay/invalid-token rejection;
- storage pressure;
- fraction completed in mesh-only versus carry-required scenarios;
- simulator-versus-field outcome difference once field evidence exists.

## Success / kill criterion

**Continue** if the game creates a safe workload with known expected behavior and modest implementation cost.

**Kill/redesign** any scoring rule that pressures movement, exposes student location/social data, or produces no networking insight beyond ordinary test packets.

## Gate decision

**PROTOTYPE.** This is a particularly good candidate for the first supervised student-network application after HW-006 because it can use synthetic content and can be designed not to collect personal location data.
