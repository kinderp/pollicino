# UC-RAIATEA-001 — Raiatea offline document discovery and manifest synchronization

Status: INTEGRATION USE CASE / PROTOTYPE

## Problem

Raiatea is evolving toward a provenance-aware Universal Document & Asset Library, but a document library may be used across devices and places that are not continuously connected.

The PollicinoNet use case is **not** to push entire PDFs/books over LoRa. It is to carry the minimum exact information needed to discover, compare, request and later obtain authorized Raiatea documents/assets:

- document/asset identity;
- version/fingerprint;
- source/provenance reference;
- Processing Rights / sharing eligibility summary where appropriate;
- manifest/chunk inventory;
- wanted state;
- transformation/output availability;
- provider/rendezvous hint.

Later, Wi-Fi/Internet/local NAS can transfer the actual document or missing chunks.

## Actors / nodes

- Raiatea library on a home/server machine;
- student laptop/portable companion;
- school lab/library node;
- trusted peer relay;
- optional Internet or local-NAS provider.

## Example educational scenario

A student discovers at school that another authorized Raiatea library has a useful document, translated derivative or extracted text version. The portable node carries only the manifest/reference home. The home Raiatea instance then:

```text
reference / manifest arrives
          |
          v
check local holdings
          |
          +-- already present -> no payload
          +-- partial version -> fetch only missing chunks/output
          +-- absent -> retrieve later from authorized provider
```

The reverse path can carry a wanted-list or availability summary back to school the next day.

## Why PollicinoNet fits

This is a strong fit with PollicinoNet's original principle: do not transmit a document when a coordinate, manifest or delta is sufficient to obtain/reconstruct it later.

It also creates useful cross-project boundaries:

```text
Raiatea
- document meaning
- source/provenance
- Processing Rights
- transformation lineage
- authorization

PollicinoNet
- compact reference
- exact identity
- availability reconciliation
- cache/chunks
- store-carry-forward
- bearer handover
```

PollicinoNet must not override Raiatea Processing Rights. A technically transferable object may still be forbidden from peer redistribution.

## Possible bearers

- LoRa for compact discovery/reference/wanted state;
- BLE for close-range library/node rendezvous;
- Wi-Fi/Wi-Fi Direct for documents and chunks;
- Internet for provider retrieval;
- physical movement for delayed manifest/wanted-list carry.

## What can be tested now in software

Raiatea is still in bounded P0 Elaboration, so the first integration should use **rights-safe synthetic fixtures**, not assume a general document library implementation already exists.

Immediately testable:

1. synthetic document manifests with provenance and rights classifications;
2. two libraries with overlapping versions/chunks;
3. wanted-list exchange;
4. exact reconciliation of existing versus missing content;
5. reference-only carry followed by simulated home retrieval;
6. rights-policy rejection when an object is locally readable but not redistributable;
7. version/delta scenarios where only a derived output changed.

## What requires real hardware

Hardware is not needed to validate the cross-project contracts. It is needed before claiming:

- how many references/manifests fit into a real LoRa encounter;
- field usefulness of LoRa discovery;
- physical student-network delivery latency;
- real handover rates between LoRa and Wi-Fi/home infrastructure.

The frozen PHY remains untouched.

## Privacy / security

Document metadata can itself be sensitive.

Requirements:

- do not broadcast private filenames/titles by default;
- use scoped/rotating references for sensitive holdings;
- preserve Raiatea provenance and Processing Rights decisions end-to-end;
- exact hashes/manifests for reconstruction;
- authorization before payload retrieval;
- no assumption that relay possession implies reading permission;
- retention/expiry for wanted lists and private availability advertisements.

## Implementation difficulty

**Medium.** The networking side largely reuses UC-CONTENT-001. The main difficulty is designing a small, stable bridge contract that does not couple PollicinoNet to unfinished Raiatea internal models.

## Minimal measurable hypotheses

- H1: reference/manifest carry avoids transmitting complete documents on scarce links in most workloads where a rich provider becomes available later.
- H2: reconciliation avoids re-fetching document chunks/derivatives already held by the receiver.
- H3: rights-aware filtering can prevent technically possible but unauthorized peer transfer without breaking discovery of permitted material.

## Metrics

- references successfully resolved;
- complete documents avoided on scarce link;
- missing chunks versus already-known chunks;
- scarce-link bytes per eventually retrieved document;
- exact hash verification;
- rights-policy rejection count;
- stale/wrong-version requests;
- rich-link handover success.

## Gate decision

**PROTOTYPE / integration contract only.** This is a concrete consumer of existing PollicinoNet capabilities, but it should not drive new Raiatea or Pollicino core schemas until Raiatea P0 contracts and rights gates are sufficiently stable.

## Raiatea state checked for this use case

The current Raiatea README states that the project is in **Elaboration — P0 risk reduction and architecture**, with source taxonomy, Processing Rights, rights-safe fixtures and provider-neutral contract exploration authorized; the Universal Document & Asset Library is not yet a general implementation. This use case therefore stays fixture/contract driven rather than pretending the final library already exists.