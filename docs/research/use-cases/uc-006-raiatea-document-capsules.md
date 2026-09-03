# UC-006 — Raiatea Document Capsules

## Idea

Use PollicinoNet beneath Raiatea/document workflows to advertise and distribute document versions, provenance metadata and missing chunks across disconnected nodes. LoRa carries only compact coordinates/version hints; the actual PDF, image set or document package should normally move over a richer link or by physical carry.

## Problem solved

A document collection may be needed at school, home or in a disconnected field setting. Full files may be large, but most updates can often be represented as a new manifest plus a small set of changed chunks.

## Actors / nodes

- Raiatea/document publisher or archive node;
- school server/NAS;
- student/teacher relay nodes;
- offline reader nodes;
- optional Internet resolver when connectivity returns.

## Why PollicinoNet fits

PollicinoNet already has `DISCOVERY`, `EXACT`, content addressing, P2P caches and richer-link handover. Raiatea can remain the domain/provenance layer while PollicinoNet answers where the exact authorized bytes can be found and how to move the missing pieces cheaply.

## Possible bearers

- **LoRa:** document coordinate, version, expiry, compact availability hint;
- **BLE/Wi-Fi:** local manifest/chunk exchange;
- **Internet/LAN/NAS:** bulk document retrieval;
- **physical transport:** cached document chunks move with a person/device between disconnected places.

No PHY change is required or proposed.

## What we can test now in software

- version a synthetic document corpus;
- chunk exact files and reuse unchanged chunks between versions;
- sign manifests and verify final object hashes;
- simulate offline readers that receive only new-version coordinates first;
- test cache invalidation/supersession without deleting still-referenced old versions;
- compare full retransmission with manifest + missing-chunk delivery using TRC.

## What requires real hardware

Only the scarce-link discovery/handover path needs LoRa hardware at first. The bulk document transfer can be exercised on ordinary PCs/phones over LAN/Wi-Fi before any field deployment.

## Privacy / security

Start with public-domain or explicitly authorized documents. Provenance/signature metadata should be exact. Private document coordinates must not leak stable identifiers or interests over public radio; access control and encryption remain mandatory. Copyright/licensing metadata should accompany distributed artifacts.

## Difficulty

**Medium.** The core mechanisms overlap strongly with PollicinoStore/P2P reconstruction; the main additional work is clean integration with Raiatea provenance/version semantics.
