# UC-186 — Raiatea Claim-Level Contradiction and Adjudication Courier

## The problem
Two disconnected Raiatea corpora can contain *apparently valid but mutually contradictory claims* on the same narrow question. Finding more documents is not enough; an assistant must avoid quietly choosing one source or presenting a provisional answer as settled.

## Actors and example
A student asks a non-sensitive scientific question about a public environmental dataset. Raiatea instance A holds an older interpretation and instance B a corrected or competing interpretation. A claim extractor, source-bound evidence store, remote claim checker, opt-in reviewer and school relay nodes exchange **bounded challenge capsules**.

## Why PollicinoNet
Instead of shipping two whole corpora, use `claim_id + exact normalized proposition + source/version digests + contradiction_request_id + context_scope`. For LoRa, carry only opaque digests, concise states and an explicitly size-capped request; send propositions and copyrighted/private source text only over an authorized rich bearer. Contradiction is **not** proof that a source is false.

## Bearers
- **LoRa:** challenge identifier, source/version fingerprints, `SUPPORTS / CONFLICTS / UNKNOWN / NEEDS_CONTEXT` summary and review state.
- **BLE/Wi-Fi/LAN:** bounded quoted passages where permitted, document provenance and evidence graphs.
- **Internet:** optional authorized metadata resolver; **physical carry:** larger Raiatea corpus or index snapshots.

## Software-only test now
Partition a set of public/synthetic documents among three local Raiatea processes. Include an intentionally outdated fact, a statement only apparently contradictory because of differing dates/units, and two genuine competing interpretations. A query-to-data worker sends the exact claim and context to holders; challenge responses contain source spans and version IDs. Compute disagreement coverage, false contradiction alerts, unresolved-claim counts and answer changes after review. Do not treat majority vote among duplicate derivative documents as independent corroboration.

## Physical validation required
4–6 student relay boards and 3 laptops/Pi with separate local corpus snapshots. Delay one challenge result until after an initial answer. Verify that the answer remains `CONTESTED/PROVISIONAL` and that the new evidence triggers **review**, not silent overwriting. Physically measure relay/confirmation delays and transferred bytes before making field claims.

## Privacy/security
Public/synthetic corpora first; do not ferry private user questions in plaintext on broadcast control channels. Bind each claim to its exact source, extraction version and intended scope, preserve conflicting evidence and human override/audit, filter malicious prompt-injection text, enforce usage rights. No use for automated emergency/medical/safety decisions.

## Difficulty and distinction
**High.** UC-147 asks for *missing evidence*; UC-149 propagates *source-status changes*; UC-065 federates document search; UC-101 flags model disagreement. **UC-186 exchanges a specific contradictory claim, tests its context and manages an explicit evidence-based adjudication workflow.**

## Acceptance gates
1. Distinguish genuine contradiction from date/unit/scope mismatch.
2. No automatic "resolved" state from count of agreeing copies.
3. Every displayed answer carries claim/source status and provenance.
4. Late challenge responses remain ordered and auditable.
