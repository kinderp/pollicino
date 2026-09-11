# UC-045 — Buffer-Aware Mobile Data Harvester

## Idea

Turn a moving PollicinoNet node into a **smart collector that decides what to download first during a short contact**, based on queue pressure, age, priority, expiry and the observed quality of the current encounter.

UC-005 already establishes the generic mobile gateway/data-mule idea. UC-045 narrows the research question to **adaptive harvesting policy during scarce contact windows**.

Start with a person or bicycle carrying the collector. Vehicles and UAVs are later variants only after the policy works in simulation and safe ground experiments.

## Problem solved

A mobile collector may meet a sensor/node for only a short time while that node has a large backlog.

A naive strategy such as "download FIFO until contact disappears" can waste the encounter:

- old low-value records may block urgent data;
- a nearly full sensor buffer may lose new evidence;
- a large object may start but never finish;
- the next node on the route may have even more urgent data;
- contact quality can change quickly.

The collector should be able to choose **which exact queued objects/chunks to harvest now** and resume the rest later.

## Actors / nodes

- fixed sensor/IoT nodes with persistent backlog;
- student-carried walking/bicycle collector;
- optional school gateway/server;
- future vehicle/UAV collector;
- optional route planner using coarse expected contacts;
- multiple queues competing for limited collector storage/time.

## Why PollicinoNet fits

PollicinoNet already models store-and-forward queues, exact content identity and intermittent contacts. UC-045 adds a scheduling policy at encounter time.

- **DISCOVERY:** compact queue summary, urgency class, buffer pressure and transferable-object hints;
- **EXACT:** object/chunk IDs, resume frontier, expiry and verification;
- **SEMANTIC:** optional labels such as `telemetry`, `evidence`, `routine`, used only for policy/ranking and never to replace exact identity.

The scarce radio can negotiate what should move first; a richer bearer can transfer the larger backlog when available.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** queue summary, priority/expiry, resume bitmap/frontier, collector intent and small urgent records;
- **BLE:** moderate nearby backlog exchange;
- **Wi-Fi:** high-rate backlog transfer during close contact;
- **Internet:** later upload from the collector to the school/server;
- **physical transport:** the collector carries stored objects between isolated nodes and the sink.

## What we can test now in software

Extend the contact simulator with finite queues and finite contacts.

Compare policies such as:

- FIFO;
- oldest-first;
- earliest-expiry-first;
- smallest-completable-object-first;
- highest-priority-first;
- buffer-pressure-aware;
- age-of-information-aware;
- fairness-constrained priority;
- simple link-aware policy using only measured/estimated contact state available at runtime.

Inject:

- sudden contact loss;
- incorrect contact-duration estimates;
- node buffer overflow;
- one very large object mixed with many small ones;
- repeated visits to the same node;
- multiple fixed nodes competing for collector storage;
- resumable partial objects;
- stale queue summaries.

Measure collected useful bytes, completed-object rate, dropped-before-collection records, age of information, deadline misses, fairness, wasted partial-transfer bytes and collector storage pressure.

## What requires real hardware

First stage:

- 3–5 fixed boards with intentionally different backlogs;
- one walking/bicycle collector;
- repeatable passes with controlled start/end points;
- deliberately short contacts where not everything can be transferred;
- real measurements of packet delivery, RSSI/SNR, airtime, contact duration and completed objects;
- compare at least two scheduling policies on the same controlled route.

Second stage:

- optional richer bearer for backlog bulk transfer;
- optional vehicle only with safe/legal procedures;
- UAV only much later and only with the relevant permissions and flight-safety constraints.

No UAV or range claim may be inferred from software results.

## Messina teaching scenario

Create several fixed sensor nodes in controlled school/home-lab locations representing coarse zones such as `Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora`.

Each node accumulates a synthetic backlog with different urgency and expiry. A student collector follows a known route and has only brief contacts. The class predicts which records each policy will choose, then compares the prediction with the actual harvested queue and measured contacts.

A later exercise can replay the exact UC-008 contact traces in software before repeating selected schedules physically.

## Privacy / security

Queue summaries themselves may reveal activity levels or event timing.

- advertise only the minimum scheduling metadata;
- encrypt sensitive payloads end-to-end so the collector can carry without reading;
- avoid exposing exact student movement trajectories as route telemetry;
- use controlled/coarse routes and rotating identities;
- authenticate priority classes so a node cannot trivially mark everything as urgent;
- impose per-source quotas/fairness so one malicious or buggy node cannot starve others;
- verify exact objects after transfer.

## Difficulty

**High.** The algorithms can be simple, but meaningful conclusions require repeatable real contact measurements because scheduling quality depends on actual contact duration, link behavior, buffer state and transfer overhead.

## Why this is distinct from UC-005

UC-005 asks whether a moving gateway can collect data at all. UC-045 asks:

> **When the collector cannot take everything, what should it take first?**

That makes it a focused queue/scheduling experiment rather than another generic mobile-gateway scenario.

## Research signal

Recent 2026 UAV/data-mule research explicitly studies buffer-aware and signal-aware collection instead of assuming ideal contacts, and Flying DTN research continues to optimize forwarding under intermittent aerial contacts. PollicinoNet should reproduce the underlying scheduling question first with walking/bicycle collectors and its own measured traces.

References:

- https://arxiv.org/abs/2601.06000
- https://doi.org/10.1007/s12083-026-02250-6
