# UC-096 — Independent Reproducible Build Attestation Courier

## Idea

Ask two or more independent, intermittently connected builders to rebuild the **same exact source/materials under the same declared build recipe**, then ferry only compact signed build attestations and artifact digests through PollicinoNet. If independent builders produce the same digest, confidence increases that the distributed artifact corresponds to the declared inputs; if they disagree, the mismatch becomes evidence to investigate.

The large source tree, dependencies and built artifact move over Wi-Fi/LAN, cached media or physical transport. LoRa carries only identifiers, build requests, result digests and attestation status.

## Problem solved

UC-081 can distribute CI/test jobs, but `tests passed` does not answer a software-supply-chain question:

> Did two independent builders actually produce the same artifact from the same declared source and build recipe?

This matters for firmware, classroom tools, Romeo software, Python environments and future PollicinoNet releases, especially when disconnected nodes receive binaries long after they were built.

## Actors / nodes

- build requester/release coordinator;
- two or more independent builder nodes (laptop, workstation, Pi where compatible);
- dependency/source caches;
- student relay/store-and-forward nodes;
- artifact verifier/consumer;
- optional transparency/provenance service when Internet is available.

## Why PollicinoNet fits

The evidence is tiny compared with source trees and binaries. Builders do not need to be online at the same time, and an isolated verifier can later receive the independent build claims.

- **DISCOVERY:** builder supports build profile/toolchain P;
- **EXACT:** source commit/tree hash, dependency/material digests, recipe ID, toolchain/environment digest, artifact digest and attestation signer;
- **SEMANTIC:** `MATCH`, `MISMATCH`, `INCOMPLETE_EVIDENCE` or `UNSUPPORTED_PROFILE` derived from exact inputs and outputs.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** build request ID, exact source/material/recipe hashes, result digest, compact attestation status and missing-evidence requests;
- **BLE:** nearby attestation/result synchronization;
- **Wi-Fi/LAN:** git bundles, dependencies, container/Nix closures, artifacts and complete provenance;
- **Internet:** optional dependency/source acquisition or publishing when available;
- **physical transport:** USB/SSD/student laptop carries source/materials and artifacts to isolated builders.

## What we can test now in software

Start with a tiny deterministic project and a pinned build environment. Define:

```text
BuildRequest
  source_digest
  material_digests[]
  recipe_id
  toolchain_digest
  expected_output_name

BuildAttestation
  request_id
  builder_id
  environment_digest
  artifact_digest
  build_status
  provenance_hash
  signature
```

Then test:

- two builders producing the same artifact hash;
- an intentionally nondeterministic timestamp embedded in the output;
- wrong dependency version on one builder;
- wrong compiler/toolchain;
- stale source bundle;
- duplicate build request;
- one builder offline or unable to satisfy the profile;
- malicious/misconfigured builder claiming a digest not matching the transferred artifact;
- late third build that breaks an apparent 2-of-2 agreement;
- provenance present but artifact unavailable;
- exact match across builders but different test results from UC-081.

Useful metrics include build request/result delay, bytes of compact evidence, independent builder count, fraction of reproducible builds, mismatch causes and full artifact bytes that did not need to traverse LoRa.

A key semantic rule is:

> Matching attestations increase evidence about reproducibility; they do not magically prove that the source itself is safe or that supposedly independent builders were not compromised by the same dependency/toolchain.

## What requires real hardware

A first physical experiment can use:

- 3–4 student/school laptops or Pis;
- 3–4 LoRa nodes for request/attestation ferrying;
- one exact git bundle from UC-044;
- one pinned container/Nix environment or deliberately small native toolchain;
- an artifact small enough to compare locally.

Disable direct Internet between requester and builders so the build request and result metadata genuinely take the PollicinoNet path. Transfer source/materials over Wi-Fi or physical media when the nodes meet.

Only claim reproducibility for the exact tested build profile. Different CPU architectures or compilers are expected to produce different artifacts unless the build definition explicitly promises otherwise.

## Messina teaching scenario

A class can treat three geographically separated student nodes as independent builders:

1. school publishes exact commit + recipe IDs;
2. a relay carries the request toward Rometta/Venetico and Spadafora;
3. each builder obtains the exact source/material bundle through a rich bearer;
4. build attestations return separately;
5. school compares digests and, on mismatch, asks for the richer provenance/log.

This is a concrete software-supply-chain lab layered on the same real DTN.

## Privacy / security

- builders must be explicitly authorized for source/materials they receive;
- never put repository secrets, tokens or signing private keys in build bundles;
- attest exact material and environment digests, not human-friendly labels alone;
- sandbox build jobs and deny unnecessary network access where practical;
- preserve builder independence where the experiment is testing independent reproduction;
- sign attestations and bind them to one exact build request;
- distinguish reproducible output from trustworthy source, trustworthy dependencies and policy approval;
- do not publish private repository names or dependency inventories over broad LoRa discovery.

## Difficulty

**High.** The DTN envelope is small; reproducible builds are hard because hidden timestamps, environment state, dependency resolution and toolchain differences easily change outputs.

## Why this is distinct from nearby use cases

- **UC-044:** moves Git history/source offline; UC-096 independently rebuilds and compares exact outputs.
- **UC-081:** distributes CI/tests; UC-096 focuses on reproducibility and artifact provenance across independent builders.
- **UC-064:** detects equivocation in signed histories; UC-096 compares independently produced artifacts.
- **UC-087:** attests a device's measured runtime state; UC-096 attests a build process/result.

## Research / implementation signal

SLSA models build provenance around the builder, exact materials, invocation/build configuration and produced subjects. Its documentation also explicitly notes that verified reproducible builds are useful but not a complete supply-chain solution and that rebuilders should truly be independent. Current tooling and 2026 research continue to combine provenance with reproducible or attested builds. PollicinoNet's experiment would add delayed, store-and-forward distribution of independent build requests and compact verification evidence.

References:

- https://slsa.dev/spec/v1.2/provenance
- https://slsa.dev/spec/draft/faq
- https://arxiv.org/abs/2605.08363
