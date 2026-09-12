# Use-Case Justification Gate

Status: project governance rule, 2026-08-25

## Rule

Pollicino/PollicinoNet does not promote a new feature, routing algorithm, protocol, dependency, wire-format extension, persistence model or architectural abstraction into the stable design merely because it is interesting or technically elegant.

Before implementation or architectural adoption, the proposal must pass a **Use-Case Justification Gate**.

The goal is not bureaucracy. The goal is to prevent speculative architecture, unnecessary protocol surface and algorithms that solve no demonstrated problem.

## What needs the gate

The gate is required for:

- new user-visible or network-visible capabilities;
- new routing/scheduling/reconciliation algorithms;
- new protocol messages or wire-format versions;
- new persistent state or schema families;
- new external runtime dependencies or network stacks;
- new cryptographic/security mechanisms;
- new bearer abstractions/adapters that change behavior;
- new general architectural layers or cross-cutting abstractions;
- substantial performance optimizations that add complexity.

The gate is **not** required for ordinary bug fixes, security fixes, test coverage, documentation, compatibility repairs, mechanical refactors with unchanged behavior, or removal of dead/unsafe code. Those changes already have an operational justification: correctness, security or maintainability.

Research and literature exploration are also exempt. An idea may live in the research shelf without a use case. The gate applies when the project wants to promote that idea into implemented/stable architecture.

## Feature / algorithm gate

A new feature or algorithm needs at least **one concrete use case**.

The proposal must state:

1. **Actor / node** — who or what needs this?
2. **Situation** — in what network/storage/contact conditions does the problem occur?
3. **Problem** — what fails, costs too much, waits too long or cannot be expressed today?
4. **Current baseline** — what does the simplest existing implementation or established literature baseline do?
5. **Measurable hypothesis** — what improvement do we expect?
6. **Metric** — bytes, delivery probability, latency, storage, CPU, energy proxy, implementation complexity, privacy exposure, etc.
7. **Minimal experiment** — what is the smallest prototype that can falsify the idea?
8. **Success / kill criterion** — what result justifies adoption, and what result makes us reject/defer it?
9. **Complexity cost** — new code, state, wire bytes, dependencies, migration burden and security surface.
10. **Evidence class** — synthetic/model, replay, measured hardware or production evidence.

No use case or no measurable hypothesis means **RESEARCH ONLY / DO NOT IMPLEMENT**.

## Architecture gate

General architecture has a higher bar than a local feature.

A new reusable layer, abstraction or protocol family requires either:

- at least **two materially different use cases** that benefit from the same abstraction; or
- one strong external constraint such as required standards interoperability, security compliance, hardware boundary or unavoidable compatibility requirement.

One use case is normally insufficient evidence for a new general abstraction. Prefer the local implementation until real commonality appears.

For a new wire protocol/version, also answer:

- Why can the existing message/standard not express the use case?
- Is there an existing standard or external implementation we should adapt instead?
- What is the wire-byte cost?
- What is the migration/compatibility story?
- Can the experiment be done out-of-band before changing the frozen protocol?

## Default decision states

Every proposal should end in one of these states:

- **ADOPT** — use case and evidence justify the implementation.
- **PROTOTYPE** — use case exists, but evidence is insufficient; implement only an isolated experiment.
- **RESEARCH ONLY** — interesting idea, no justified implementation yet.
- **DEFER** — valid use case, but not worth current cost/risk or blocked by evidence/hardware.
- **REJECT** — baseline/simple alternative is better or the hypothesis failed.

Rejected/deferred ideas are not deleted from project knowledge. Record why they were not adopted and what evidence could reopen the decision.

## Simplicity rule

The gate must compare the proposed technique with the **simplest plausible solution**, not only with the current implementation.

Examples:

- Before adding IBLT/minisketch for availability reconciliation, compare bitmap, sparse missing-index list and run-length/compressed bitmap.
- Before inventing a new LoRa routing layer, compare raw LoRa plus the existing DTN overlay, LoRaMesher and Reticulum where relevant.
- Before a new routing algorithm, compare established Epidemic, Spray-and-Wait, PRoPHET/RAPID-style baselines.
- Before a new cross-bearer architecture, verify that at least two real bearers/use cases need the abstraction.

A more sophisticated solution is adopted only when its measured benefit justifies its extra complexity.

## Physical-evidence rule

A software use case can justify synthetic experiments, but it cannot justify physical performance claims.

For LoRa-specific decisions, synthetic evidence may justify implementing a prototype. Measured claims about range, contact capacity, loss/retry, energy or real routing superiority require the appropriate hardware campaign.

Current physical gate remains HW-006 before deriving real LoRa contact budgets or claiming superiority on the planned field/student network.

## Current literature checkpoint examples

### BPv7 interoperability

Interesting and highly relevant architecture, but **no immediate implementation yet**.

Current use case is semantic comparison and avoiding reinvention. There is not yet a concrete requirement to interoperate with an external BPv7 node/application. Therefore:

**Decision: RESEARCH ONLY + semantic/interop ADR.**

Reopen implementation when a concrete use case requires connection to a BPv7 ecosystem, tool or external DTN node.

### PNA2 / set reconciliation

Concrete use case exists:

> A relay and receiver share a very large manifest/dataset but differ in only a small number of chunks, while the contact has a scarce byte budget.

This passes the feature gate, but complex sketches do not automatically pass adoption. First compare simple encodings (sparse missing-index list, run-length/compressed bitmap) against minisketch/IBLT/rateless reconciliation.

**Decision: PROTOTYPE/benchmark.**

### LoRaMesher / Reticulum adapter

Concrete possible use case exists:

> During a contemporaneously connected multi-hop LoRa segment, use a mature mesh/post-IP transport underneath PollicinoNet instead of making the object/reconciliation layer also solve radio routing.

However the correct underlying stack is not yet established and physical topology matters.

**Decision: RESEARCH/adapter benchmark first; no replacement of current bearer layer yet.**

## Pull-request checklist

For any substantial new feature/architecture PR, include a short section:

```text
Use-case gate:
- use case:
- current baseline:
- measurable problem:
- proposed improvement:
- simplest competing solution:
- experiment/evidence:
- success/kill criterion:
- complexity/security cost:
- decision: ADOPT | PROTOTYPE | RESEARCH ONLY | DEFER | REJECT
```

This gate applies prospectively. Existing code is not presumed justified merely because it already exists; important existing subsystems may be audited against the same rule during future consolidation.
