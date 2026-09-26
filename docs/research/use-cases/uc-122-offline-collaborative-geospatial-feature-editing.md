# UC-122 — Offline Collaborative Geospatial Feature Editing and Conflict Merge

## Idea

Allow disconnected teams to add and edit vector-map features — points, lines and polygons — and later reconcile those edits through PollicinoNet while preserving geometry validity, provenance and unresolved conflicts. The frozen LoRa PHY is unchanged.

## Problem solved

Static map tiles are useful offline, but many field scenarios need edits rather than downloads: mark a fictional blocked road, move a checkpoint, add an environmental observation area, correct a path segment or annotate a school exercise zone.

Two disconnected teams may edit the same feature differently. A naive latest-timestamp-wins rule is unreliable when clocks differ and can also create invalid geometry.

## Actors / nodes

- field mapping clients;
- relay/store-and-forward nodes;
- local map replicas;
- optional authoritative map/reviewer node;
- evidence holder for photos or survey notes.

## Why PollicinoNet fits

Vector edit metadata can be much smaller than complete map layers.

- **DISCOVERY:** layer/tile ID, feature IDs changed, revision/conflict summary.
- **EXACT:** feature ID, geometry operation, parent revision, actor/role, exact layer/schema version and evidence hash.
- **SEMANTIC:** labels such as "road blocked" or "survey boundary", which remain distinct from exact geometry/state.

LoRa can carry feature-change digests and reconciliation requests. BLE/Wi-Fi carries GeoJSON/vector deltas, map tiles and imagery.

## Possible bearers

- **LoRa:** changed-feature inventory, revision summary, conflict flag, small status delta;
- **BLE:** small GeoJSON/feature patch;
- **Wi-Fi/LAN:** vector layer, map tiles, photos and larger evidence;
- **Internet:** optional basemap/source refresh;
- **physical transport:** complete offline map pack.

## What we can test now in software

Create a synthetic map layer and generate concurrent edits: two teams move the same point, one edits while another deletes, both reshape the same polygon, independent edits to different features, a geometry that becomes invalid, a stale layer/schema version and a late old edit.

Test operation logs, branch/merge, CRDT-style approaches or explicit manual conflict queues. Metrics include convergence, invalid-geometry rate, unresolved conflicts, bytes transferred and full-layer retransfers avoided.

## What requires real hardware

Use 4–6 boards and several phones/laptops with an offline map client. Run a controlled school or public-area exercise with entirely synthetic hazards/checkpoints. Let groups edit while disconnected, then reconcile through student relays.

Any statement about geographic LoRa coverage must come from separate physical measurements, not the map exercise.

## Messina teaching scenario

Prepare a fictional exercise layer covering coarse public/school locations in Messina, Villafranca, Rometta/Venetico and Spadafora. Different groups add temporary checkpoints or synthetic access restrictions. Students moving between areas act as relays; the final map should show which edits converged automatically and which require review.

This can later integrate UC-049 route-condition state and UC-060 visual evidence without making either one authoritative by itself.

## Privacy / security

- avoid student homes and precise personal trajectories;
- use coarse/public coordinates for teaching;
- authenticate authoritative layer updates;
- keep provisional observations visibly provisional;
- do not auto-resolve safety-relevant geometry conflicts;
- strip unnecessary image metadata;
- retain exact revision provenance for every accepted edit.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-017 distributes map tiles; UC-049 propagates route-condition state; UC-060 ferries visual survey evidence. UC-122 adds **concurrent offline editing and reconciliation of vector geospatial features**.

## Research / implementation signal

Geometry-aware CRDT work shows that collaborative spatial editing has conflict and topology problems beyond ordinary text synchronization.

References:

- https://doi.org/10.3390/ijgi15070302
- https://doi.org/10.5194/isprs-archives-XLVIII-4-W13-2025-171-2025
