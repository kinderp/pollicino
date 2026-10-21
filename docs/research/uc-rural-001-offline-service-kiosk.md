# UC-RURAL-001 — Offline community knowledge/service kiosk with asynchronous sync

Status: TERRITORIAL USE CASE / PROTOTYPE

## Problem

A small community location may have a local device with useful digital resources even when Internet access is intermittent or intentionally absent. The device can serve cached public information locally and exchange updates asynchronously whenever a mobile relay or temporary gateway appears.

Examples:

- public-domain/offline knowledge pages;
- local community notices;
- public forms and instructions;
- school learning material authorized for redistribution;
- local service schedules;
- sensor summaries;
- wanted lists for documents/data not currently cached.

The goal is **asynchronous local service**, not pretending to provide normal real-time Internet.

## Actors / nodes

- fixed community/school/rural kiosk node;
- student/teacher/vehicle data mule;
- school or town Internet gateway;
- local users via Wi-Fi/BLE/LAN;
- optional Raiatea/document cache.

## Messina-oriented scenario

Model a set of logical territorial clusters representing coastal and hill communities in the province. A kiosk has a local Wi-Fi interface for users, while Pollicino/LoRa handles compact sync state with passing relays. A student or supervised vehicle later reaches the school hub and exchanges updates through Wi-Fi/Internet.

```text
local users -- Wi-Fi --> offline kiosk
                         |
                         | compact LoRa sync/reference
                         v
                     mobile mule
                         |
                    physical carry
                         |
                         v
                   school gateway
                         |
                       Internet
```

This architecture does not imply measured LoRa coverage between villages.

## Why PollicinoNet fits

The system naturally separates scarce and rich work:

- locally cached content remains usable with no WAN;
- LoRa can carry availability, wanted state, checksums, notices and compact deltas;
- physical mobility bridges long disconnected intervals;
- Wi-Fi at either end carries bulk content;
- reconciliation avoids repeatedly transporting unchanged material.

This is close in spirit to historical asynchronous rural systems such as DakNet, but PollicinoNet adds content-addressed exactness, multiple bearers, reconciliation and explicit cost accounting.

## Possible bearers

- LoRa for compact sync/discovery;
- BLE for maintenance/provisioning;
- local Wi-Fi/LAN for user access and bulk local content;
- Internet at hub/gateway;
- physical student/vehicle movement between clusters.

## What can be tested now in software

- two or more kiosks with partial overlapping caches;
- periodic mobile relay visits;
- wanted-list and availability reconciliation;
- mutable public bulletin versus immutable content objects;
- reference-only retrieval versus carrying small missing chunks;
- one-day/one-week gateway outages;
- priority between urgent notices and bulk knowledge updates;
- storage quota and cache eviction.

A useful baseline is a kiosk that only synchronizes when Internet returns directly. Pollicino helps only if the mobile path adds useful timeliness/availability for acceptable cost.

## What requires real hardware

- real kiosk-to-mule contact capacity;
- range and obstruction behavior;
- power requirements for unattended nodes;
- Wi-Fi local-service performance;
- environmental enclosure/installation;
- actual route/contact timing;
- any claim of usefulness for a specific town or rural zone.

## Privacy / security

Public caches are simpler than personal services, so the first pilot should remain public/non-sensitive.

If later used for personal forms/messages:

- end-to-end encryption and authentication are required;
- kiosk operators/relays must not automatically gain plaintext access;
- precise user identities/location histories should not be propagated;
- public bulletin provenance must be explicit;
- content licensing/redistribution rights must be respected.

## Implementation difficulty

**Medium** for a public-content pilot; **high** for private e-government/personal-service workflows.

## Minimal measurable hypotheses

- H1: mobile asynchronous sync reduces staleness of local cached resources compared with waiting for direct kiosk Internet restoration.
- H2: wanted-list/reconciliation substantially reduces mule traffic when caches overlap.
- H3: separating LoRa metadata from Wi-Fi bulk transfer allows useful local content service without forcing bulk data onto the scarce bearer.

## Metrics

- cache freshness;
- requested-resource satisfaction ratio;
- time until requested resource arrives;
- metadata versus payload bytes by bearer;
- cache hit ratio;
- duplicate bytes avoided;
- mobile relay visits required;
- storage occupancy/evictions;
- provenance/authorization failures.

## Gate decision

**PROTOTYPE.** This is a concrete territorial composition of existing primitives. It should initially reuse generic content/wanted/reconciliation contracts rather than invent a kiosk-specific protocol.

## Related precedent

DakNet demonstrated the basic architectural idea of asynchronous digital connectivity by combining short wireless contacts with physical transportation to remote locations: https://www.media.mit.edu/publications/daknet-rethinking-connectivity-in-developing-nations/ .