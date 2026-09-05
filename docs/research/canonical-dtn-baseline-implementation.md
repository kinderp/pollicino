# Canonical DTN routing baselines in PollicinoNet

Status: implemented synthetic benchmark baselines

## Purpose

PollicinoNet should compare new routing ideas against established DTN behavior before treating a proprietary strategy as useful. The canonical baseline set is therefore:

1. Direct Delivery;
2. Epidemic;
3. Binary Spray-and-Wait;
4. PRoPHET.

These implementations are benchmark controls, not new PollicinoNet routing claims. They run through the same governed chunk transfer, cache/reconciliation, custody, fairness and TRC machinery as the existing experimental strategies.

All results in the current scenario-family harness remain `MODEL_SYNTHETIC` evidence.

## Direct Delivery

Use case: establish the cheapest one-copy/no-relay lower baseline.

Rule:

```text
encounter target is final destination?
  yes -> offer bundle
  no  -> do not replicate
```

This can have very low traffic but fails whenever the original carrier never meets a destination.

## Epidemic

Use case: establish the high-redundancy delivery baseline.

Rule:

```text
every encounter -> offer every bundle
```

The routing rule is epidemic, but the underlying transfer is intentionally Pollicino-aware: a receiver availability summary suppresses chunks it already owns. Consequently this is a canonical replication-policy baseline inside the Pollicino transport, not a byte-for-byte reproduction of every control message in the original Epidemic implementation.

An explicit Epidemic summary-vector protocol should be modeled only if a research question requires its control-plane cost.

## Binary Spray-and-Wait

Use case: limit replication while retaining more delivery opportunity than Direct Delivery.

Each bundle begins with a bounded logical copy budget `L` (current benchmark factory: `L=4`).

For a non-destination encounter:

```text
carrier has n > 1 tokens
        |
        +-- reserve floor(n/2) for target
        +-- retain the remainder
```

A carrier with one token enters the wait phase and forwards only to a final destination.

### Chunked-transfer adaptation

Classic Spray-and-Wait describes message copies as atomic. Pollicino exact objects may need several bounded contacts to complete a replica. The benchmark therefore uses a reservation:

```text
source tokens
    |
    +-- retained active tokens
    +-- reserved target tokens
              |
              +-- target becomes exact -> activate there
              +-- no progress -> return to source
              +-- partial progress -> keep reservation
```

The invariant is:

> active copy tokens + reserved copy tokens never exceed the configured initial copy budget.

Copy tokens are routing-model state. They are not encoded into PNB1 and do not change the frozen wire protocol.

## PRoPHET

Use case: exploit non-random encounter history instead of replicating blindly.

The implementation is inspired by RFC 6693 and models its three core mechanisms:

1. predictability increase after direct encounters;
2. predictability aging over elapsed time;
3. transitive predictability through encountered peers.

Initial benchmark parameters follow the RFC's recommended starting values when measurement-derived values are unavailable:

```text
P_encounter_max     0.7
P_encounter_first   0.5
P_first_threshold   0.1
beta                0.9
gamma               0.999
delta               0.01
```

The forwarding decision is deliberately simple:

```text
final destination?
  yes -> forward

otherwise:
  target predictability to destination
      > source predictability + margin
  -> forward
```

### Important control-plane limitation

PRoPHET normally requires routing-information exchange. The current Pollicino model updates prediction tables in memory when a synthetic contact occurs but does **not** manufacture RIB/control packet sizes.

Therefore:

- delivery and forwarding behavior can be compared now;
- Pollicino payload/protocol-transfer traffic can be measured now;
- a claim that PRoPHET has lower *total network traffic* than another strategy is not yet justified, because its routing-control traffic is absent from TRC.

A future control-plane experiment should report routing-state bytes separately before deciding whether they belong in an end-to-end cost metric.

## Scenario-family comparison

`canonical_dtn_strategy_factory()` derives final destinations from rank-zero generated gateways and returns all four baselines. Non-zero static gateway ranks are deliberately ignored, so Direct/Spray/PRoPHET do not receive the generator's oracle-like whole-scenario route rank.

For every generated scenario:

```text
same nodes
same bundles
same initial caches
same contact windows
same logical budgets
same seed
        |
        +-- Direct Delivery
        +-- Epidemic
        +-- Binary Spray-and-Wait
        +-- PRoPHET
```

Mutable peer stores, custody state, scheduler state and routing-strategy state remain isolated between strategies/runs.

## Current validation

Tests cover:

- Direct Delivery failing where a relay is required;
- Direct Delivery avoiding unnecessary replication when a direct path exists;
- Epidemic relay delivery;
- Binary Spray copy-budget conservation;
- Binary Spray wait phase at one remaining token;
- PRoPHET learning a useful relay from prior encounters;
- PRoPHET skipping an uninformed relay in a controlled scenario;
- reset/reproducibility of mutable routing state between independent benchmark runs;
- four-baseline execution over the exact same deterministic scenario families.

## Use-case gate

Decision: **ADOPT AS BENCHMARK BASELINES**, not as the production routing policy.

They are justified because several existing use cases need routing comparisons, including school/data-mule dissemination, content/reference ferry, sensor ferry, scheduled mobility, educational delivery and fleet-management propagation.

Any production/default routing policy remains a separate adoption decision.

## Next gate

RAPID-like routing is intentionally not included in this baseline block. It optimizes an explicit utility objective; implementing it before choosing that objective would violate the Use-Case Justification Gate.

`UC-EDU-001` now provides a plausible concrete next experiment because it has a meaningful delivery-before-class/deadline objective. That workload should define application deadline semantics and success/kill criteria before a RAPID-like strategy is implemented.

## Physical boundary

No hardware evidence is required for this baseline implementation.

Real claims about LoRa contact capacity, range, energy or routing superiority on the student network remain behind **GATE PROVE FISICHE HW-006**.
