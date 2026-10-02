# UC-150 — Distributed Visual Survey Mosaic Courier

## Problem solved

Large survey image sets can be split across disconnected phones, cameras or moving collection nodes. A processing worker may discover later that a zone lacks overlap or that one batch is low quality.

UC-150 separates small coverage/quality metadata from the large imagery, so the network can request only the missing image batches needed to complete a survey product.

## Actors / nodes

Camera/phone node, optional vehicle-mounted camera, student relay, checkpoint cache, photogrammetry worker, map/Raiatea node and reviewer.

## Why PollicinoNet fits

LoRa can carry campaign ID, coarse survey-cell ID, image-batch hash, image count, quality class, missing-overlap flag and processing status. Full images wait for richer bearers.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- **LoRa:** survey manifest, coarse coverage, quality flag and follow-up request.
- **BLE:** thumbnails or small previews.
- **Wi-Fi/LAN:** full-resolution images and generated map products.
- **Internet:** optional map data or remote compute.
- **Physical transport:** SD card/SSD for large image batches.

## What we can test now in software

Use a public photogrammetry sample dataset and divide the images across 3–5 virtual nodes. Test a missing strip, insufficient overlap, duplicate images, one low-quality batch and late arrival after an initial mosaic.

Measure control bytes, image bytes eventually requested, repair rounds and provenance from source-image hashes to final map tiles.

## What requires real hardware

Start with phones and 4–6 LoRa boards inside an approved school/public test area. Split capture batches across groups and keep full images off LoRa.

Any later use of specialised capture vehicles or aircraft should be treated as a separate authorised activity; the networking workflow does not depend on them.

## Messina teaching scenario

Three groups collect overlapping image strips in different parts of an approved campus/public test area in the province of Messina. Their nodes advertise only coarse survey-cell coverage and quality status.

A school laptop discovers a gap. The follow-up request moves through store-and-forward; another group later captures the missing strip and full images reach the processing worker by Wi-Fi or removable media.

## Privacy / security

Avoid faces, licence plates, private homes and unnecessary precise trajectories. Coarsen location metadata when exact coordinates are not needed. Preserve source-image hashes and treat generated maps as potentially sensitive location data.

## Difficulty

**High.**

## Why this is distinct

UC-005 covers moving gateways, UC-060 visual evidence, UC-084 robot map fragments and UC-122 vector-map editing. UC-150 focuses on **distributed image-set assembly and late repair of survey coverage gaps**.

## Tooling signal

OpenDroneMap provides an open photogrammetry workflow for orthophotos and related products, making a software-only phase practical before any field capture.
