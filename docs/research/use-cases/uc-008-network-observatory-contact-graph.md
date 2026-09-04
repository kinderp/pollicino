# UC-008 — Privacy-Preserving Network Observatory

## Idea

Use the real student network itself as a measurement instrument. Participating nodes record **encounters, relay opportunities and coarse link observations** so that PollicinoNet can learn where store-and-forward actually works, which routes are useful, and where fixed relays would help.

A Messina-area experiment can start with controlled routes among school, Rometta, Venetico, Spadafora and nearby towns. The important object is a **contact graph**, not a continuous GPS track: *node A encountered node B during a time window, with these measured radio/link properties*.

## Problem solved

Before designing routing or placing relays, we need evidence about real contact opportunities. Static coverage maps do not tell us how often student-carried nodes meet, how long contacts last, or whether a message can move across several daily encounters.

## Actors / nodes

- student-carried PollicinoNet nodes;
- optional fixed school/home relay nodes;
- a school-side analysis service;
- synthetic nodes for software-only experiments.

## Why PollicinoNet fits

PollicinoNet already treats intermittent connectivity, store-and-forward, TTL and richer-link handover as first-class concepts. The observatory turns those concepts into measurable traces that can later drive relay placement, queue policy and realistic simulators without changing the frozen LoRa PHY.

## Possible bearers

- **LoRa:** peer discovery and measured scarce-link encounters;
- **BLE:** nearby encounter confirmation or faster metadata exchange;
- **Wi-Fi/Internet:** upload of accumulated measurement bundles;
- **physical transport:** a node can carry its logs until it reaches an authorized collector.

## What we can test now in software

- generate synthetic student mobility/contact traces;
- build time-varying contact graphs;
- replay UC-001/UC-003 traffic over those traces;
- compare relay-placement and forwarding strategies;
- measure delivery probability, delay, queue age, relay centrality and contact-window utilization;
- test privacy-preserving aggregation with rotating node IDs and coarse zones.

## What requires real hardware

- controlled walks/commutes with 3+ boards;
- measured encounter timestamps, packet success, RSSI/SNR and contact duration;
- repeat the same route at different times/days before drawing conclusions;
- compare fixed relay positions only after real traces exist.

No range or reliability claim is valid until these field measurements are collected.

## Privacy / security

This use case is privacy-sensitive. Do **not** collect student names, home addresses or continuous precise trajectories. Prefer rotating/scoped identifiers, coarse location zones, short retention, explicit opt-in and aggregated publication. Raw encounter traces should be access-controlled because repeated contact timing can re-identify routines even without names.

## Difficulty

**Medium.** The software is straightforward graph/event processing; the main challenge is collecting useful real traces without turning the experiment into student tracking.
