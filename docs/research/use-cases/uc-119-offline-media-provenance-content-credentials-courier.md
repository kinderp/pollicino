# UC-119 — Offline Media Provenance / Content Credentials Courier

## Idea

Carry compact, verifiable media-provenance information through PollicinoNet before or separately from a large photo, audio clip, video or document. A receiver should be able to distinguish "I have provenance that validates for this exact asset" from "this media merely looks plausible".

The frozen LoRa PHY is unchanged.

## Problem solved

Field reports, citizen-science observations, emergency drills and AI-generated media can all be copied, edited, resized or recompressed while offline. A detached image may arrive long before its provenance metadata, or vice versa.

We need a way to preserve exact asset identity, provenance claims, declared transformations, validation state and explicit UNKNOWN when provenance is missing or cannot yet be verified.

This is not a truth detector. Provenance can prove a signed history was attached to an asset; it cannot prove the depicted event itself happened.

## Actors / nodes

- camera/phone/document producer;
- optional AI or editing tool;
- relay/store-and-forward nodes;
- provenance verifier;
- evidence collector or Raiatea node;
- optional Internet-connected trust-material gateway.

## Why PollicinoNet fits

The media can be large while its identity and provenance status are compact.

- **DISCOVERY:** asset type, provenance-present flag, signer/trust-profile class, evidence availability.
- **EXACT:** asset hash, manifest hash, signer identity/fingerprint, validation result, ingredient/derivation references and tool/version.
- **SEMANTIC:** human description such as "cropped derivative" or "AI-assisted", never used as a substitute for signature validation.

LoRa carries the small identity/validation envelope; Wi-Fi/BLE carries the manifest and media; Internet can refresh trust material; physical transport can move full evidence.

## Possible bearers

- **LoRa:** asset ID/hash prefix, manifest ID, validation state, request for missing manifest;
- **BLE:** sidecar manifest or thumbnail;
- **Wi-Fi/LAN:** full media plus Content Credentials;
- **Internet:** optional trust-list, certificate-status or repository access;
- **physical transport:** camera card or encrypted evidence pack.

## What we can test now in software

Use public/synthetic media and current C2PA tooling where practical. Test an original asset with a valid manifest, an unauthorized alteration, a legitimate derivative with a new manifest, missing external provenance, asset/manifest arrival in either order, unknown trust state and two similar filenames bound to different hashes.

Measure bytes moved, validation outcomes and how often the system correctly returns VALID / INVALID / UNKNOWN rather than guessing.

## What requires real hardware

A first physical trial needs only 4–6 boards, two phones/cameras or laptops, and one verifier. Capture a harmless classroom object, produce an edited derivative, distribute media and provenance through different relay paths, then reconcile them.

No claim about authenticity of real emergencies, people or public events should be made from this teaching experiment.

## Messina teaching scenario

One student group creates a synthetic field-report image in a permitted school/public location. Another group receives only the compact provenance announcement first. The full image later reaches the verifier over Wi-Fi through a different student relay.

A second exercise introduces a legitimate crop and an unauthorized alteration and checks that the provenance workflow distinguishes them.

## Privacy / security

- provenance metadata can reveal creator/device identity, timestamps and location: include only what the exercise needs;
- avoid faces, private homes, license plates and sensitive coordinates;
- do not equate a valid signature with factual truth;
- preserve UNKNOWN when trust material is unavailable;
- never expose private signing keys to relay nodes;
- keep heuristic AI detection separate from cryptographic provenance.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-060 ferries visual evidence; UC-110 detects near-duplicates; UC-116 verifies a citizen-science claim. UC-119 focuses on **cryptographically bound media provenance and derivation metadata** that can travel separately from the heavy asset.

## Research / implementation signal

C2PA 2.4 was published in April 2026 and defines Content Credentials, signed manifests, derivations/ingredients and validation behavior across multiple media formats.

References:

- https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html
- https://doi.org/10.1145/3795513.3806658
