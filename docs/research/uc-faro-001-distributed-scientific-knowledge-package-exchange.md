# UC-FARO-001 — Distributed scientific knowledge package exchange

Status: PRIMARY / CROSS-PROJECT CONFORMANCE / SOFTWARE-FIRST

## Summary

FARO produces, imports and evaluates signed scientific knowledge packages. PollicinoNet is a candidate substrate for preserving, storing, locating, caching, reconciling and eventually distributing the exact package bytes without interpreting FARO's scientific semantics.

The central requirement is deliberately narrow:

> PollicinoNet may prove that the exact bytes requested by an application were preserved or reconstructed, but it must not decide whether a FARO publisher is trusted, whether an evidence claim is scientifically valid, whether it applies to the local machine, whether it was locally validated, or what FARO should recommend.

This use case is valuable to PollicinoNet because FARO is materially different from the existing DNA/Travel consumer. If the same Pollicino primitives can serve both without application-specific branches in the network core, that is evidence that PollicinoNet is becoming a genuinely transport- and application-independent substrate rather than a LoRa/DNA-specific stack.

## Cross-project evidence checkpoint

FARO gate `RG2-PX0 — FARO × PollicinoNet Distributed Registry Convergence` concluded:

```text
POLLICINO_SUBSTRATE_REUSE_READY_WITH_BOUNDARIES
confidence: HIGH
```

The checkpoint used FARO base `2401ba7ad6a637aaa3b962cb78917ab73ff27e5d`, final FARO closure `885fe1d5061e8e5fddead6ab98c795c273bb3e39`, Pollicino main `750405a4aba86e7335141383396edf84347fc1d8`, and separately inspected the research-only PR #52 head `bc8e088a183ab008e48f8f356387ede40f9f593e`.

PX0 established, at its stated local/offline scope, that:

- FARO should not build a parallel P2P/DTN/cache substrate;
- current Pollicino exact-content/store/resolver/provider primitives are strong reuse candidates;
- FARO package identity remains distinct from Pollicino transport identity;
- exact transport does not upgrade FARO trust;
- exact transport does not upgrade evidence grade;
- exact transport does not set `validated_here`;
- DNA is not required for FARO integration;
- BitTorrent, Mainline DHT, BEP44 and BEP46 remain future adapter/design work;
- persistent DTN/custody/bearer surfaces observed in PR #52 remain experimental rather than stable external API.

PX0 is cross-project evidence, not proof that every future Pollicino networking feature is ready for FARO.

The next FARO-side validation is `PX1 — FAROPackage over Pollicino Exact Content Vertical Slice`.

## Actor / nodes

A minimal software scenario has:

- a FARO publisher or local FARO node that owns canonical `FAROPackage` bytes;
- one or more Pollicino content stores/providers;
- a receiving FARO node;
- an optional intermediary peer or cache;
- later, only after separate gates, DTN relays or Internet P2P providers.

No LoRa hardware is required for the first integration.

## Situation

A FARO node knows that a scientific package exists and wants to obtain the exact package bytes from one of several possible sources.

Possible future sources include:

- local cache;
- another peer;
- NAS/HDD;
- Wi-Fi/LAN provider;
- HTTP/static mirror;
- BitTorrent swarm;
- another content-addressed distribution system.

Pollicino should represent these as generic retrieval/provider concerns. The FARO package must not be redefined around any one transport.

## Problem

Without a shared substrate, FARO would be tempted to implement its own:

- content-addressed cache;
- provider abstraction;
- partial-object reconciliation;
- restartable storage;
- peer distribution;
- DTN/store-carry-forward;
- bearer handover;
- future Internet P2P layer.

That would duplicate a large part of PollicinoNet and create two independent implementations of the same distribution problems.

The opposite mistake is also dangerous: moving FARO-specific scientific semantics into Pollicino would couple the substrate to one application and blur trust boundaries.

The use case therefore tests a strict adapter boundary.

## Responsibility split

### FARO remains authoritative for

- canonical `FAROPackage` bytes and package identity;
- FARO package schema/version;
- publisher signatures and publisher identity;
- scientific provenance;
- evidence types and grades;
- real versus synthetic evidence classification;
- trust and revocation policy;
- compatibility and applicability;
- evidence conflicts;
- local validation state;
- `validated_at_origin` versus `validated_here`;
- Recommendation and validation planning;
- FARO-specific query semantics.

### PollicinoNet may own

- exact byte preservation and reconstruction;
- content addressing at the transport/store layer;
- content manifests and chunk identities;
- provider/resolver abstraction;
- local cache/store;
- availability and missing-state reconciliation;
- duplicate suppression;
- bounded relay storage policy;
- future store-carry-forward and custody;
- future bearer/runtime transport selection;
- future external P2P adapters.

### PollicinoNet must not infer

```text
FARO package transported exactly
    != publisher trusted
    != evidence scientifically valid
    != evidence applicable here
    != locally validated
    != recommended
```

Likewise:

```text
10 peers serving one FAROPackage
    = 10 distribution sources
    != 10 independent scientific replications
```

## Identity boundary

FARO and Pollicino intentionally have different identities for different purposes.

```text
FARO package identity
        |
        | application/scientific identity
        v
canonical FAROPackage bytes
        |
        v
Pollicino exact object
        |
        +-- object/content hash
        +-- manifest identity
        +-- chunk hashes
```

Changing Pollicino chunk size or transport representation may change a Pollicino manifest identity. It must not change the FARO package identity if the canonical FAROPackage bytes are unchanged.

Pollicino transport identity must never overwrite FARO package identity.

## Minimal flow

```text
FARO publisher
    |
    | canonical signed FAROPackage bytes
    v
FARO -> Pollicino adapter
    |
    v
Pollicino exact content / store / manifest
    |
    +--> local provider A
    +--> local provider B
    +--> future remote provider
    |
    v
exact reconstruction
    |
    v
same FAROPackage bytes
    |
    v
FARO independently verifies
    |
    +-- package identity
    +-- signature
    +-- publisher/trust
    +-- evidence semantics
    +-- applicability
    +-- local validation state
    +-- Recommendation policy
```

## Simplest baselines

Compare in order:

1. FARO reads a package directly from a local file/store;
2. FARO stores/reconstructs the same bytes through the stable Pollicino exact-content primitives;
3. FARO retrieves through one generic Pollicino provider;
4. FARO retrieves with multi-provider fallback;
5. FARO reuses partial verified content through PNA1/PCM1 where appropriate;
6. only later, after independent gates, compare persistent DTN and Internet P2P paths.

Do not implement a network merely to prove the adapter.

## Measurable hypotheses

H1. Canonical FAROPackage bytes survive Pollicino exact storage/reconstruction byte-for-byte.

H2. FARO package identity, signatures, scientific provenance, evidence grade and local-validation state are unchanged by Pollicino transport.

H3. A bounded application-owned reference plus generic Pollicino provider/resolver primitives is sufficient for local multi-provider retrieval without teaching Pollicino FARO semantics.

H4. Partial-cache reconciliation can reduce retransmitted transport bytes while leaving FARO scientific semantics unchanged.

H5. The same stable Pollicino primitive surface can support both FARO and non-FARO applications, providing evidence for substrate generality.

## Metrics

Track separately:

- original and reconstructed byte equality;
- FARO package ID equality;
- FARO canonical digest equality;
- Pollicino manifest/content identities;
- provider attempts and failures;
- cached/missing chunk counts where PNA1/PCM1 are exercised;
- bytes stored/reused/transferred at the Pollicino layer;
- signature outcome before/after;
- trust state before/after;
- evidence grade before/after;
- `validated_here` before/after;
- LocalKnowledgeStore mutation count;
- LocalTrustStore mutation count;
- privacy exposure of the bounded reference;
- dependency/stability class of every Pollicino primitive used.

Distribution metrics must never be reported as scientific corroboration metrics.

## Adversarial cases

The integration should eventually cover at least:

1. Pollicino content integrity passes but FARO signature fails;
2. FARO signature is valid but publisher trust is unknown;
3. trusted publisher package is incompatible locally;
4. same package is served by multiple providers;
5. provider disappears after discovery;
6. reference survives while payload is unavailable;
7. wrong FARO package is returned for a requested reference;
8. package is cached before publisher revocation;
9. duplicated package is delivered repeatedly;
10. synthetic evidence is replicated widely;
11. transport peer differs from scientific publisher;
12. future split-view/equivocation state is observed across distributed catalogs.

The network layer must fail closed on transport/content mismatch. FARO still performs its own package/authenticity/trust checks afterwards.

## Privacy and security

A future FARO reference/catalog entry must be bounded and privacy-minimized.

It should not expose by default:

- local filesystem paths;
- usernames or hostnames;
- private keys;
- LocalTrustStore state;
- LocalKnowledgeStore internals;
- Recommendation state;
- exact device identifiers;
- complete MachineProfile details when coarse discovery hints suffice.

A transport provider may be untrusted. Exact content verification and FARO signature/trust checks remain independent layers.

## Relationship to other Pollicino use cases

### `UC-CONTENT-001`

CONTENT transports arbitrary authorized references/manifests/chunks. FARO supplies a concrete scientific-package consumer with stricter authenticity/science boundaries.

### `UC-CONTENT-002`

CONTENT-002 motivates bounded mobile reference catalogs. FARO gives a second independent reason to study a generic bounded reference-catalog primitive, but only after FARO PX1 proves the exact-content adapter.

### `UC-QUERY-001`

A future FARO search such as `M4 Max / Metal / SSD streaming / model family` could be carried as an application-owned bounded query and return compact references. Pollicino should not understand the FARO query semantics.

### `UC-TRUST-001`

FARO has real publisher rotation/revocation semantics. A future experiment may carry FARO-signed revocation/security-state objects through Pollicino, while FARO remains authoritative for their meaning.

### `UC-WITNESS-001`

FARO registry/index split-view detection provides a concrete future transparency-gossip fixture. Pollicino may carry signed checkpoints; it must not become the scientific/trust authority.

### `UC-PREFETCH-001`

A future distributed FARO network may pre-position rare/useful packages or references under local storage budgets. Provider count or replica count must never increase scientific evidence grade.

## Relationship to DNA

DNA is not required for this use case.

DNA may remain an independent Pollicino consumer. If FARO and DNA later need a genuinely common subscription/filter primitive, that abstraction must pass the normal architecture gate rather than creating a FARO -> DNA dependency.

## Internet distribution boundary

This use case does not authorize BitTorrent, Mainline DHT, IPFS, BEP44 or BEP46 implementation.

A later gate may compare existing systems as external adapters for serverless Internet distribution. The default preference is to adapt an established external distribution system rather than invent a Pollicino-specific global DHT.

Potential future roles to test include:

```text
BitTorrent       -> immutable package/shard distribution
Mainline DHT     -> provider/rendezvous discovery
BEP44            -> small signed mutable publisher/catalog head
BEP46            -> mutable pointer to current torrent/catalog generation
HTTP/static      -> simple baseline/mirror
IPFS             -> alternative content-addressed provider baseline
```

These are hypotheses, not adopted architecture.

## Stable versus research Pollicino surface

The current cross-project plan deliberately distinguishes:

- stable/main exact-content primitives suitable for immediate pin-and-test integration;
- research-only persistence/DTN/custody/bearer primitives currently developed in PR #52;
- design/use-case-only catalog/query/security extensions.

FARO must not make experimental PR #52 APIs a hidden mandatory dependency merely to complete the first exact-content vertical slice.

## Minimal experiment sequence

### FARO-PN-001 — Exact package round trip

Canonical FAROPackage bytes -> Pollicino store/manifest -> reconstruction -> FARO verification.

### FARO-PN-002 — Multiple local providers

One missing/corrupt source followed by a valid source; verify exact fallback without trust escalation.

### FARO-PN-003 — Partial cache

Receiver begins with a subset of verified chunks; use existing reconciliation primitives and reconstruct exactly.

### FARO-PN-004 — Bounded reference

Define the minimum application-owned reference needed to locate the package without copying full scientific evidence into Pollicino discovery metadata.

### FARO-PN-005 — Distributed catalog

Only after PX1/exact-content success, study bounded catalog exchange using `UC-CONTENT-002` as the existing baseline.

### FARO-PN-006 — Serverless Internet adapter study

Only after the local/distributed catalog model is justified, compare existing external P2P/distribution systems.

## Success criterion

Continue integration when:

- canonical package identity survives exact Pollicino storage/reconstruction;
- trust/evidence/local-validation state never escalates because of transport;
- the adapter remains application-side;
- no FARO semantic branch is required inside Pollicino core;
- stable Pollicino primitives provide material reuse versus a FARO-specific implementation.

## Kill/defer criteria

Defer or narrow the integration if:

- Pollicino requires understanding FARO scientific semantics;
- FARO package identity must be replaced by Pollicino identity;
- large amounts of Pollicino code would need copying into FARO;
- only unstable research APIs can satisfy the first exact-content use case;
- transport metadata creates unacceptable privacy exposure;
- simple local/static distribution is sufficient and a more complex P2P layer has no measured value.

## Gate decision

**PRIMARY / CROSS-PROJECT CONFORMANCE / SOFTWARE-FIRST.**

The existing PX0 evidence justifies treating FARO as an independent PollicinoNet consumer and using it to pressure-test substrate generality. It does not authorize production distributed networking, automatic trust/import/recommendation, BitTorrent/DHT implementation or promotion of PR #52 APIs to stable status.
