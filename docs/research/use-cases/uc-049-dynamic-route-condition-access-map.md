# UC-049 — Dynamic Route Condition and Access Map

## Idea

Maintain a delay-tolerant map of **what routes are currently reported passable, blocked, degraded or unknown**, using compact signed observations that can move through PollicinoNet even when normal connectivity is fragmented.

The first implementation is a classroom/campus drill with synthetic closures. It must not be presented as an authoritative emergency-routing system.

## Problem solved

A static offline map can tell us where roads, paths or corridors normally exist, but after an incident the important question may be different:

```text
Can I still pass here?
When was that condition observed?
Who/what observed it?
Is there conflicting evidence?
Is the report too old to trust?
```

A central map server is fragile when the network is partitioned. Field observations also arrive late and out of order.

UC-017 already moves map tiles. UC-049 adds **dynamic access state** on top of those maps.

## Actors / nodes

- student field-observer nodes;
- school/lab map node;
- student relay/store-and-forward nodes;
- optional sensor/edge-AI node producing a candidate observation;
- optional teacher/coordinator verifier;
- optional vehicle or walking data mule;
- optional Raiatea/field-report node holding richer evidence.

## Why PollicinoNet fits

Route-condition updates are small, naturally delay-tolerant and useful even when they cannot reach a central server immediately.

- **DISCOVERY:** `route-condition update available for coarse area X`;
- **EXACT:** segment/zone ID, condition code, observation time/checkpoint, expiry, observer key/pseudonym, evidence hash and signature;
- **SEMANTIC:** labels such as `blocked`, `restricted`, `water`, `debris`, `unknown`, always subordinate to the exact observation record.

LoRa can carry compact status deltas and hashes. Photos, video, detailed reports and map tiles move later through BLE/Wi-Fi/Internet or physical carry.

Store-and-forward is valuable because the observer, coordinator and eventual route user do not need to be connected simultaneously.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** segment ID, compact condition code, freshness/expiry, confidence class, evidence hash, conflict notice;
- **BLE:** nearby exchange of several route updates and compact evidence;
- **Wi-Fi/LAN:** map patches, photos, larger incident reports and bulk reconciliation;
- **Internet:** optional synchronization with an authoritative external source when available;
- **physical transport:** a student/device carries observations between disconnected zones.

## What we can test now in software

Start with a synthetic graph representing school corridors or a small fictional road network.

- define immutable `RouteObservation` objects;
- inject closures, reopenings, degraded segments and `unknown` states;
- deliver observations late, duplicated and out of order;
- require expiry/freshness rather than keeping a closure forever;
- retain conflicting observations instead of silently choosing the newest one;
- test one-witness versus multi-witness corroboration through UC-022;
- attach exact photo/report hashes while keeping the bulky evidence elsewhere;
- compute routes that exclude only sufficiently trusted/fresh blocked segments;
- distinguish `no report` from `reported clear`;
- simulate a stale node that missed the reopening update;
- integrate UC-017 for offline base tiles and UC-013 for richer field reports;
- measure update-propagation delay, stale-route decisions, unresolved conflicts, bytes per bearer and evidence-retrieval delay.

A useful invariant is:

> absence of a recent blockage report is not proof that a route is safe or passable.

## What requires real hardware

- 4+ boards split between two or more controlled zones;
- predeclared harmless synthetic closures on a campus/school route;
- one or more moving student relays;
- real LoRa propagation of compact route updates;
- optional BLE/Wi-Fi retrieval of a photo or detailed report;
- measurements of update convergence and stale/conflict exposure.

Any real-road or civil-protection use would require independent procedures, authoritative data sources, legal/safety review and field validation.

## Messina teaching scenario

Create a fictional access graph with coarse nodes named after areas such as `Messina`, `Villafranca`, `Rometta`, `Spadafora` and `Milazzo`, but do **not** publish actual road-safety assertions.

During the exercise, the teacher declares that one synthetic link is blocked and another has reopened. Student boards in different zones learn the updates at different times. Relays carry signed observations until the replicas converge. Students then compare:

- routing with no dynamic updates;
- last-write-wins routing;
- freshness-aware routing;
- multi-witness/conflict-aware routing.

A safer first physical demo can use school corridors, doors or outdoor checkpoints instead of public roads.

## Privacy / security

Route reports can expose observer locations and movements.

- use coarse segment/zone IDs, not continuous GPS tracks;
- use synthetic/pseudonymous observers in teaching tests;
- separate observer identity from the public route status where possible;
- authenticate authoritative corrections/reopenings;
- preserve provenance and conflicts;
- never allow an unauthenticated relay to silently replace the state of a segment;
- rate-limit/spam-protect false reports;
- store exact evidence only where policy allows;
- never claim that the prototype produces safe evacuation routes.

## Difficulty

**Medium–High.** Compact transport is easy; freshness, conflicting evidence, trust and safe route interpretation are the challenging parts.

## Research signal

Humanitarian mapping activations in 2026 continue to emphasize that up-to-date road and infrastructure information is operationally important after floods and landslides. HOT/OpenStreetMap activations for Kenya, Ethiopia, DRC and Mozambique explicitly map damaged infrastructure and access-relevant data for relief planning. Recent LoRa work also continues to study remote landslide/rockfall monitoring. PollicinoNet can reproduce only the delay-tolerant information-flow problem at teaching scale; none of those external results establish PollicinoNet field reliability.

References:

- https://wiki.openstreetmap.org/wiki/Humanitarian_OSM_Team/Open_Mapping_Hub_Eastern_and_Southern_Africa/Kenya_Floods_2026_HOT_Activation
- https://www.hotosm.org/en/projects/mozambique-floods-response/
- https://www.mdpi.com/2079-9268/16/1/7
