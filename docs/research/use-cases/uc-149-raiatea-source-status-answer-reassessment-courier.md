# UC-149 — Raiatea Source-Status and Answer-Reassessment Courier

## Problem solved

Keep a cached answer linked to the current status of its sources when an offline corpus later receives an update.

## Actors / nodes

Raiatea corpus, metadata source, answer cache, relay and reviewer.

## Why PollicinoNet fits

Status metadata is small and can move before replacement documents. The frozen LoRa PHY remains unchanged.

## Possible bearers

LoRa for compact status; BLE/Wi-Fi for metadata and documents; Internet or physical transport when available.

## What we can test now in software

Use a public corpus, change the status of one source and verify that dependent answers are marked for reassessment while their old provenance remains visible.

## What requires real hardware

Use 3–5 boards and 2–3 corpus hosts, keeping one host offline while the source status changes.

## Privacy / security

Use public documents first, minimize query metadata and preserve source hashes.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-120 handles derived-artifact invalidation and UC-147 handles missing evidence. UC-149 handles a later change in the status of evidence already present.
