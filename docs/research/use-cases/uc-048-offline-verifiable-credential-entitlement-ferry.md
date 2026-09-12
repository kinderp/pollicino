# UC-048 — Offline Verifiable Credential and Entitlement Ferry

## Idea

Let a person or device prove a **small scoped entitlement while Internet is unavailable**, without giving every relay a reusable password or requiring a live identity server.

Examples include a synthetic school-lab authorization, permission to borrow a test kit, eligibility to access a local course pack, or authorization to submit one class job. The first experiments must use synthetic identities and harmless entitlements, not real identity documents or access-control decisions.

## Problem solved

Many systems can verify permissions only by contacting a central server. That fails when a verifier is offline or when issuer, holder and verifier are separated by a network partition.

The useful question is not “who are you in every possible sense?” but often something narrower:

```text
May this holder perform action X?
Is credential C still valid enough for this context?
Does the verifier have sufficiently fresh issuer/revocation state?
```

PollicinoNet can ferry compact credential/status material so that a verifier can make a limited offline decision from signed evidence it already trusts.

## Actors / nodes

- issuer node, for example a school or test authority;
- holder node carrying the credential or short-lived presentation;
- verifier node, for example a lab laptop, classroom hotspot or equipment station;
- student relay/store-and-forward nodes carrying trust/status updates;
- optional school/server node publishing credential status or revocation epochs;
- optional UC-019/UC-020 services for revocation freshness and time evidence.

## Why PollicinoNet fits

Credential verification separates naturally into small control objects and richer private exchange:

- **DISCOVERY:** an opaque indication that a compatible credential/presentation can be offered;
- **EXACT:** issuer key ID, credential/presentation hash, validity/freshness metadata, status-list or revocation epoch references;
- **SEMANTIC:** a human label such as `lab-access` or `equipment-borrowing`, never a replacement for exact authorization data.

LoRa is useful for tiny issuer/status updates and rendezvous metadata. The actual credential or privacy-preserving presentation should normally move over BLE/Wi-Fi or be presented directly by the holder.

Store-and-forward matters because a verifier may receive the latest trust/revocation state from a student relay before it ever meets the credential holder.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** issuer/status epoch, credential-type capability, revocation/status digest, short-lived rendezvous token;
- **BLE/NFC:** close-range credential presentation between holder and verifier;
- **Wi-Fi/LAN:** richer presentation, policy bundle or status-list synchronization;
- **Internet:** optional issuer/status refresh when connectivity exists;
- **physical transport:** a device carries signed trust/status state between disconnected islands.

## What we can test now in software

Use only synthetic identities and entitlements.

- define a minimal issuer/holder/verifier model;
- issue signed test credentials such as `may-use-lab-printer` or `may-borrow-kit-A`;
- verify a credential entirely offline against locally cached issuer keys;
- bind a presentation to a specific verifier/challenge so replay elsewhere fails;
- test expiry, wrong issuer, altered claim and forged-signature rejection;
- combine with UC-019 to test revoked credentials under fresh, stale and unknown revocation state;
- combine with UC-020 so time-dependent decisions preserve explicit uncertainty instead of inventing precise time;
- test selective disclosure or claim minimization where supported by the chosen credential library;
- keep an audit record of the decision without storing unnecessary personal claims;
- compare full credential transfer with a smaller presentation/status path;
- measure bytes per bearer, verifier decision time, stale-status exposure and relay propagation delay.

A useful invariant is:

> a relay may help a verifier obtain trust/status evidence, but possession of that evidence never grants the relay the holder's entitlement.

## What requires real hardware

- 3–4 boards/devices representing issuer/status source, holder, verifier and optional relay;
- one deliberately disconnected verifier;
- a real LoRa status/trust update followed by BLE/NFC/Wi-Fi presentation;
- replay attempts with a captured old presentation;
- delayed revocation propagation and a measured transition from `unknown/stale` to `current` status.

The hardware experiment must remain a teaching demo. Do not connect prototype authorization to doors, payments, safety systems or regulated identity workflows.

## Messina teaching scenario

Give each student group a synthetic credential that allows one harmless action, for example downloading a specific offline course pack or checking out one test electronics kit at school.

A verifier in `Rometta/Venetico` is intentionally cut off from the issuer. A relay arriving from the school node carries a newer trust/status epoch. Later the student holder presents a short-lived credential proof locally. The class records whether the verifier correctly accepts, rejects or returns `STATUS_TOO_STALE` under controlled cases.

A second exercise can revoke one synthetic credential and measure how long the revocation state takes to reach all disconnected verifier nodes through ordinary student mobility.

## Privacy / security

Credentials are highly sensitive even when they do not contain legal identity.

- use synthetic/pseudonymous identities in all teaching tests;
- do not broadcast names, dates of birth, classes or stable identifiers over LoRa;
- prefer narrow claims and short-lived presentations;
- bind presentations to verifier/challenge/context where practical;
- treat stale revocation/status state explicitly;
- separate authentication from authorization: proving control of a key does not imply permission for every action;
- never let a relay gain reusable bearer credentials merely by forwarding them;
- minimize logs and retention;
- do not claim compatibility with real institutional identity systems without dedicated interoperability and security review.

## Difficulty

**Medium–High.** Basic signature verification is straightforward; correct privacy, revocation freshness, replay resistance, selective disclosure and policy semantics are the real work.

## Research / standards signal

W3C published the Verifiable Credentials 2.0 family as Recommendations on 15 May 2025. The family explicitly addresses cryptographically secure, privacy-respecting, machine-verifiable credentials; related recommendations include JOSE/COSE protection and a compact status-list mechanism. This makes offline-verifiable entitlement a mature standards direction to study, while PollicinoNet should start with a much smaller synthetic profile and validate its own transport/freshness behavior.

References:

- https://www.w3.org/press-releases/2025/verifiable-credentials-2-0/
- https://www.w3.org/TR/vc-jose-cose/
