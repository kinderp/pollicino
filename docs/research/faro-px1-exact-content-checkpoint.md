# FARO PX1 exact-content cross-project checkpoint

Status: PASS / CROSS-PROJECT CONFORMANCE EVIDENCE, 2026-09-01

## Result

FARO gate `PX1 — FAROPackage over Pollicino Exact Content Vertical Slice` concluded:

```text
CLASSIFICATION: FAROPACKAGE_POLLICINO_EXACT_CONTENT_READY
CONFIDENCE: HIGH
```

FARO state:

```text
FARO_BASE: 885fe1d5061e8e5fddead6ab98c795c273bb3e39
IMPLEMENTATION_COMMIT: 99d188d30f9f4cbcebe927a3b2ecaf4445d0d3e1
FINAL_CLOSURE_COMMIT: e2ad5e2c44e05112b212b18c91d67df184999795
```

Pollicino source used by the external consumer:

```text
POLLICINO_HEAD: 750405a4aba86e7335141383396edf84347fc1d8
SURFACE: main
PR_52_RUNTIME_DEPENDENCY: NONE
```

Validation reported by FARO PX1:

```text
FARO_TESTS: 436 PASS
PX1_FOCUSED: 28 PASS
POLLICINO_RELEVANT: 29 PASS
POLLICINO_ROOT: 125 PASS / 2 SKIP
BENCHMARK: NOT_RUN_BY_DESIGN
RUNTIME_NETWORK: NOT_USED_BY_DESIGN
```

The two Pollicino root-suite skips were optional Torch modules not installed and unrelated to the exact-content path. FARO also recorded that indiscriminate collection of `course/` exercises produced context errors and did not classify those educational exercises as the declared Pollicino root suite.

## What PX1 proves at this scope

A canonical FAROPackage can traverse the pinned Pollicino main exact-content surface while preserving the application-owned FARO semantics.

Validated path:

```text
canonical FAROPackage bytes
        |
        v
FARO-side optional Pollicino adapter
        |
        v
DiscoveryDescriptor / ContentManifest / RetrievalSource
resolver / provider
PCM1 / PNA1 / PollicinoStore
partial-cache synchronization
exact reconstruction
        |
        v
byte-identical FAROPackage
        |
        v
FARO independently verifies semantics
```

PX1 used these stable-main primitives:

- `DiscoveryDescriptor`;
- `ContentManifest`;
- `RetrievalSource`;
- `InMemoryResolver`;
- `InMemoryContentProvider`;
- `retrieve_exact`;
- `build_chunk_manifest`;
- `PollicinoStore`;
- `reconstruct_from_store`;
- `sync_missing_chunks`.

No Pollicino implementation code was copied into FARO.

## Identity boundary

PX1 directly validated the two-identity model:

```text
FARO package identity
    != Pollicino transport identity
```

Changing the Pollicino chunk size may change the PCM1 manifest fingerprint / transport layout while the FARO package ID and canonical digest remain unchanged.

Therefore Pollicino transport identity is not promoted into application/scientific identity.

## Semantic non-escalation

PX1 validated that exact Pollicino transport does not upgrade FARO semantics.

The following remained unchanged after store/retrieval/reconstruction:

- canonical package bytes;
- FARO package ID;
- canonical FARO digest;
- signatures;
- publisher/scientific origin;
- evidence grade;
- real versus synthetic classification;
- trust state;
- `validated_here`;
- Recommendation authority.

In particular:

```text
Pollicino transport PASS
    != FARO signature PASS
    != publisher trusted
    != evidence scientifically valid
    != locally validated
    != recommended
```

A mathematically valid Pollicino content transfer containing a FARO package with an invalid FARO signature was explicitly represented as transport success plus `FARO_SIGNATURE_FAILURE`.

## FARO evidence fixtures

PX1 preserved the established FARO semantics of the principal fixtures.

### AUTO

Receiver-side state remained:

```text
validated_at_origin = true
validated_here = false
```

AUTO was not promoted to best, optimal or winner.

### CACHE256

The E3 LIMIT state survived unchanged:

```text
paired throughput: +3.5475%
requested reads: +105.283%
physical device loads: NOT_AVAILABLE
storage-read guardrail: failed
classification: E3 LIMIT
```

Successful distribution did not reinterpret the result as positive scientific evidence.

### Synthetic fixture

The fixture remained `SYNTHETIC_TEST` after exact transport.

### Unknown / blocked / revoked publisher

Unknown publisher state remained unknown/advisory. Blocked or revoked publisher bytes may still be transported exactly, but FARO remains authoritative for denying decision authority.

## Provider and corruption behavior

PX1 exercised multiple local providers.

Observed properties:

- corrupt provider rejected;
- fallback to a later valid provider succeeds;
- corrupt chunk/store state fails reconstruction verification;
- package B returned for a reference to package A is rejected;
- two valid providers serving the same package reconstruct identical bytes;
- provider count does not increase scientific confidence;
- provider ordering is operational, not scientific ranking.

Mandatory interpretation:

```text
10 distribution sources
    != 10 independent scientific replications
```

## Partial cache / PNA1

The receiver-side partial-cache vertical slice used stable `sync_missing_chunks` / PNA1 behavior.

Reported PX1 fixture behavior:

```text
first synchronization: 38 missing chunks
second synchronization: 0 missing chunks
```

Availability and cache-hit state remain transport/operational state and do not enter FARO scientific evidence.

## Application-state immutability

Pollicino fetch/reconstruct operations did not mutate:

- FARO `LocalKnowledgeStore`;
- FARO `LocalTrustStore`;
- Recommendation state.

FARO knowledge changes only through its explicit normal import operation.

No auto-import, auto-trust or auto-recommend path was introduced.

## FAROPollicinoReference checkpoint

PX1 froze the bounded application-owned reference as:

```text
schema: faro.pollicino-reference.v0
max encoded size: 4096 bytes
max retrieval hints: 8
```

The reference is deterministic/canonical and privacy-minimized. It does not contain a complete MachineProfile, local filesystem paths, `LocalTrustStore` state or Recommendation state.

A reference is discovery/retrieval metadata, not authoritative FARO science.

## Stable-surface interpretation

PX1 is stronger evidence than the earlier architecture-only convergence gate because a real external consumer exercised the pinned Pollicino main surface and independently ran relevant/root tests.

The correct status is therefore:

```text
current main exact-content/store/resolver/provider surface
= EXTERNALLY_EXERCISED_AT_PINNED_COMMIT
```

This does **not** yet mean:

```text
all current symbols = versioned stable public API
```

A separate Pollicino API/stability contract is still required before making long-term compatibility guarantees.

Research-only PR #52 persistence, custody, store-forward, node-runtime and bearer-runtime surfaces remain outside this PX1 claim.

## Generality implication

PX1 supports the Independent Consumer Generality Gate.

FARO can use generic Pollicino exact-content primitives without adding FARO-specific branches to Pollicino core. DNA and FARO remain materially different consumers, which strengthens the evidence that exact-content/store/provider behavior belongs in the shared substrate.

## Next cross-project question

PX1 closes the first exact-content integration question.

The next justified FARO gate is:

```text
PX2 — FARO Bounded Reference Catalog over Pollicino
```

This should use `UC-CONTENT-002` plus `UC-FARO-001` as independent application pressure and ask whether a genuinely generic bounded-reference/catalog primitive is justified.

Start with the simplest baselines:

1. explicit bounded reference lists;
2. deterministic short-ID ordering;
3. receiver-known-ID comparison;
4. pull only selected/new references;
5. simple exact reconciliation;
6. only introduce sketches or new wire formats if measured evidence requires them.

PX2 must not turn Pollicino into a FARO query engine.

## Still deferred / blocked

PX1 does not authorize:

- production distributed catalog;
- public FARO network;
- PR #52 DTN/custody/bearer use as stable external API;
- BitTorrent execution;
- Mainline DHT execution;
- BEP44 execution;
- BEP46 execution;
- automatic FARO import/trust/recommendation.

Serverless Internet distribution remains a later design gate after the immutable exact-content and bounded-catalog layers are established.
