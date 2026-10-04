# UC-162 — Selective Restore Dependency-Closure and Recovery-Plan Courier

## Problem solved
After a device failure, a full backup restore may be unnecessary or too large for intermittent contacts. A user may need only one project, one model environment, one course folder or one Raiatea corpus while the required pieces are spread across several caches.

UC-162 computes the minimal exact restore closure, discovers candidate holders and moves only the required content until the selected target is verified.

## Actors / nodes
Replacement device, snapshot/manifest catalog, distributed cache nodes, student relays, optional physical-storage bearer and verifier.

## Why PollicinoNet fits
The restore plan is compact metadata: snapshot ID, selected root, manifest/tree hash, missing-object digest, holder summaries and progress. LoRa can carry that state while selected chunks move through BLE/Wi-Fi/LAN or physical transport. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: restore request, snapshot/tree ID, missing-set summary and progress.
- BLE: small manifests.
- Wi-Fi/LAN: required chunks/files.
- Internet: optional remote store.
- Physical transport: large selected restore closure.

## Software test now
Create a synthetic directory tree and split deduplicated chunks across 3–5 caches. Compare full restore, file-level restore, dependency-closure restore, UC-152 set reconciliation, UC-130 chunk reuse and UC-112 resume. Inject missing or corrupt chunks and disappearing caches. Measure bytes planned/transferred and verified completeness.

## Real hardware
Use 4–6 LoRa boards and three storage hosts with public or synthetic backup fragments. Simulate one replacement device and restore only one public project through interrupted rich-bearer contacts. Completion requires final manifest/hash verification.

## Messina scenario
Backup fragments for a public programming project are held at school/lab caches in Messina, Villafranca and Rometta/Venetico-Spadafora. A replacement machine asks for only that project and its exact environment.

## Privacy / security
Backup metadata can reveal filenames, directory structure and content possession. Start with public/synthetic data, use opaque IDs, minimize LoRa metadata and authenticate restore requests.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-012 covers backup/restore, UC-091 retrievability audit, UC-130 chunk deduplication and UC-152 set reconciliation. UC-162 focuses on the minimal dependency closure for one selective restore across intermittent distributed caches.

## Design signal
Content-addressed backup systems such as restic and Borg model snapshots through manifests/trees and deduplicated chunks; UC-162 applies that structure to a multi-holder DTN restore planner.
