# UC-EVIDENCE-001 — Integrity-first field evidence manifest ferry

Status: RESEARCH / PROTOTYPE, EMERGENCY-ADJACENT

## Problem

A field observer, sensor, robot or drone may capture a photo, short video, audio clip or log that is far too large for a scarce LoRa contact. The rich object can remain on local storage while a small integrity/provenance manifest is ferried immediately. Later, when Wi-Fi/LAN/Internet is available, an authorized reviewer retrieves the exact object and verifies that it matches the earlier manifest.

The defining requirement is **integrity and provenance across delayed custody**, not ordinary content discovery. This distinguishes the use case from `UC-CITSCI-001` and `UC-CONTENT-001`, although it can reuse their reference/manifests.

PollicinoNet must not call this a legally valid digital-evidence or certified chain-of-custody system. The initial goal is research-grade integrity and transfer traceability.

## Actors / nodes

- field observer/student in a supervised exercise;
- fixed sensor, robot or drone producing evidence artifacts;
- student-carried or vehicle relay nodes;
- school/lab review node;
- optional future Civil Protection analysis node under separate authorization;
- rich storage/provider holding the original bytes.

## Messina educational / emergency-adjacent scenario

During a controlled exercise, a student or robot photographs a **synthetic** damaged marker, blocked-path prop or instrument reading in a pseudonymous zone. The media remains on the capture device or encrypted storage. LoRa carries a small manifest such as:

```text
artifact_id
content_hash
media_class
capture_source_role
coarse_zone
capture_time + uncertainty
provider/reference
manifest_generation
optional signed custody receipt
```

The manifest can reach school before the bulk object. At school/home Wi-Fi, the exact media is later retrieved and its hash checked.

Do not use identifiable people, vehicle plates, home addresses or sensitive sites in the first pilot.

## Why PollicinoNet fits

PollicinoNet already has relevant primitives:

- exact object/manifests and hashes;
- reference-first content movement;
- store-carry-forward;
- custody/provenance concepts;
- `UC-TIME-001` for explicit time uncertainty;
- `UC-TRUST-001` for future signed authority/revocation;
- rich-bearer resolution after scarce-link discovery.

This creates a concrete use case for keeping “what object is this?” and “who/what handled this manifest?” stable across LoRa, physical carry and later Wi-Fi retrieval.

## Possible bearers

- LoRa for hash/manifests, custody receipts and tiny textual observations;
- BLE for capture-device to Pollicino handoff;
- Wi-Fi/LAN for the actual photo/video/log;
- Internet for authorized remote storage/review if available;
- physical transport for delayed custody.

## What can be tested now in software

1. generate synthetic binary artifacts and SHA-256 manifests;
2. tamper with a byte after manifest creation and verify failure;
3. lose the rich object while the manifest survives;
4. duplicate/replay an old manifest generation;
5. transfer custody through several pseudonymous relay roles;
6. deliver a derivative/redacted artifact and require a new hash/reference rather than silently replacing the original;
7. simulate uncertain clocks and out-of-order receipts;
8. compare simple signed manifest only versus append-only transfer receipts;
9. measure bytes spent on integrity/custody metadata;
10. resolve the rich artifact only after reaching `RICH_HOME`.

The simplest baseline is a content hash + source signature + provider reference. Add richer custody logs only if a concrete hypothesis shows they are needed.

## What requires real hardware

Real devices are required before claiming:

- capture-to-manifest latency/energy;
- storage durability after reboot/power loss;
- real BLE/Wi-Fi handoff behavior;
- field usability while wearing/carrying the device;
- real media transfer time;
- any RF contact/capacity figure;
- robustness of robot/drone capture integration.

HW-006 remains the RF prerequisite; it does not by itself establish evidence-system security or legal validity.

## Privacy / security

- collect only deliberately staged/public non-sensitive material first;
- encrypt sensitive rich artifacts at rest and in transit;
- keep relay-visible manifest metadata minimal;
- use coarse zones, not student/home GPS traces;
- signed source/manifest generations where authenticity matters;
- anti-replay and anti-rollback;
- role-based access to rich media;
- explicit retention/deletion policy;
- derivatives/redactions get new identities/hashes while preserving provenance links;
- never imply that a hash alone proves who captured an object or when it was captured;
- never imply court admissibility or official Civil Protection chain of custody without the required legal/organizational process.

## Implementation difficulty

**High.** Hashing is easy; trustworthy provenance, key custody, time, role authorization and human procedures are the hard parts.

## Minimal measurable hypotheses

- H1: small integrity manifests can arrive earlier/more reliably than bulk media and still bind later retrieval to the original bytes.
- H2: a simple hash + signed source generation catches the main synthetic tamper/replay cases without a heavy ledger.
- H3: custody metadata remains small enough to be useful on scarce links while rich media stays off LoRa.

## Metrics

- manifest bytes versus artifact bytes;
- verified artifact retrieval rate;
- orphan-manifest/orphan-artifact rate;
- tamper detection rate;
- custody gaps/invalid transitions;
- replay/rollback rejection;
- time from capture to manifest arrival;
- time from capture to rich-artifact availability;
- storage/metadata overhead.

## Success / kill criterion

**Continue** if the reference-first integrity pattern catches staged corruption/replay and provides clear value beyond ordinary content discovery with modest metadata.

**Reject/defer** any ledger/blockchain/general audit system unless the simple signed-manifest baseline demonstrably fails a concrete requirement.

## Gate decision

**PROTOTYPE / RESEARCH.** Useful for citizen science, robot inspection and emergency-adjacent exercises, but not an official evidentiary system.

## Related precedent

NIST defines chain of custody as tracking evidence through collection, safeguarding and analysis while documenting handlers, transfer times and purposes: https://csrc.nist.gov/glossary/term/chain_of_custody . This motivates explicit custody metadata, but PollicinoNet does not claim to implement a compliant forensic process merely by carrying hashes.
