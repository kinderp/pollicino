# UC-141 — Progressive Representation and Graceful-Degradation Content Ferry

## Idea

For one logical asset, publish a ladder of independently useful representations so short contacts deliver something usable first and richer detail can arrive later.

Examples: document metadata then extracted text then PDF; image thumbnail then medium image then original; coarse map then detailed vector layer then imagery; short transcript then compressed audio then original.

## Problem solved

UC-112 can resume one exact large object across many contacts, but sometimes a user gets no value until enough bytes arrive. Sending a complete small derivative may be more useful than sending the first bytes of a much larger file. The lower representation is a complete, explicitly derived object with its own hash and provenance, not merely a partial transfer.

## Actors / nodes

Publisher/source, derivative worker, student relay/store-and-forward nodes, requester, cache, optional Raiatea pipeline, optional edge-AI summarizer and UC-120 invalidation service.

## Why PollicinoNet fits

Representation manifests are compact and can bind source hash, representation ID/level, derivation tool/version, MIME type, byte size, fidelity label, freshness and policy/license state. LoRa handles discovery/negotiation; richer bearers carry the selected representation.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: source/representation IDs, size class, available-level bitmap and request.
- BLE: text, thumbnails, low-resolution maps and compact previews.
- Wi-Fi/LAN: full PDF, original image/audio or detailed maps.
- Internet: optional alternate source for richer levels.
- Physical transport: highest-fidelity representation on phone/USB/SSD.

## What we can test now in software

Compare full-object-only, UC-112 partial-byte resume, fixed preview-first, contact-aware representation selection and progressive upgrade. Inject early contact termination, source changes after preview generation, old preview paired with new original, outdated derivation tool, forbidden derivative, caches with different levels and accidental confusion between preview-complete and source-complete.

Measure time to first usable representation, time to full fidelity, bytes before first useful result, stale/mismatched derivatives, upgrade success and metadata overhead.

## What requires real hardware

Use 4–6 boards plus phones/laptops with public images, PDFs and map assets. Create short repeatable BLE/Wi-Fi contact windows. Compare full-object-only against preview-first and progressive upgrade with the same contact script.

## Messina teaching scenario

A public field packet contains a 2 kB summary, a 100 kB low-resolution map, a 5 MB detailed vector package and a 30 MB photo/document bundle. A short contact in Villafranca delivers the summary/coarse map; a later encounter in Rometta/Venetico upgrades the map; the full packet reaches Spadafora later.

## Privacy / security

Bind every derivative to the exact source hash and derivation version, preserve UC-076 usage policy, apply UC-111 redaction when needed, mark machine-generated summaries/translations, invalidate derivatives through UC-120 when the source changes, and never label a lower-fidelity representation as the full source.

## Difficulty

**Medium.**

## Why this is distinct

UC-112 resumes the same exact object; UC-141 transfers complete useful derivatives of increasing fidelity. UC-045 prioritizes queued objects. UC-130 reuses shared byte chunks. UC-106 is specific to multilingual emergency derivatives.

## Research / implementation signal

Progressive and multi-representation delivery has a long systems history, and 2026 edge-network work still studies caches containing several quality representations of the same content. The useful PollicinoNet lesson is architectural, not a performance claim.

References:

- https://doi.org/10.1109/TNSM.2026.3695712
- https://arxiv.org/abs/2009.12480
