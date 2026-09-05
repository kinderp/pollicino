# UC-CODEBOOK-001 — Shared compression side-information ferry

Status: PRIMARY / PROTOTYPE-DRIVING research bridge between Pollicino compression and PollicinoNet

## Problem

Pollicino's central research question is whether two peers that already share useful prior knowledge can exchange fewer bits while still reconstructing authoritative bytes exactly.

The school-network pattern creates a concrete opportunity: during the dense morning phase, nodes may cheaply synchronize a **small shared compression dictionary/model identity** over Wi-Fi or local high-capacity contact. In the afternoon, when only scarce/intermittent LoRa contacts remain, messages from the same domain may be encoded against that shared side information.

The question is measurable:

> does carrying a bounded shared codebook/model before separation reduce total end-to-end scarce-link bytes enough to justify the storage, versioning and bootstrap cost?

This is distinct from `UC-PREFETCH-001`: PREFETCH chooses which application objects to place. CODEBOOK prepositions **shared decoding side information** that changes how later application objects can be represented losslessly.

## Actors / nodes

- school hub or trainer/source of a test codebook;
- student-carried Pollicino nodes;
- territorial peers using the same topic/domain;
- optional fixed sensors producing repetitive small records;
- home/school Wi-Fi or LAN gateway;
- experiment recorder measuring total bootstrap + payload cost.

## Why PollicinoNet fits

This workload joins Track A and Track B without inventing a magical hash-to-file mechanism.

PollicinoNet already provides:

- exact object identity and SHA-256 verification;
- content-addressed store;
- bearer transitions;
- durable state and restart;
- total wire/TRC accounting;
- topic/domain use cases that produce repeated micro-objects.

A shared dictionary/model can therefore be treated as an explicitly versioned prerequisite. If the receiver lacks the exact side-information fingerprint, decoding must fail closed or fall back to an ordinary representation.

## Candidate side information

Start from simplest to richest:

1. static byte dictionary for one synthetic record family;
2. zstd-style trained dictionary or equivalent classical shared dictionary;
3. compact domain-specific token table;
4. only later, a tiny learned predictor/checkpoint if Track A provides evidence that it beats the classical baseline.

Do not jump directly to a neural model.

## Possible bearers

- Wi-Fi/LAN at school: preferred bootstrap of dictionary/model bytes;
- BLE: local side-information synchronization between nearby devices;
- LoRa: only if the codebook is very small or a missing-dictionary repair is demonstrably worthwhile;
- Internet: optional retrieval of a signed/hashed codebook version;
- physical carry: the student node carries the synchronized decoder state into the afternoon territorial network.

## What we can test immediately in software

Create repeated small workloads from existing use cases, for example:

- IoT sensor records;
- task-board state transitions;
- public classroom-resource descriptors;
- synthetic emergency-bulletin fixtures;
- DNA-like topic micro-information.

For each workload compare:

```text
raw / baseline framing
classical compression without shared dictionary
shared dictionary + compressed payload
shared dictionary + fallback when peer lacks it
```

Account **all bytes**, including:

- dictionary bootstrap bytes;
- dictionary identity/version bytes;
- negotiation/fallback control;
- encoded payload;
- ACK/retry overhead;
- storage cost;
- periodic refresh/replacement.

Experiments should sweep number of later messages per synchronized codebook and find the break-even point.

## Messina student-network scenario

Morning school phase:

```text
school hub
  -> codebook/topic-v3 synchronized locally
  -> students depart
```

Afternoon:

```text
Rometta-like / Spadafora-like / Saponara-like logical clusters
  -> many repetitive small records exchanged over scarce contacts
  -> receivers decode only if the exact codebook fingerprint is present
```

Town names remain logical labels; no inter-town LoRa link is assumed.

## What requires real hardware

Software can prove exactness and modeled break-even now. Hardware is required later for:

- actual ESP32 RAM/flash budget for codebooks;
- actual compression/decompression CPU time;
- energy cost versus bytes saved;
- real LoRa airtime/encounter savings after HW-006 calibration;
- reboot/persistence behavior;
- mixed-version field behavior when some nodes miss the morning synchronization.

A separate embedded feasibility gate is required before a learned model is considered.

## Privacy and security

- codebooks must not contain recoverable private student data;
- train/construct initial dictionaries only from public or synthetic corpora;
- content-address and version every codebook;
- authenticate codebook provenance before production-like use;
- reject version mismatch deterministically;
- preserve an uncompressed/classical safe fallback;
- never treat compression model identity as authorization to access content.

## Difficulty

**Medium for classical dictionaries; high for learned side information.** The experiment is scientifically useful even if the result is negative.

## Success / kill criteria

Adopt a shared-codebook path only if, over a preregistered workload, total cost including bootstrap is lower than the simplest no-codebook baseline for a practically meaningful number of messages, exact reconstruction is deterministic, and embedded resource cost remains acceptable.

If the break-even requires unrealistic message counts or codebooks are too expensive to store/compute, retain the result as a negative research finding and use ordinary compression/raw transfer.

## Physical evidence boundary

Software/model results do not imply LoRa airtime savings in the real student network until HW-006 and actual frame-size/control measurements calibrate the scarce-link model. The frozen PHY remains unchanged.