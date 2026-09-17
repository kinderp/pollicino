# UC-076 — Artifact Usage-Policy and License Envelope Ferry

## Idea

Make an exact content object travel together with a **machine-readable usage-policy reference** so that a disconnected cache or edge node can answer not only "do I have these bytes?" but also:

> under the policy state I currently know, may this actor use this exact artifact for this exact purpose?

The first experiments should use synthetic policies and public/open content. This is not an attempt to build DRM or to make legal judgments automatically.

## Problem solved

PollicinoNet can distribute documents, software, datasets and AI artifacts through many caches. Possession alone, however, does not imply permission for every action.

Examples:

- a course pack is available to one class but not public redistribution;
- a dataset may be usable for a specific teaching/research purpose;
- an AI model or adapter may have a known license that must remain attached to its exact hash/version;
- a document may be readable but not eligible for a particular automated pipeline;
- policy may be superseded or revoked while a cache is offline.

If bytes move faster than policy metadata, an offline node can make a stale decision. If policy moves without exact artifact binding, the wrong rules may be applied to a different version.

## Actors / nodes

- artifact publisher/owner or policy issuer;
- authorized user/service node;
- student relay/store-and-forward nodes;
- opportunistic cache nodes;
- Raiatea/document nodes;
- AI model/dataset consumers;
- optional UC-048 credential/entitlement verifier;
- optional UC-019 revocation/trust state and UC-020 freshness source.

## Why PollicinoNet fits

Policy metadata is compact compared with the content it governs.

- **DISCOVERY:** `artifact available`, `policy update available`, coarse eligibility hint;
- **EXACT:** artifact hash/version, policy ID/version/hash, issuer, action, purpose/context constraints, expiry and supersession state;
- **SEMANTIC:** friendly policy/category labels, never a substitute for the exact policy object and artifact identity.

LoRa can ferry policy digests and freshness state while BLE/Wi-Fi/LAN or physical carry transfers the artifact and full policy document. A cache may transport encrypted bytes without being entitled to use them.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** artifact ID/hash, policy ID/version/hash, eligibility/status hint, expiry/supersession notice;
- **BLE:** nearby policy/artifact synchronization;
- **Wi-Fi/LAN:** full policy documents, model/dataset/document objects and audit records;
- **Internet:** optional authoritative policy/licensing source;
- **physical transport:** a student carries cached artifacts while compact policy state converges separately.

## What we can test now in software

Start with public/open test artifacts and synthetic policy rules.

Define an `ArtifactPolicyBinding` that includes at least:

```text
artifact_hash
policy_id
policy_version
policy_hash
issuer
allowed_action
purpose/context
subject/role constraint
not_before / expiry
supersedes
```

Then test:

- artifact arrives before its policy;
- policy arrives before the artifact;
- old policy arrives after a newer policy;
- two policies conflict;
- artifact version changes but a stale policy binding remains;
- actor has bytes but lacks the required UC-048 entitlement;
- policy permits `read` but not `redistribute`;
- purpose mismatch;
- expired policy/freshness state;
- malicious relay swaps policy metadata between two artifacts;
- node is offline too long and must return `policy-status-unknown` rather than guessing;
- audit receipt records which exact policy version was used for a decision.

A useful first policy profile should stay deliberately small: `action`, `purpose`, `subject-role`, `expiry`, `supersedes` and exact artifact binding.

Key invariant:

> policy evaluation can restrict what a cooperating PollicinoNet service will do; it cannot guarantee that a malicious recipient will obey a policy after receiving decryptable bytes.

## What requires real hardware

- 3–5 PollicinoNet nodes;
- two caches holding different public/open artifacts;
- one authorized and one intentionally unauthorized synthetic client identity;
- one policy update that reaches nodes later than the artifact;
- a real LoRa policy/status exchange plus Wi-Fi/BLE artifact transfer;
- measured policy-convergence delay and number of stale/unknown decisions.

No proprietary, confidential or student-sensitive material is needed for the first experiment.

## Messina teaching scenario

Create three content classes:

1. a public open-source package;
2. a teacher-created course pack marked for a synthetic `class-A` role;
3. a public AI model with its exact SPDX/license metadata attached.

Caches representing `Messina`, `Villafranca` and `Rometta/Venetico` hold different objects. Student relay nodes move the objects and later carry a policy update. The exercise intentionally creates a period where a cache has the artifact but only stale policy state.

The correct result is not "allow because the file is present". It is `allow`, `deny`, or `policy-status-unknown` based on exact, current-enough evidence.

## Privacy / security

- policy metadata can reveal sensitive membership or interests, so do not broadcast class/person names when an opaque role is sufficient;
- bind every policy to the exact artifact hash/version;
- authenticate policy issuers and supersession/revocation state;
- separate artifact transport from decryption/use authority;
- fail closed or return `unknown` when policy freshness is insufficient for the requested action;
- do not present experimental policy evaluation as definitive legal advice;
- do not use DRM-like surveillance of student behavior;
- keep decision logs minimal and retention-limited.

## Difficulty

**Medium–High.** Transport is easy. The interesting work is exact binding, policy precedence, stale state, conflict handling and making `unknown` a first-class result instead of silently allowing use.

## Relationship to existing use cases

- **UC-004 / UC-006:** move AI artifacts and Raiatea documents.
- **UC-048:** proves that an actor holds a narrow entitlement.
- **UC-056:** binds donated data to consent/purpose provenance.
- **UC-076:** binds a general artifact to a versioned usage-policy decision at the point of use.

## Research / standards signal

W3C ODRL 2.2 is a Recommendation for expressing permissions, prohibitions, duties and constraints over assets and services. SPDX is an ISO-standardized ecosystem for machine-readable software/package metadata and license expressions; SPDX lists version 3.0 as the current specification, while a 3.1 release candidate was published in January 2026. PollicinoNet does not need to implement all of either standard initially, but both are useful references for exact artifact/license/policy binding.

References:

- https://www.w3.org/TR/odrl-model/
- https://www.w3.org/TR/odrl-vocab/
- https://spdx.dev/use/specifications/
- https://spdx.dev/learn/handling-license-info/
