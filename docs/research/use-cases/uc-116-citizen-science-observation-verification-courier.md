# UC-116 — Citizen-Science Observation Verification Courier

## Idea
Let field nodes record compact observations, optionally run a local classifier, and ferry only a small claim first. Rich evidence such as a photo or audio clip moves later when a reviewer or nearby edge node requests it.

## Problem solved
Environmental observations are often collected where backhaul is weak, while raw media is much larger than the initial claim. A useful workflow needs to preserve uncertainty and provenance rather than treating every local AI label as truth.

## Actors / nodes
Field observer or sensor, relay/store-and-forward nodes, optional edge-AI worker, reviewer/expert, school/lab collector.

## Why PollicinoNet fits
- **DISCOVERY:** observation class, confidence bucket, coarse area, evidence availability.
- **EXACT:** observation ID, model/version if used, timestamp evidence, sensor/camera profile, evidence hash and review status.
- **SEMANTIC:** species/event/category labels for humans.

LoRa carries compact claims and review requests; BLE/Wi-Fi carries media; physical transport can carry full evidence collections.

## What we can test now in software
Use public biodiversity or environmental datasets. Test correct/incorrect model labels, duplicate observations, uncertain classifications, delayed expert review, conflicting reviewers and model-version changes.

## What requires real hardware
Use 4–6 boards plus phones or simple sensors. Start with harmless classroom/outdoor observations and known public datasets. Any statement about LoRa coverage or energy requires direct measurement.

## Messina teaching scenario
Groups can collect non-sensitive observations from permitted public or school areas and let relay nodes carry compact claims back to school. Only selected evidence is requested over Wi-Fi when a claim is interesting or uncertain.

## Privacy / security
Avoid faces, private property and precise sensitive-species coordinates; strip unnecessary metadata; keep reviewer identity separate from relay identity; preserve model and evidence provenance.

## Difficulty
**Medium.**

## Why this is distinct
UC-007 scouts generic edge-AI events and UC-060 ferries visual survey evidence; UC-116 adds an explicit **claim -> selective evidence -> human/edge verification** workflow for citizen-science observations.
