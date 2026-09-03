# UC-005 — Mobile Gateway: Person, Bicycle, Vehicle or UAV

## Idea

Treat a moving node as a scheduled or opportunistic collector for fixed PollicinoNet nodes that may otherwise remain disconnected. Start safely with a person or bicycle carrying the gateway; a vehicle or UAV is a later research variant.

## Problem solved

Some rural/isolated nodes may never have an end-to-end route to the school or Internet. A mobile gateway can create short contact windows, collect queued data and deliver it later.

## Actors / nodes

- fixed field/sensor nodes;
- moving collector carried by a student/teacher in controlled tests;
- optional bicycle/vehicle gateway;
- future UAV-mounted gateway;
- school server/cache.

## Why PollicinoNet fits

This is a direct delay-tolerant/store-carry-forward problem. PollicinoNet can prioritize a backlog during a short encounter, advertise compact inventories and resume exact transfers across later contacts without changing the LoRa PHY.

## Possible bearers

- **LoRa:** discovery, contact-window signaling, backlog summaries, small priority objects;
- **BLE/Wi-Fi:** faster transfer when the moving collector comes close enough;
- **Internet:** later backhaul from the collector;
- **physical transport:** the moving collector is itself the bearer between disconnected areas.

No PHY change is required or proposed.

## What we can test now in software

- synthetic routes and contact windows;
- queue scheduling by priority, expiry, size and fairness;
- partial/resumable transfers across multiple passes;
- compare opportunistic vs scheduled collection;
- multi-node contention and starvation tests;
- metrics: collected fraction, age of information, TRC, completion delay, fairness and queue growth.

## What requires real hardware

First stage:
- fixed board + walking/bicycle collector;
- repeated controlled passes at measured distances/speeds;
- packet loss, RSSI/SNR, airtime and completed-object measurements.

Later stage:
- vehicle or UAV gateway only with appropriate legal/safety procedures;
- antenna orientation/directivity and ground-to-air behavior must be measured, not assumed.

Recent 2025 UAV-assisted LoRa work reports that ground-to-air antenna directivity and scheduling materially affect throughput, which is a useful warning against treating an aerial relay as simply a higher ground node.

## Privacy / security

Do not use real student travel histories as routing telemetry. Use synthetic or coarse routes and rotating node identities. A mobile collector must not become an unrestricted reader of carried content; end-to-end authorization/encryption remains above the bearer.

## Difficulty

**High.** The software simulator is tractable, but meaningful physical evaluation needs controlled mobility experiments and careful separation of protocol behavior from radio/antenna effects.
