# UC-055 — Opportunistic Transit Disruption and Arrival Relay

## Idea

Use PollicinoNet to carry **small, time-bounded public-transport status observations** between disconnected stations, stops or student groups.

The goal is not to build an unofficial authoritative timetable. The experiment is to see whether delay-tolerant relays can propagate useful status such as:

```text
trip 22303
stop = Rometta Messinese
observed_departure = checkpoint T
status = delayed / canceled / unknown
uncertainty = explicit
expires = soon
```

Students themselves can act as store-and-forward relays while moving along ordinary routes.

## Problem solved

A static timetable is still useful when the Internet disappears, but the information passengers most need is often what changed: delay, cancellation, platform/stop issue or a revised expected arrival.

In a sparse network there may be no continuous path from an authoritative feed or one observed station to every other stop. Small updates can nevertheless move opportunistically with people and devices.

This is different from UC-025, which uses scheduled mobility as a **routing opportunity**, and UC-049, which describes **route/passability conditions**. UC-055 treats the public-transport service itself as the changing object being observed.

## Actors / nodes

- student commuter/relay nodes;
- school or station-adjacent cache nodes;
- public timetable cache;
- optional authorized/official GTFS-Realtime or operator feed gateway;
- optional manually generated teaching observations;
- passengers/users consuming a local offline status view.

## Why PollicinoNet fits

Transit updates are small, expire quickly and remain useful even when delivery is delayed by several minutes.

- **DISCOVERY:** `trip/status update available`, `stop X wants fresher status`;
- **EXACT:** public trip/route/stop ID, observation epoch, signed/source-tagged state, uncertainty and expiry;
- **SEMANTIC:** human labels such as `significant delay`, `service modified`, only when tied to an exact source/observation.

LoRa can carry compact status/control messages. Wi-Fi/Internet can refresh the underlying timetable or obtain official feeds when available. Physical mobility naturally transports status along the same corridors where the information is useful.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** trip/stop ID, compact delay/status bucket, observation epoch, uncertainty, expiry and source class;
- **BLE:** nearby stop/station cache synchronization;
- **Wi-Fi/LAN:** complete GTFS/static schedules, richer alert text and batch synchronization;
- **Internet:** optional official GTFS-Realtime/operator feed ingestion;
- **physical transport:** students/commuters carry cached updates between otherwise disconnected zones.

## What we can test now in software

Build a small synthetic timetable graph with public trip IDs and stops.

Test:

- baseline static timetable plus delayed observations;
- `on_time`, `delayed`, `canceled`, `unknown`, `no_fresh_data` states;
- strict TTL so old delay reports do not circulate indefinitely;
- several observations of the same trip arriving out of order;
- official-source updates versus student observations with different trust classes;
- conflicting observations that remain explicit rather than silently overwriting one another;
- demand-driven status requests using UC-024;
- relay routing over UC-008/UC-025 contact traces;
- comparison of schedule-only versus schedule-plus-opportunistic-status views;
- metrics: age of status at delivery, stale-update rejection, coverage by stop, conflicting-state count and bytes per bearer.

A key invariant is:

> absence of fresh status must remain `unknown`; the system must never infer that a train/bus is on time merely because no update arrived.

## What requires real hardware

Start with a controlled teaching route before any real-service claim:

- 4–6 LoRa nodes;
- 2–4 fixed public/school checkpoints representing stops;
- student relays moving between them;
- scripted synthetic delays/cancellations;
- measured propagation delay and update age.

A later opt-in experiment may observe public station departure/arrival events, but must not interfere with transport operations or claim official status. Any vehicle deployment requires permission where appropriate.

## Messina teaching scenario

The Tirrenica corridor is unusually convenient for this experiment because the same regional rail sequence connects **Messina Centrale, Villafranca Tirrena, Rometta Messinese, Spadafora and Milazzo**.

A synthetic exercise can give each station/cache one piece of fresher trip state and let student nodes relay it west/east. The class measures whether downstream caches receive the update before it expires.

The scenario is also realistic: on **13 September 2026**, RFI published maintenance-related timetable changes affecting regional services on the Messina–Palermo line, including a regional service with stops at Villafranca Tirrena, Rometta Messinese, Spadafora and Milazzo. That is a useful dated example of the type of changing information the experiment models; it is not evidence that PollicinoNet can distribute it reliably.

## Privacy / security

Transport status is public-domain-like information, but the relay network can still expose people's movements.

- bind observations to public trip/stop IDs, not passenger identities;
- do not publish which student rode which service;
- avoid continuous GPS traces;
- use coarse checkpoint encounters and rotating relay identifiers;
- distinguish official, teacher-scripted and crowd-observed sources;
- authenticate authoritative updates;
- include expiry and observation uncertainty;
- never present crowd observations as official operator information.

## Difficulty

**Medium–High.** Payloads are tiny and very testable; the harder parts are freshness, conflicting observations, trust classes and privacy-safe mobility.

## Research / standards signal

GTFS-Realtime already models `TripUpdate`, predicted arrivals/departures, cancellations and service alerts, and explicitly treats missing realtime data as **no realtime information**, not proof that service is on time. That is a good semantic model for PollicinoNet's stale/unknown handling.

References:

- https://gtfs.org/documentation/realtime/feed-entities/trip-updates/
- https://gtfs.org/documentation/realtime/feed-entities/service-alerts/
- https://www.rfi.it/it/news-e-media/infomobilita/avvisi/2026/9/13/linee-siracusa---messina-c-le--messina-c-le---palermo-c-le-.html
