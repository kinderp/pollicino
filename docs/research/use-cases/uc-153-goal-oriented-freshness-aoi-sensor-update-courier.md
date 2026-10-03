# UC-153 — Goal-Oriented Freshness / AoI-Aware Sensor Update Courier

## Problem solved

A sensor network with intermittent contacts can waste scarce contact time by forwarding every queued sample in FIFO order even when many samples are already superseded.

UC-153 asks a more useful question: **which update most improves the receiver's current knowledge or task quality?**

Examples include temperature, humidity, water level, air quality, machine state, or a compact feature used by an edge model. The receiver tracks how old its latest accepted state is and the sender/relay can prioritize the update that reduces useful staleness most.

This is not simply "newest packet wins": some streams may be safety-relevant, some may change slowly, and some applications may need a short history window rather than one point.

## Actors / nodes

- fixed or mobile sensor nodes;
- student relay/store-and-forward nodes;
- collector or school gateway;
- optional edge-inference consumer;
- optional UC-123 clock-quality source;
- optional UC-045 mobile harvester.

## Why PollicinoNet fits

Store-and-forward creates exactly the condition where freshness matters: by the time a queue reaches the destination, some samples may no longer be worth sending.

Compact control metadata can include:

- stream ID;
- sample/sequence ID;
- source timestamp or logical epoch;
- freshness class;
- replacement/supersession relation;
- compact task-utility class;
- receiver's last-known accepted sample;
- explicit `TIME_UNCERTAIN` when clock quality is insufficient.

LoRa can carry these hints and small urgent updates. Richer bearers can carry longer history blocks.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** stream ID, sequence/epoch, freshness/utility hints, latest-state summary and small updates.
- **BLE:** short history windows and local reconciliation.
- **Wi-Fi/LAN:** bulk time-series repair or high-rate windows.
- **Internet:** optional normal backhaul when available.
- **Physical transport:** SD/laptop/data mule carrying historical blocks.

## What we can test now in software

Create several synthetic sensor streams with known dynamics and intermittent contact traces.

Compare policies such as:

1. FIFO;
2. newest-first;
3. oldest-destination-state first;
4. deadline/priority aware;
5. Age-of-Information aware;
6. goal-oriented utility where freshness matters differently for different streams.

Inject:

- long partitions;
- bursty updates;
- a slowly changing stream and a rapidly changing stream;
- clock uncertainty;
- duplicate/superseded samples;
- one stream used by a simple remote inference task;
- contact windows too short to move all queued data.

Measure destination AoI/freshness, task error on the synthetic inference, bytes sent, completed updates, stale bytes avoided and fairness between streams.

These are software metrics only; they are not physical LoRa performance claims.

## What requires real hardware

Use 4–6 LoRa boards and 3–5 harmless sensors or simulated analog inputs. Keep the destination unreachable for controlled periods, then allow short contacts.

Compare at least FIFO against one freshness-aware policy on the same scripted experiment.

Measure actual delivery, contact duration, bytes, latency, RSSI/SNR if already exposed by the frozen stack, and energy only with real instrumentation.

## Messina teaching scenario

Place environmental nodes representing coarse public/school zones in Messina, Villafranca and Rometta/Venetico-Spadafora. Student-carried relays encounter them at different times.

The experiment asks whether a gateway that has not heard from one zone for hours should receive that zone's newest compact state before a large backlog from a recently refreshed zone.

No home address or continuous student route needs to be recorded.

## Privacy / security

Freshness metadata can reveal when a site was active. Use coarse stream identifiers and avoid linking them to a student's identity or home.

Authenticate priority/utility classes so a sender cannot mark every packet as urgent. Treat timestamps as uncertain unless UC-123 or another trusted timing method justifies stronger claims.

Do not discard history required for audit merely because a newer state exists; supersession is application-specific.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-045 chooses what a mobile harvester downloads during one scarce contact. UC-107 handles validity/freshness of cached content. UC-123 handles clock uncertainty.

UC-153 focuses on **receiver-side information freshness across sensor streams and whether an old queued update still has task value at all**.

## Research signal

Age of Information and goal-oriented status updating remain active research topics in 2026, including remote-inference settings with two-way delay and intermittent store-and-forward constraints.

References:

- C. Arı et al., “Goal-Oriented Status Updating for Real-time Remote Inference over Networks with Two-Way Delay,” IEEE Transactions on Networking, 2026, DOI: 10.1109/TON.2026.3670099.
- C. Arı et al., “Optimizing Peak Age under Intermittent Satellite Connectivity and Store-and-Forward,” Asilomar 2026 (forthcoming).
