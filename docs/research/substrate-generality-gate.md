# PollicinoNet Independent Consumer Generality Gate

Status: ACTIVE / CROSS-PROJECT ARCHITECTURE GATE, 2026-08-31

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

## Current FARO checkpoint

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

It also kept distributed catalog, asynchronous query/result, prefetch, equivocation gossip and diversity replication behind future gates, and deferred BitTorrent/Mainline-DHT/BEP44/BEP46 execution.

This is evidence for the generality direction, not a promotion of research-only PR #52 APIs to stable status.

## Stable-surface rule

External consumers must be told which Pollicino capabilities are:

- stable/main implemented;
- research-branch implemented;
- prototype implemented;
- design-only;
- use-case-only.

An external consumer must not unknowingly depend on research-only APIs.

Current FARO integration should prefer the pinned Pollicino main exact-content surface before using persistence/DTN/custody/bearer functionality from PR #52.

## Generic catalog gate

A generic bounded reference catalog becomes justified only if measurements show common behavior across at least two consumers.

Current independent pressure:

- `UC-CONTENT-002`: discover authorized content references without pushing lifetime catalogs;
- `UC-FARO-001`: discover scientific-package references without embedding FARO science in Pollicino.

Candidate common behavior:

- bounded reference IDs;
- TTL/expiry;
- byte/item quota;
- duplicate suppression;
- simple set reconciliation;
- pull only selected references.

Application-specific metadata remains opaque/application-owned unless genuine commonality is demonstrated.

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

DNA plus FARO provide two materially different consumers and therefore justify explicit generality testing of PollicinoNet's exact-content, reference, catalog, query and future distributed-storage boundaries.

Do not yet promote experimental catalog/DTN/security/P2P surfaces merely because FARO needs them. The next evidence should come from FARO PX1 exact-content integration and subsequent bounded-catalog experiments.
