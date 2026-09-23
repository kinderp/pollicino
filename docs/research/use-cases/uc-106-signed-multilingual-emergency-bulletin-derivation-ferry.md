# UC-106 — Signed Multilingual Emergency Bulletin Derivation Ferry

## Idea

Distribute one exact authoritative emergency/civil-protection bulletin, then allow disconnected edge nodes to create **clearly marked derived versions** such as translations, simplified language or accessibility-oriented summaries while preserving a cryptographic link to the original source.

The original bulletin remains authoritative. Every derived artifact must say exactly what it is:

```text
AUTHORITATIVE SOURCE
    -> derived translation / simplification
    -> machine-generated or human-reviewed state
    -> source hash + derivation metadata
```

## Problem solved

A resilient bulletin that reaches a disconnected group is useful only if recipients can understand it. In a real community there may be multiple languages, literacy levels or accessibility needs.

The dangerous shortcut is to let an AI-generated translation silently replace the source. UC-106 instead treats translation/simplification as a **derived artifact with provenance and review state**.

This makes the scenario useful for civil-protection drills while also exercising Raiatea-style provenance and edge AI.

## Actors / nodes

- authoritative bulletin publisher/coordinator;
- student relay/store-and-forward nodes;
- recipient groups;
- edge translation/simplification worker;
- optional human reviewer/teacher;
- optional Raiatea store preserving source and derived artifacts;
- optional Internet gateway for language models or terminology resources when permitted.

## Why PollicinoNet fits

The authoritative header, source hash, language code and derivation status are compact. Rich text/audio/image resources can move later.

- **DISCOVERY:** bulletin ID, language variants available, review status, expiry/update indicator;
- **EXACT:** authoritative source hash/signature, derived artifact hash, language, model/tool/version, reviewer identity/receipt where used;
- **SEMANTIC:** readable labels such as `Italian`, `English`, `simple-language`, never a substitute for the exact source/derivation identity.

The frozen LoRa PHY is unchanged. LoRa can announce and carry compact bulletin/control state; richer bearers carry longer text, audio and resources.

## Possible bearers

- **LoRa:** bulletin ID, urgency/status, source hash, available-language list, short text when it safely fits, derivation/review state;
- **BLE:** nearby transfer of text/audio resources;
- **Wi-Fi/LAN:** complete CAP-like bulletin, translations, images/audio and provenance records;
- **Internet:** optional source ingestion or translation assistance when available;
- **physical transport:** student-carried cache/phone/USB transports full multilingual packs between disconnected islands.

## What we can test now in software

Use fictional civil-protection messages only.

Create an authoritative source and derive several variants:

- Italian source -> English translation;
- Italian source -> simplified Italian;
- Italian source -> short spoken/audio script;
- machine translation with no review;
- machine translation later reviewed by a human;
- intentionally stale derived translation after the source has been updated.

Test invariants:

- a derived artifact always points to an exact source hash;
- source update makes old derivations visibly stale/pending-review;
- a translation can never upgrade itself to `AUTHORITATIVE`;
- conflicting translations remain separate artifacts rather than silently overwriting one another;
- recipients can always retrieve/display the authoritative source when available;
- cancellation/update of the source propagates to derived variants;
- a model/tool version is preserved in provenance;
- missing language support returns `UNAVAILABLE`, not an invented translation.

Useful software metrics include source-to-derived latency, stale-derived detection, percentage of recipients with a usable variant, review turnaround and bytes moved per bearer. Translation quality must be evaluated with an explicit test set/human review, not assumed from model reputation.

## What requires real hardware

A first physical drill can use:

- 5–8 boards split into two or three disconnected groups;
- one publisher at school;
- one laptop/Pi acting as translation worker;
- one teacher/student reviewer;
- a fictional bulletin with at least two language variants;
- relay delivery across real student contacts;
- rich-bearer retrieval of the full multilingual pack.

Measure only network/process facts we actually observe: propagation timing, which exact versions reached which test nodes, duplicate/stale handling and transfer success. Do not present the exercise as a validated emergency-alerting system.

## Messina teaching scenario

A fictional exercise message is published at a school node in Messina. One group around Villafranca receives the authoritative Italian version. Another relay later reaches Rometta/Venetico, where an edge worker creates an English and simplified-Italian derivative. A reviewer marks one translation `REVIEWED`.

Before that derivative reaches Spadafora, the authoritative source is updated. The network must make the old translation visibly stale and request/regenerate a derivative from the new exact source instead of continuing to display it as current.

This creates a concrete lesson in provenance, stale information, AI limitations and resilient communication.

## Privacy / security

The main risk is misinformation rather than personal-data leakage.

- authenticate authoritative publishers;
- never let derived content masquerade as authoritative content;
- bind every derivative to the exact source hash and source version;
- preserve `machine-generated`, `human-reviewed`, `stale` and `cancelled` states;
- keep urgency/severity/certainty values from the source unless an authorized transformation policy says otherwise;
- do not allow a translation to silently change actionable numbers, times, places or instructions;
- rate-limit malicious/flooded derivative generation;
- use only fictional drills until independently validated for real emergency use;
- avoid collecting unnecessary recipient identity/location data.

## Difficulty

**Medium.** Distribution is straightforward; correct provenance, update invalidation and human/AI review semantics are the important design work.

## Why this is distinct

- **UC-002:** distributes small signed authoritative bulletins.
- **UC-099:** derives document-processing artifacts for Raiatea ingestion.
- **UC-106:** preserves an authoritative emergency message while distributing multiple language/accessibility derivatives with explicit provenance and review state.

## Standards signal

OASIS Common Alerting Protocol (CAP) 1.2 permits multiple `info` blocks and explicitly supports multiple languages. CAP also separates alert metadata, human-readable information, resources and geographic areas. UC-106 can borrow these semantics without claiming to be a full CAP implementation or a production public-warning system.

References:

- https://docs.oasis-open.org/emergency/cap/v1.2/cs01/CAP-v1.2-cs01.html
- https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.pdf
