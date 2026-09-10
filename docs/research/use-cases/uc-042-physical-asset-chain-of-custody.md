# UC-042 — Physical Asset Chain-of-Custody Courier

## Idea

Use PollicinoNet to record and ferry **signed custody handovers for real physical objects** such as school lab equipment, emergency-drill kits, sensors, batteries, document envelopes or spare parts.

The object itself moves physically. LoRa carries only small custody/status events and exact asset references.

## Problem solved

In disconnected environments a physical item may move through several people or locations before any central system is reachable.

Later we need to know:

```text
What asset was handed over?
From whom to whom?
In which coarse location/context?
Was the handover acknowledged?
Was the package/equipment condition noted?
Did any custody event arrive late or out of order?
```

UC-015 tracks a logical resource ledger. UC-042 is different: it treats **physical custody transitions themselves as signed evidence** tied to an asset identity.

## Actors / nodes

- school lab/warehouse node;
- student or teacher custodians;
- civil-protection drill teams using harmless training equipment;
- asset tag/QR/NFC label plus companion PollicinoNet node;
- student relay/store-and-forward nodes;
- optional central inventory/Raiatea documentation node;
- optional sensor attached to the asset for shock/temperature evidence.

## Why PollicinoNet fits

Custody events are naturally small and append-only.

- **DISCOVERY:** `asset A / custody update available` or `handover requested`;
- **EXACT:** asset ID/root, previous custody event hash, sender/receiver key IDs, signed acknowledgement, condition/evidence hash;
- **SEMANTIC:** labels such as `LoRa kit 12`, `first-aid training box`, `camera tripod`, never a replacement for the exact asset identifier.

The asset may travel farther than any direct radio path. Store-and-forward lets signed handover events catch up later without requiring continuous Internet.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** custody-event digest, handover request/acknowledgement, asset status, missing-event notice;
- **BLE/NFC/QR:** close-range confirmation that the person is physically with the asset;
- **Wi-Fi/LAN:** photos, manuals, detailed condition reports or complete event-log synchronization;
- **Internet:** optional central inventory synchronization;
- **physical transport:** the physical asset is itself the primary transported object.

## What we can test now in software

Create a simple append-only `CustodyEvent`:

```text
asset_id
previous_event_hash
event_type
from_id
to_id
time_checkpoint / uncertainty
coarse_location_or_context
condition_code
evidence_hash
signatures
```

Then test:

- normal handover chain A -> B -> C;
- duplicate event delivery;
- event arrival out of order;
- missing intermediate event;
- two conflicting claims of current custody;
- forged signature;
- receiver refuses/never acknowledges the handover;
- asset temporarily offline while event metadata moves separately;
- condition report with exact photo hash arriving later over Wi-Fi;
- integration with UC-020 time checkpoints and UC-031 sensor calibration provenance.

Useful metrics include time-to-ledger-convergence, unresolved custody gaps, duplicate overhead, conflict detection and evidence retrieval delay.

## What requires real hardware

- 3–5 LoRa nodes representing successive custodians;
- harmless tagged school equipment or a training box;
- optional QR/NFC/BLE proximity confirmation;
- a real moving asset that changes custodians/locations;
- deliberate network partitions and delayed event delivery;
- measured convergence time and radio/contact behavior.

No logistics or safety claim should be made from simulation alone.

## Messina teaching scenario

Prepare four identical-looking training boxes but give each one a unique exact asset identity. A box starts at school in Messina or the local institute and is handed through several student/teacher checkpoints in a controlled route toward Villafranca, Rometta, Spadafora/Venetico or Milazzo.

At each handover both sides create or acknowledge a compact custody event. Some events are intentionally delayed because groups are disconnected. One relay later carries the missing chain segment.

At the end, the class checks whether all replicas agree on the current custodian and whether every gap/conflict is explicit rather than silently overwritten.

This can be combined with a harmless shock/temperature sensor so that condition evidence is linked by hash without transmitting the complete sensor log over LoRa.

## Privacy / security

Custody data can reveal movements and identities.

- use synthetic/pseudonymous participants during teaching experiments;
- store coarse locations or named checkpoints, not continuous GPS traces;
- separate public asset status from private custodian identity;
- sign handover events and protect private identity mappings;
- never treat mere possession of a relay message as proof of physical possession;
- use close-range confirmation where the experiment requires stronger physical binding;
- append conflicts instead of overwriting contradictory evidence;
- do not use the prototype for regulated/high-value/safety-critical chain-of-custody claims without independent validation.

## Difficulty

**Medium.** The event model is simple and the hardware can be harmless. The interesting work is conflict handling, physical/digital binding and delayed convergence.

## Research / standards signal

GS1 EPCIS is a mature visibility-event standard designed to capture what happened to products/assets, including status, movement and chain of custody; EPCIS 2.0 also supports sensor data. That makes event-based physical custody a concrete interoperable domain to study without requiring PollicinoNet to adopt the whole standard in its core.

References:

- https://www.gs1.org/standards/epcis
- https://support.gs1.org/support/solutions/articles/43000755325-what-is-electronic-product-code-information-services-epcis-
