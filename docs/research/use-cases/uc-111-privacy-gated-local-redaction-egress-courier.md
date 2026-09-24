# UC-111 — Privacy-Gated Local Redaction and Egress Courier

## Idea

Before a document, prompt, field report or image is allowed to leave a trusted local node for an Internet gateway, cloud AI service or broader PollicinoNet audience, run a **local redaction/de-identification gate** and ferry only the approved derivative unless policy explicitly authorizes the original.

The original and redacted artifact remain different exact objects with explicit provenance:

```text
source_hash
  -> redaction_policy/version
  -> redacted_hash
  -> review/status
  -> allowed egress target class
```

## Problem solved

Intermittent networks often separate the moment data are created from the moment an Internet/cloud gateway becomes available. That delay is useful: it gives PollicinoNet an opportunity to enforce privacy before egress.

Examples:

- a Raiatea document should be summarized by a cloud model later, but names/emails must stay local;
- a field report contains a phone number that is unnecessary for a public bulletin;
- a student asks an external AI service a question containing accidental personal data;
- a diagnostic log contains usernames, paths or tokens that should not leave the device;
- a visual report needs EXIF/location or text-in-image redaction before broader distribution.

Encryption protects data while in transit, but an authorized remote service would still receive the plaintext. UC-111 reduces the plaintext that is allowed to leave in the first place.

## Actors / nodes

- source device holding the original private artifact;
- local redaction/anonymization worker;
- optional human reviewer;
- student relay/store-and-forward nodes;
- trusted Internet/cloud gateway;
- Raiatea/document or AI service receiving the approved derivative;
- policy authority defining what categories may leave for which purpose.

## Why PollicinoNet fits

PollicinoNet already carries exact artifacts, requests, provenance and delayed Internet fetch/compute jobs. UC-111 inserts an explicit privacy boundary between local data and an external destination.

- **DISCOVERY:** `redaction-capable`, policy profile, review-required flag and target/service class;
- **EXACT:** source hash, derivative hash, redaction tool/model/version, policy ID, reviewer status and egress authorization;
- **SEMANTIC:** detected categories such as `PERSON`, `EMAIL`, `PHONE`, `LOCATION` help policy but never replace exact provenance or authorization.

LoRa carries only compact job/status/control metadata. Original/redacted documents move over local BLE/Wi-Fi/LAN or remain on-device. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** redaction job ID, source/derivative compact IDs, policy/review status and gateway-ready notices;
- **BLE:** nearby local transfer to a trusted redaction worker;
- **Wi-Fi/LAN:** source document inside a trusted local zone and approved derivative to the gateway;
- **Internet:** only the policy-approved derivative is submitted to the external service;
- **physical transport:** phone/laptop/USB may carry the original to a trusted local workstation without ever exposing it to cloud transport.

## What we can test now in software

Start with synthetic/public documents containing planted sensitive fields and exact ground truth.

Test:

- regex-only versus local PII recognizer;
- replacement, masking, irreversible redaction and reversible pseudonymization;
- names, email, phone, addresses, IDs and custom school/project terms;
- accidental secret/token patterns in logs;
- image OCR followed by redaction on staged images;
- false positives that unnecessarily remove useful context;
- false negatives that leak a planted identifier;
- policy mismatch (`EMAIL allowed for service A, forbidden for public export`);
- stale redaction policy;
- redacted derivative arriving at gateway before human review;
- source document changed after redaction, forcing a new derivative;
- gateway refusing an artifact without a valid redaction/provenance envelope.

Useful metrics include planted-PII recall, false-positive rate, bytes retained/removed, review effort, blocked-egress count and provenance correctness. The prototype must report missed planted entities rather than claiming perfect anonymization.

A core invariant is:

> `redacted` means processed under one exact policy/tool/version, not guaranteed anonymous.

## What requires real hardware

A first physical test can use:

- 3–5 LoRa nodes;
- one laptop acting as local redaction worker;
- one separate laptop/Raspberry Pi acting as Internet gateway;
- synthetic documents with known planted identifiers;
- a requester that cannot directly reach the Internet;
- a relay carrying only the approved derivative to the gateway.

The original file should never be placed on the gateway in the privacy-preserving test. Network/energy benefits are not the goal of this first experiment.

## Messina teaching scenario

A student node in `Rometta/Venetico` creates a synthetic field report containing planted names, email addresses and a precise location. The report is intended for a later external summarization service reached through the school gateway in `Messina`.

A local worker produces a policy-bound derivative:

```text
exact source -> redact PERSON/EMAIL/exact location -> reviewed derivative
```

Only the derivative can receive an `egress-approved` ticket. A student relay can carry that derivative toward the gateway while the original remains local.

The class can intentionally insert identifiers the detector misses and observe why automated redaction needs measurable recall and, for higher-risk workflows, human review.

## Privacy / security

This use case exists specifically to reduce disclosure, but the redaction process itself is sensitive.

- process originals locally by default;
- never put raw PII in LoRa control messages;
- encrypt local transfers containing originals;
- bind derivatives to exact source hash and policy/version;
- require fresh review when source or policy changes;
- do not log detected raw values unnecessarily;
- treat reversible pseudonymization keys as secrets and keep them separate;
- redact EXIF/location and OCR-visible text when relevant;
- enforce target-specific policy: approval for one service does not authorize another;
- preserve UC-056 consent/purpose constraints;
- keep the ability to block egress when detection confidence is insufficient.

## Difficulty

**Medium–High.** Local redaction libraries are available; trustworthy policy binding, false-negative measurement, multimodal handling and safe egress authorization are the harder parts.

## Why this is distinct

- **UC-021:** encrypts sensitive content so carriers cannot read it.
- **UC-057:** moves an approved model toward private local data.
- **UC-088:** carries a bounded web/API request to an Internet gateway.
- **UC-111:** transforms sensitive local content into a **policy-approved reduced-disclosure derivative before egress**.

## Research / implementation signal

Presidio provides local/open tooling for PII detection and anonymization in text, images and structured data, including redact, mask, replace, hash and encrypt operators. Its own documentation explicitly warns that automated PII detection cannot guarantee that every sensitive item will be found. That warning is a useful design rule for PollicinoNet: the experiment should measure misses and expose uncertainty rather than label automated output as perfectly anonymous.

References:

- https://microsoft.github.io/presidio/
- https://microsoft.github.io/presidio/anonymizer/
