# UC-103 — Adaptive Temporary Relay Placement and Coverage-Gap Trial Planner

## Idea

Use privacy-safe evidence from the real PollicinoNet observatory to propose **where a temporary relay should be tried next**, then validate the proposal with a controlled field experiment.

This is not a promise that a location gives coverage. It is a closed loop:

```text
measured contacts / failures / backlog
        -> candidate checkpoint ranking
        -> temporary relay trial
        -> new measurements
        -> keep / move / reject the candidate
```

A temporary relay can be a board left for a supervised test window, a teacher/student carrying a relay at a coarse checkpoint, or later a safe vehicle-mounted node. The first experiments should use only pre-approved public/school checkpoints.

## Problem solved

Once several student nodes are distributed around Messina and the hinterland, the contact graph may show recurring weakly connected groups or long delivery paths. UC-073 can choose where a mobile courier should go, but sometimes the better intervention is to create a **new rendezvous opportunity** by temporarily placing a relay at a useful checkpoint.

The hard question is not simply "where is the geometric midpoint?". A useful candidate may depend on:

- measured contact opportunities from UC-008;
- real forwarding evidence from UC-098;
- queue pressure and fairness from UC-095;
- recurring schedules from UC-025;
- whether a rich-bearer handoff can actually complete at the checkpoint;
- privacy and participant burden.

## Actors / nodes

- student LoRa relay/store-and-forward nodes;
- school/lab collector;
- UC-008 network observatory;
- optional UC-098 delivery-receipt collector;
- temporary relay board;
- student/teacher carrying or supervising the relay;
- planner that ranks coarse candidate checkpoints.

## Why PollicinoNet fits

PollicinoNet already produces the right evidence to turn relay placement into an empirical experiment rather than a map guess.

- **DISCOVERY:** coarse candidate checkpoint, relay availability, trial epoch, queue-pressure summary;
- **EXACT:** experiment manifest, candidate ID, firmware/config hash, observation window, result/evidence IDs;
- **SEMANTIC:** labels such as `bridge-two-islands` or `reduce-backlog`, used for planning only.

LoRa carries compact trial/control information. Bulk contact traces and evidence move over richer bearers. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** relay advertisements, trial ID, compact contact/backlog summaries, health/status;
- **BLE:** nearby configuration and evidence pickup;
- **Wi-Fi/LAN:** logs, trace upload and firmware/config distribution;
- **Internet:** optional upload to the school observatory when available;
- **physical transport:** the relay board itself is placed or carried to the selected checkpoint.

## What we can test now in software

Take synthetic traces first, then replay measured UC-008 traces when available.

Generate candidate checkpoints and compare simple policies:

1. random safe checkpoint;
2. graph-centrality candidate;
3. candidate that joins two weakly connected communities;
4. backlog-weighted candidate;
5. fairness-aware candidate that improves a persistently underserved group;
6. conservative policy that refuses to recommend a site when evidence is too sparse.

Test failure modes:

- one apparent bridge is caused by a single unusual day;
- contact data are stale;
- a candidate helps delivery for one group but overloads another relay;
- the temporary relay disappears halfway through the trial;
- two candidate checkpoints appear equivalent in simulation;
- an expected rich-bearer transfer does not fit inside the real contact window;
- a recommendation would reveal a participant's home or routine and must therefore be rejected.

Useful software metrics include predicted path/contact improvement, backlog reduction, fairness, candidate sensitivity to missing observations and confidence/uncertainty. These are **planning metrics only**, not physical range or coverage claims.

## What requires real hardware

The first field experiment needs:

- 5–8 distributed boards;
- one extra temporary relay;
- 2–3 pre-approved candidate checkpoints;
- the same bounded workload and experiment manifest for every candidate;
- repeated observation windows at comparable times;
- measured contacts, completed deliveries, relay health, contact duration and packet statistics.

A useful experimental design is A/B/C:

```text
A = no temporary relay
B = candidate checkpoint 1
C = candidate checkpoint 2
```

Only the measured comparison can justify keeping or rejecting a candidate. A simulator recommendation must never be described as demonstrated coverage.

## Messina teaching scenario

Suppose UC-008 shows two coarse communities: one around `school/Messina-Villafranca` and another around `Rometta/Venetico-Spadafora`, with only occasional student-carried bridges.

The planner proposes two safe supervised trial points, for example a school building or another authorized public checkpoint. For one afternoon the same spare board is placed at candidate A; on another comparable day it is placed at candidate B. UC-097 supplies the exact experiment manifest and UC-098 records a bounded sample of actual forwarding receipts.

Students can then answer a concrete engineering question:

> Did either temporary relay create more useful delivery opportunities on our network, under this measured trial, without imposing unacceptable storage, privacy or participant burden?

## Privacy / security

Relay-placement optimization can become location tracking if designed badly.

- use coarse named checkpoints, never home coordinates;
- do not publish individual mobility histories;
- pseudonymize rotating student-node identities;
- require supervised/authorized placement locations;
- authenticate relay configuration and trial manifests;
- enforce volunteer storage/energy budgets from UC-095;
- do not interpret lack of contact as proof that a person was absent;
- avoid ranking students as "good" or "bad" relays;
- keep raw contact traces retention-limited and access-controlled.

## Difficulty

**Medium–High.** Ranking candidate checkpoints is easy; designing a fair, privacy-safe experiment that separates real improvement from day-to-day mobility noise is the harder part.

## Why this is distinct

- **UC-040:** decides where content replicas should be placed.
- **UC-073:** decides where a mobile courier should go next.
- **UC-103:** decides where a **temporary network relay itself should be trialled**, then validates the choice physically.

## Research signal

Relay placement remains an active topic in wireless and sensor networks. A 2026 LoRaWAN study explicitly compares relay-placement strategies, while a September 2026 survey of IoT sensor connectivity highlights coverage/connectivity as a core deployment problem. Their numerical results do not transfer to PollicinoNet; they only reinforce that placement should be treated as an empirical design variable.

References:

- https://www.mdpi.com/2076-3417/16/6/2698
- https://link.springer.com/article/10.1007/s12083-026-02296-6
