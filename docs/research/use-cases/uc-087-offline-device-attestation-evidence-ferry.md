# UC-087 — Offline Device Attestation Evidence Ferry

## Idea

Let a board or edge device prove later, through delay-tolerant transport, **what software/firmware/configuration state it was actually running** when it performed a task or joined the network.

The device generates compact attestation evidence or an evidence reference. A relay carries that evidence to a verifier even if the verifier was unreachable at the time. The verifier returns an attestation result that can itself travel later to a relying party.

The goal is not to claim hardware trust where none exists. The first experiments may use synthetic measurements or software TPMs; stronger claims require appropriate hardware roots of trust and independently validated implementations.

## Problem solved

UC-068 enrolls a device identity, UC-069 stages firmware updates and UC-062 reports crashes. None of those alone answers:

> is this exact node currently running the expected software/configuration state?

A compromised or stale node might possess a valid identity while running an unexpected image. In a sparse network, a verifier may be offline for hours, so a conventional live challenge/response path is unavailable.

Useful questions include:

- what firmware/build measurement did the node report?
- was the evidence fresh enough for the requested decision?
- was the evidence generated before or after a known update campaign?
- is the reference-value set itself current?
- can an old good attestation be replayed after the node changes state?
- what should a relying party do when verification is impossible or stale?

## Actors / nodes

- **Attester:** student board, Raspberry Pi, robot or edge node;
- **Verifier:** school/lab service that appraises evidence against known reference values/policy;
- **Relying Party:** service deciding whether to trust/authorize the node for one bounded purpose;
- student relay/store-and-forward nodes;
- optional UC-019 trust/revocation state;
- optional UC-020 trusted-time/checkpoint state;
- optional UC-068 enrollment identity;
- optional UC-069 rollout campaign state.

## Why PollicinoNet fits

Attestation metadata can be small while endorsements/reference-value sets may be larger.

- **DISCOVERY:** attestation requested, verifier available, evidence/result pending;
- **EXACT:** attester identity, measurement set/hash, evidence nonce/epoch, verifier policy/reference-value version, attestation-result hash;
- **SEMANTIC:** labels such as `firmware-approved`, `lab-image`, `robot-runtime`, useful for humans but never substitutes for exact appraisal evidence.

PollicinoNet can transport evidence, reference-version hints and results asynchronously. It should never reinterpret a cryptographic attestation as merely a semantic label.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** challenge/evidence/result IDs, compact measurement digest, nonce/epoch, policy/reference version, `PASS/FAIL/INDETERMINATE/STALE` summary and hashes;
- **BLE:** nearby evidence transfer;
- **Wi-Fi/LAN:** full evidence, endorsements, reference values and audit logs;
- **Internet:** optional access to vendor endorsements or remote verifier;
- **physical transport:** laptop/board carries evidence or verifier material between disconnected islands.

## What we can test now in software

Begin with a synthetic attester and verifier, or with a software TPM where useful.

Define an `AttestationRequest`:

```text
request_id
attester_id
nonce_or_epoch
required_claims
appraisal_policy_id
expiry
```

and an `AttestationEvidenceEnvelope`:

```text
request_id
attester_id
evidence_hash
measurement_set
nonce_or_epoch
boot_or_runtime_id
created_checkpoint
```

plus an `AttestationResult`:

```text
request_id
attester_id
verifier_id
appraisal_policy_id
reference_values_version
result = PASS|FAIL|INDETERMINATE|STALE
result_hash
verified_checkpoint
```

Test:

- expected measurement passes;
- one firmware measurement changes;
- old good evidence is replayed;
- evidence arrives after its freshness window;
- verifier has stale reference values;
- reference values arrive later and allow re-appraisal;
- attestation result arrives before the relying party sees the underlying evidence;
- two verifiers use different policy versions;
- attester identity is valid but measurement state is not;
- evidence is duplicated/reordered without creating conflicting logical results;
- verifier is absent and the system must return `INDETERMINATE`, not `PASS`.

Useful metrics include evidence/result bytes, time-to-verdict, stale-evidence rate, replay rejection, reference-state delay and percentage of decisions that remain indeterminate under partitions.

A key rule is:

> device identity, attestation evidence and authorization are separate facts; a valid identity or signature is not itself proof that the device is in an approved runtime state.

## What requires real hardware

A staged validation path is appropriate:

1. synthetic evidence and deterministic verifier;
2. software TPM/emulated measured boot;
3. board or Raspberry Pi with a real supported secure-boot/TPM/secure-element path;
4. only then experiments where authorization depends on the result.

A first physical network experiment needs:

- 3–5 LoRa nodes;
- one attester device;
- one verifier laptop isolated from the attester at evidence-generation time;
- one student relay;
- two known software states, one expected and one deliberately changed.

The experiment must record exactly what hardware trust anchor, secure boot or measurement mechanism is present. If none exists, results are only software-protocol demonstrations.

## Messina teaching scenario

Prepare a lab image `A` and modified image `B` for a Raspberry Pi or development board. The node at a `Rometta/Venetico` island creates evidence while the verifier is at school and unreachable. A student relay later carries the compact evidence/result exchange.

The class tests four visible states:

```text
identity valid + expected measurement  -> PASS
identity valid + changed measurement   -> FAIL
identity valid + too-old evidence      -> STALE
verifier/reference state unavailable   -> INDETERMINATE
```

This is especially useful after UC-069 staged firmware rollout: a rollout health report can say “node is alive,” while UC-087 separately asks whether the node is running the expected measured state.

## Privacy / security

Attestation evidence can fingerprint devices and expose software inventories.

- reveal only claims necessary for the relying-party decision;
- do not broadcast full measurement inventories over LoRa;
- authenticate verifiers when evidence is sensitive;
- bind evidence to nonce/epoch/freshness semantics;
- keep reference values and appraisal-policy versions explicit;
- never convert `INDETERMINATE` or `STALE` into success;
- protect endorsements/reference data from unauthorized modification;
- do not claim a hardware-rooted property when using only software-emulated evidence;
- authorization decisions must remain scoped to the relying-party policy, not become a global “trusted/untrusted” label.

## Difficulty

**High.** The delay-tolerant transport is straightforward; meaningful freshness, reference-value lifecycle, privacy and genuine hardware-rooted evidence are the difficult parts.

## Why this is distinct from nearby use cases

- **UC-019:** distributes trust/revocation state.
- **UC-048:** carries user/device entitlements.
- **UC-062:** reports diagnostics/crash evidence.
- **UC-068:** establishes device identity/enrollment.
- **UC-069:** stages firmware rollout and health evidence.
- **UC-087:** transports and appraises **evidence about the actual measured device state** under intermittent connectivity.

## Research / standards signal

The IETF RATS architecture (RFC 9334) separates Attester, Verifier and Relying Party roles and explicitly treats Evidence, Reference Values, Attestation Results and freshness as distinct concepts. The Entity Attestation Token (RFC 9711, published in 2025) provides a standardized claims container that fits this architecture. These standards are useful conceptual anchors; PollicinoNet should experimentally validate its own delayed-evidence behavior and must not claim security properties beyond the hardware/software root actually present.

References:

- https://www.rfc-editor.org/rfc/rfc9334.html
- https://www.rfc-editor.org/rfc/rfc9711.html
