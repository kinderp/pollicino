# Routing baseline implementation checkpoint

Status: 2026-08-26

This checkpoint records the first literature-driven DTN routing baselines implemented after the Use-Case Justification Gate and experimental-evaluation methodology were adopted.

## Implemented now

### Direct Delivery

`DirectDeliveryStrategy` forwards a bundle only when the encountered target is an explicit final destination.

Use as the lowest-complexity baseline:

- no relay replication;
- no encounter history;
- no topology state;
- no copy budget;
- zero forwarding traffic toward non-destination peers.

Validated scenario:

```text
A -> X -> D
```

Direct Delivery does not give the object to X, therefore it cannot reach D through the relay-only path.

When a later direct contact exists:

```text
A -> X   (unhelpful)
A -> D   (direct)
```

Direct Delivery reaches D while avoiding the A -> X replication traffic.

### Epidemic forwarding eligibility

`EpidemicStrategy` makes every bundle eligible at every encounter. The existing Pollicino scheduler/governed transfer then sends only data the encountered receiver is actually missing.

Validated scenario:

```text
A -> X -> D
```

Epidemic replication gives X the object/state needed to forward to D and succeeds where Direct Delivery cannot.

Important scientific boundary: this is the canonical **Epidemic forwarding eligibility** rule inside the Pollicino experiment harness. It is not a byte-for-byte reproduction of every control packet from the original Epidemic Routing implementation. Pollicino's existing PCM1/PNA1 reconciliation and governed PNB1/PNC1 transfer remain the control/data substrate and are accounted by the benchmark.

A separate experiment is required if the research question needs the exact overhead of a classic Epidemic summary-vector protocol rather than a common Pollicino reconciliation substrate.

## Why `FloodAllStrategy` still exists

`FloodAllStrategy` predates the literature baseline round and is behaviourally close to Epidemic eligibility. It remains for compatibility with previous experiments.

New literature comparisons should prefer the explicit `epidemic` strategy ID so reports distinguish a scientific baseline from the earlier project-specific experiment name.

## Validation

Actions run `32965570488`: PASS.

- full project test suite: PASS;
- `tests/test_net_routing_baselines.py`: PASS.

## Next blocker: stateful strategy lifecycle

Binary Spray-and-Wait and PRoPHET should not be forced into the current stateless selection interface.

They require state that evolves because of contacts:

### Binary Spray-and-Wait

Needs at least:

- per-bundle copy budget;
- per-peer copy ownership;
- update only when a transfer/copy handoff actually succeeds;
- an explicit decision for partial Pollicino chunk custody versus a complete DTN message copy.

### PRoPHET

Needs at least:

- encounter-history state;
- delivery predictabilities;
- aging over time;
- transitive updates;
- deterministic state cloning/reset for fair multi-strategy comparisons.

The existing `RoutingStrategy.select_bundles(...)` hook selects eligibility before a contact but does not receive an explicit post-contact result callback. Hiding state inference inside strategy objects would make repeated benchmarks fragile and make evidence harder to audit.

## Required next experiment-harness capability

Before implementing Spray-and-Wait or PRoPHET, add the smallest stateful-strategy lifecycle needed by at least these two independent baseline use cases.

Candidate conceptual contract:

```text
strategy.start_scenario(initial_context)
strategy.select_bundles(contact_context)
strategy.observe_contact(contact_result)
strategy.finish_scenario()
```

The exact API is not adopted yet. It must preserve:

- independent state per strategy;
- deterministic scenario reset;
- cloned state in multi-scenario benchmarks;
- no mutation leakage between strategies;
- explicit evidence/accounting;
- current stateless strategies without unnecessary boilerplate.

## Use-case gate decision

**Direct Delivery: ADOPT AS BASELINE.**

**Epidemic eligibility: ADOPT AS BASELINE.**

**Stateful routing lifecycle: PROTOTYPE/JUSTIFIED.** It is now supported by at least two independent literature baselines (Spray-and-Wait and PRoPHET), so it satisfies the architecture-gate requirement for a shared benchmark abstraction. The implementation should still be minimal and benchmark-scoped until runtime use cases require the same abstraction.
