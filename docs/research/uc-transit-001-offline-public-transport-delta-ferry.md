# UC-TRANSIT-001 — Offline public-transport timetable and service-delta ferry

Status: PROTOTYPE / TERRITORIAL RESEARCH

## Problem

Public-transport information is often compact but time-sensitive: timetable generation, changed stop, delayed/cancelled service, replacement route or ferry/train/bus service notice. A user in a weak-connectivity area may not need a full app refresh; they may only need the latest authoritative delta for the routes they care about.

PollicinoNet can carry signed public schedule/service metadata between school, student/commuter nodes and territorial clusters, while full GTFS/NeTEx/SIRI data or maps remain on Wi-Fi/Internet.

This is not a navigation or safety system and must not manufacture live transport data. The prototype uses synthetic fixtures or authoritative public data only.

## Actors / nodes

- authoritative public-data ingest gateway;
- school gateway/cache;
- student/commuter Pollicino nodes;
- optional bus/train/ferry/vehicle relay if separately authorized;
- offline local display/client;
- optional home Internet/Wi-Fi resolver.

## Messina educational scenario

Model public route-interest cohorts such as `west-coast`, `hill-link`, `messina-hub`, `ferry-link` without associating them with named students. At school, nodes receive only changed service descriptors for subscribed route IDs. During the afternoon, those deltas propagate through store-carry-forward contacts.

```text
authoritative feed -> school cache
                         |
               route/status deltas
                         |
        +----------------+----------------+
        v                v                v
   student A         student B        commuter relay
        |                |                |
        +------ physical carry / DTN -----+
                         |
                         v
                offline territorial client
```

No synthetic result implies actual radio coverage of any route in Messina province.

## Why PollicinoNet fits

Transport status has useful properties for a DTN experiment:

- compact identifiers and versioned deltas;
- strong freshness/usefulness deadlines;
- public authoritative provenance;
- subscriptions by route/area rather than broadcast to everyone;
- stale state is harmful even when technically deliverable;
- predictable commuter/vehicle mobility can create relay opportunities;
- rich maps/full feeds can be retrieved later over Wi-Fi/Internet.

It is therefore distinct from generic content distribution and from emergency bulletins, while reusing the same transport primitives.

## Possible bearers

- LoRa for compact route/status deltas;
- BLE for local stop/station exchange experiments;
- Wi-Fi/LAN for full feed/cache refresh;
- Internet for authoritative source ingestion;
- physical movement by students/commuters/vehicles as the carry mechanism.

## What can be tested now in software

Without boards we can model:

1. GTFS/NeTEx-like synthetic route IDs and timetable generations;
2. compact `route -> changed generation/status` deltas;
3. route-interest subscriptions;
4. timetable update versus cancellation alert with different deadlines;
5. stale-state suppression;
6. morning school cache fill followed by afternoon disconnected propagation;
7. scheduled vehicle relay versus purely opportunistic student relay;
8. gateway outage and later authoritative refresh;
9. full snapshot versus delta/reconciliation byte cost.

A useful application metric is **useful-before-departure delivery**, not merely eventual delivery.

## What requires real hardware

Real boards are required before claiming:

- useful transport deltas per contact;
- real student/commuter route connectivity;
- station/vehicle contact opportunity;
- real end-to-end timeliness in Messina province;
- battery/energy cost;
- any operational benefit to passengers.

HW-006 remains the first RF evidence gate. Any experiment involving transport operators or vehicles requires separate permission and safety review.

## Privacy / security

Requirements:

- public route subscription should not expose named student travel patterns;
- use coarse route-interest groups and rotating pseudonyms where possible;
- only signed/verified authoritative data may be labeled operational/public-service information;
- preserve source timestamp/generation and freshness deadline;
- reject stale or superseded service state;
- never use experimental crowd reports as authoritative cancellation/safety notices without a separate trust model.

## Implementation difficulty

**Medium.** Feed parsing is straightforward; the interesting work is delta selection, deadline semantics, subscription privacy and provenance.

## Minimal measurable hypotheses

- H1: route-interest filtering and deltas reduce scarce-link bytes materially relative to full feed snapshots.
- H2: predictable student/commuter mobility can deliver useful public-service updates before their application deadline in some disconnected scenarios.
- H3: freshness-aware suppression prevents stale service state from consuming relay capacity.

## Metrics

- updates delivered before usefulness deadline;
- stale updates suppressed;
- bytes per useful route update;
- route-interest precision/recall;
- hops and relay count;
- authoritative-generation convergence time;
- full-snapshot versus delta wire cost;
- per-bearer TRC.

## Gate decision

**PROTOTYPE / TERRITORIAL RESEARCH.** Strong local relevance, but field use must remain informational and experimental until real sources, permissions and measured contact evidence exist.

## Related research / standards context

A study in Milan evaluated Wi-Fi-enabled public-transport buses as a backbone for delay-tolerant, opportunistic service access: https://doi.org/10.3233/AIS-170443 .

For authoritative Italian multimodal data, the National Access Point describes NeTEx-based static mobility information and national/regional access mechanisms: https://www.cciss.it/nap/mmtis/public/en/static/multimodal .
