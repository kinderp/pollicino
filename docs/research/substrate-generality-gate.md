# PollicinoNet Independent Consumer Generality Gate

Status: ACTIVE / CROSS-PROJECT ARCHITECTURE GATE, updated 2026-09-01

## Purpose

PollicinoNet is intended to become a transport- and application-independent information substrate, not a collection of domain-specific shortcuts hidden behind generic names.

The generality gate asks:

> Can materially different applications reuse the same Pollicino primitives without moving their domain semantics into the Pollicino core?

This gate extends the existing `Use-Case Justification Gate` with a stricter rule for reusable cross-application abstractions.

## Current independent consumers

### DNA / Travel DNA

DNA exercises:

- temporary discovery objects;
- intent/domain filtering;
- consent/application authorization;
- micro-information;
- privacy-sensitive identities and subscriptions;
- school-mixing and carried-node workflows.

### FARO

FARO exercises:

- immutable signed scientific packages;
- application-owned canonical package identity;
- publisher authenticity and revocation;
- scientific evidence grades;
- local applicability and validation;
- distributed references/catalog discovery;
- exact package replication without scientific trust escalation.

These consumers are materially different enough that common requirements between them are meaningful evidence for a substrate abstraction.

## Core rule

The application depends on the substrate.

The substrate does not depend on the application.

Conceptually:

```text
DNA -----------\
                \
FARO ------------> application adapters -> PollicinoNet generic contracts
                /
Raiatea --------/
```

A feature must not enter Pollicino core merely because one application needs it.

## Architecture promotion rule

A reusable Pollicino abstraction should normally require at least two materially different consumers/use cases that need the same behavior.

Examples:

- exact content/store/provider is already generic and independently useful;
- bounded reference catalog becomes more justified when both `UC-CONTENT-002` and `UC-FARO-001` need it;
- asynchronous query/result transport becomes more justified when both `UC-QUERY-001` and FARO distributed discovery need it;
- generic subscription semantics should not be extracted solely from DNA until another consumer needs the same semantics;
- FARO scientific trust/evidence semantics remain in FARO because they are not generic transport concerns.

One strong standards/interoperability/security constraint may still justify a general abstraction under the existing Use-Case Justification Gate.

## Fail conditions

The generality gate fails if Pollicino core starts containing application-specific logic such as:

```text
if application == "faro": ...
if package_type == "faro": ...
if evidence_grade == "E3": ...
if dna_domain == ...: ...
```

Equivalent hidden coupling through schemas, magic labels or routing policy also fails the gate.

Application adapters may of course contain application semantics.

## Ownership test

For every proposed shared feature answer:

1. Who owns the meaning of the object?
2. Who owns exact byte/content identity?
3. Who owns application authenticity?
4. Who owns trust?
5. Who owns authorization?
6. Who owns discovery metadata?
7. Who owns retention policy?
8. Who owns transport/provider selection?
9. Can Pollicino process the object without parsing application semantics?
10. Can another independent application reuse the same primitive?

If questions 9 or 10 fail, keep the feature in an application adapter unless another external constraint justifies generalization.

## Identity rule

Applications may have authoritative identities that are distinct from Pollicino transport identities.

Example FARO:

```text
FARO package ID
    != Pollicino manifest fingerprint
```

Pollicino may use hashes/manifests/chunk IDs to prove exact transport/reconstruction. It must not replace an application's canonical identity unless that application explicitly defines Pollicino identity as authoritative.

## Trust rule

Transport integrity is not application trust.

```text
exact Pollicino object
    != trusted FARO publisher
    != authorized DNA fragment
    != scientifically valid claim
```

Likewise custody, replica count, provider count or cache availability must not be interpreted as stronger application evidence unless the application explicitly evaluates independent provenance itself.

## FARO cross-project checkpoints

### RG2-PX0 — architecture/convergence

FARO `RG2-PX0` classified the integration direction as:

```text
POLLICINO_SUBSTRATE_REUSE_READY_WITH_BOUNDARIES
confidence: HIGH
```

The checkpoint found direct reuse candidates in current Pollicino main for:

- `PollicinoStore`;
- `ManifestResolver`;
- `ContentProvider`;
- `RetrievalSource`;
- PNA1 availability;
- exact reconstruction.

It identified thin application-side adapters for FAROPackage bytes, provider references, content cache and a bounded FARO reference.

It kept FARO ownership of package identity, signatures, evidence, trust, applicability, local validation and Recommendation.

### PX1 — executable exact-content conformance

FARO `PX1 — FAROPackage over Pollicino Exact Content Vertical Slice` concluded:

```text
FAROPACKAGE_POLLICINO_EXACT_CONTENT_READY
confidence: HIGH
```

PX1 used Pollicino main pinned at:

```text
750405a4aba86e7335141383396edf84347fc1d8
```

and reported:

```text
POLLICINO_RELEVANT: 29 PASS
POLLICINO_ROOT: 125 PASS / 2 SKIP
FARO_TESTS: 436 PASS
PX1_FOCUSED: 28 PASS
```

The external consumer exercised `DiscoveryDescriptor`, `ContentManifest`, `RetrievalSource`, resolver/provider, `PollicinoStore`, PCM1/PNA1 partial-cache synchronization and exact reconstruction without depending on PR #52.

PX1 directly demonstrated that:

- canonical FAROPackage bytes round-trip exactly;
- FARO package ID/digest remain unchanged;
- different Pollicino chunk layouts may change PCM1 transport identity without changing FARO package identity;
- signatures and scientific origin remain application-owned;
- unknown trust remains unknown/advisory;
- blocked/revoked authority remains blocked by FARO policy;
- `validated_here` does not change;
- synthetic evidence remains synthetic;
- E3 LIMIT evidence remains LIMIT;
- provider count/cache hits do not become scientific corroboration;
- fetch/reconstruction do not mutate FARO LocalKnowledgeStore, LocalTrustStore or Recommendation.

See `faro-px1-exact-content-checkpoint.md` for the detailed cross-project record.

This is now evidence that the pinned current-main exact-content/store/resolver/provider surface is **externally exercised by a materially independent consumer**.

It is still not a promise that every current symbol is a versioned stable public API.

## Current exact-content decision

For the specific exact-content/store/resolver/provider behavior exercised by PX1:

```text
GENERIC_REUSE_PROVEN_AT_PINNED_MAIN_SCOPE
```

Long-term API compatibility remains:

```text
STABILIZATION_REQUIRED
```

Research-only PR #52 persistence/DTN/custody/bearer surfaces remain outside this decision.

## Stable-surface rule

External consumers must be told which Pollicino capabilities are:

- stable/main implemented;
- externally exercised at a pinned main commit;
- research-branch implemented;
- prototype implemented;
- design-only;
- use-case-only.

An external consumer must not unknowingly depend on research-only APIs.

Current FARO integration should continue to prefer the pinned Pollicino main exact-content surface before using persistence/DTN/custody/bearer functionality from PR #52.

## Generic catalog gate

PX1 satisfies the prerequisite that `UC-FARO-001` can obtain the exact package behind a reference without changing FARO semantics.

The next commonality question is now active:

> Can `UC-CONTENT-002` and `UC-FARO-001` share a genuinely generic bounded reference-catalog primitive without moving application metadata/query semantics into Pollicino core?

Current independent pressure:

- `UC-CONTENT-002`: discover authorized content references without pushing lifetime catalogs;
- `UC-FARO-001`: discover scientific-package references without embedding FARO science in Pollicino.

Candidate common behavior:

- bounded reference IDs;
- deterministic canonical representation;
- TTL/expiry where required;
- byte/item quota;
- duplicate suppression;
- receiver-known-ID comparison;
- simple exact set reconciliation;
- pull only selected/new references.

Application-specific metadata remains opaque/application-owned unless genuine commonality is demonstrated.

### Required baseline order

Before a new generic catalog protocol or sketch is adopted, compare:

1. explicit bounded reference list;
2. deterministic sorted IDs;
3. receiver-known-ID list/comparison;
4. explicit pull of selected references;
5. simplest exact reconciliation;
6. only then compressed summaries/sketches if measured need remains.

A FARO-only catalog implementation must remain in FARO unless the cross-consumer experiment proves common behavior.

## Generic query gate

Similarly, Pollicino should transport a bounded asynchronous query/result envelope without becoming a universal search-language engine.

Preferred initial boundary:

```text
application query payload
        |
        v
Pollicino bounded transport/governance envelope
        |
        v
application/provider executes semantics
        |
        v
bounded application result references
```

FARO hardware/model filters remain FARO semantics. Raiatea full-text/vector semantics remain Raiatea semantics.

This is not yet the next implementation gate; bounded references/catalog come first.

## Security-state and witness gate

`UC-TRUST-001` and `UC-WITNESS-001` may provide generic transport for signed security/checkpoint objects.

FARO supplies concrete future fixtures for:

- publisher-key rotation/revocation;
- stale trust generations;
- registry/index equivocation;
- signed checkpoint gossip.

Pollicino may carry and reconcile these exact objects. The application/security authority remains responsible for interpreting them.

## Serverless Internet gate

FARO introduces a strong future requirement for distribution without mandatory owner-funded infrastructure.

This justifies a design/benchmark gate, not immediate adoption.

Compare established systems first:

- static HTTP/object mirrors;
- BitTorrent;
- Mainline DHT;
- IPFS or another content-addressed provider;
- hybrid mirror + P2P arrangements.

Potential BEP44/BEP46 use for tiny mutable catalog/publisher heads should be evaluated only after the immutable content/catalog model is stable.

Do not invent a proprietary Pollicino global DHT unless existing systems fail a measured requirement.

## Decision states

For each candidate shared abstraction use:

- `GENERIC_REUSE_PROVEN`
- `GENERIC_REUSE_PROVISIONAL`
- `APPLICATION_ADAPTER_ONLY`
- `SECOND_CONSUMER_REQUIRED`
- `STABILIZATION_REQUIRED`
- `DEFER`
- `REJECT`

## Current decision

**ACTIVE / CONTINUE.**

The exact-content/store/provider boundary has now passed a real cross-project executable conformance checkpoint through FARO PX1 at a pinned Pollicino main commit.

The next justified generality experiment is the bounded-reference/catalog boundary using `UC-CONTENT-002` and `UC-FARO-001` as independent consumers.

Do not yet promote a new catalog wire format, PR #52 DTN APIs, security-distribution machinery, BitTorrent/DHT/BEP44/BEP46 execution, or application-specific query semantics into Pollicino core merely because FARO needs them.
