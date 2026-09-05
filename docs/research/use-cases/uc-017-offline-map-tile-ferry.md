# UC-017 — Offline Map and Route Tile Ferry

## Idea

Distribute **offline map areas, route packs and field overlays** across an intermittent network without sending an entire regional map every time. A LoRa node advertises a compact area/version coordinate; peers that later meet over Wi-Fi, LAN, Internet or physical transport exchange only the missing content-addressed vector/raster tiles, route graphs or small overlay objects.

For a Messina teaching scenario, different student nodes can cache prepared map packs for separate towns or corridors. A field group requests a synthetic area of interest, another node carries the missing tiles, and the receiver reconstructs the exact signed map pack when a richer bearer becomes available.

## Problem solved

Maps are valuable exactly when connectivity is weak, but regional map datasets can be large and updates are often localized. Re-downloading a whole pack wastes bandwidth and may leave field devices with stale information. The system needs compact discovery of **which area/version is needed** and exact, resumable retrieval of only the changed pieces.

## Actors / nodes

- school map/package server;
- student relay/store-and-forward nodes;
- phone, tablet or laptop displaying the offline map;
- optional field team, vehicle or drone gateway;
- `PollicinoStore` caches containing signed manifests and exact tiles/overlays.

## Why PollicinoNet fits

`DISCOVERY` can carry a short coordinate describing map family, coarse area of interest, version and expiry. `EXACT` can identify the resolved map manifest and every tile or overlay by full cryptographic identity. Content-addressed storage naturally deduplicates unchanged tiles across versions, while store-and-forward lets a student or vehicle physically carry the missing region between disconnected areas.

This does not change the frozen LoRa PHY. LoRa is primarily the scarce control/discovery bearer; bulk map bytes should move on richer links whenever possible.

## Possible bearers

- **LoRa:** area/version request, tile-set coordinate, priority, expiry, provider hint and compact authenticator;
- **BLE/Wi-Fi/LAN:** actual vector/raster tiles, route graph segments and overlays;
- **Internet:** fetch from an upstream open-data mirror when available;
- **physical transport:** a student node, USB/NVMe device or vehicle carries complete regional packs between network islands.

## What we can test now in software

- generate or import a small open map pack split into deterministic content-addressed tiles;
- create two versions with only a small subset of tiles changed;
- simulate nodes caching different towns/areas and request a rectangular or corridor-shaped area of interest;
- prove that only missing/changed tiles are transferred;
- interrupt and resume a multi-tile transfer;
- test signed manifest expiry and rollback to an older map version;
- simulate a field overlay such as a synthetic closed-road marker without using real emergency data;
- measure scarce-link metadata bytes, rich-link bytes, cache hit ratio, time-to-usable-area and exact reconstruction success.

A useful correctness test is that the final local pack must match the expected manifest and hashes exactly even if tiles arrive from several peers in different orders.

## What requires real hardware

- at least three nodes with different cached map subsets;
- real LoRa discovery of an area/version need;
- a measured LoRa-to-Wi-Fi/BLE handover for missing tile retrieval;
- one walking or vehicle data-mule pass carrying a map subset;
- measured packet delivery for the LoRa control path and actual transfer time on the richer bearer.

Do not infer usable geographic range or emergency availability from software simulation.

## Privacy / security

Prefer open map data and synthetic overlays. Requests should use coarse areas when exact user location is unnecessary. Do not broadcast a student's live position or home address. Operational overlays may reveal sensitive infrastructure, so manifests need provenance, authorization, signature/expiry and clear distinction between official data and classroom annotations.

## Difficulty

**Medium.** The content-addressed and store-and-forward parts fit PollicinoNet directly, and the result is visually easy for students to understand. The main work is packaging/versioning map data and designing privacy-safe area requests.

## Research signal

Offline/self-hosted map systems remain relevant for field and disaster deployments because map, routing and search services cannot assume Internet access. PollicinoNet adds an experimental question on top: how little scarce-link metadata is needed to discover and eventually reconstruct the exact useful map subset from distributed caches?
