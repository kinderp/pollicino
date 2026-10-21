# Stateful routing strategy lifecycle — minimal design

Status: design checkpoint before Spray-and-Wait / PRoPHET implementation

## Why this exists

The current routing comparator was intentionally sufficient for stateless or scenario-hint strategies:

- Flood/Epidemic eligibility;
- Direct Delivery;
- gateway-progress rank;
- emergency flooding;
- bearer-size hold policy.

Two independent literature baselines now require state that evolves across contacts:

1. **Binary Spray-and-Wait** — per-bundle copy budgets change only after a successful copy handoff;
2. **PRoPHET** — encounter history, aging and transitive delivery predictabilities evolve over scenario time.

This satisfies the architecture side of the Use-Case Justification Gate for a shared *benchmark* lifecycle. It does not automatically justify the same abstraction in production runtime code.

## Requirements

The lifecycle must guarantee:

- strategy configuration is reusable and does not accumulate hidden state;
- every strategy/scenario run receives a fresh mutable runtime;
- repeated benchmark execution on the same scenario object produces the same result;
- no state leaks between strategies;
- no state leaks between seeds/scenarios;
- post-contact updates use actual scheduled/transfer results rather than assuming selection equals success;
- existing stateless strategies remain valid without boilerplate;
- state can be inspected/exported for evidence when needed;
- synthetic/model state is never mislabeled as physical evidence.

## Minimal conceptual split

```text
RoutingStrategy                 RoutingStrategyRuntime
----------------                ----------------------
immutable configuration   ->    fresh per scenario
strategy_id                     mutable algorithm state
new_runtime() optional          select_bundles(...)
                                observe_contact(...)
```

Existing stateless strategies may continue to act as their own runtime. The comparator should only create a separate runtime when a strategy explicitly supports it.

## Contact lifecycle

For each ordered contact window:

```text
fresh/current runtime
      |
      v
select_bundles(contact context)
      |
      v
Pollicino scheduler + governed transfer
      |
      v
StrategyWindowReport
      |
      v
observe_contact(actual outcome)
```

`select_bundles` is called exactly once for each strategy/contact in deterministic order.

A stateful runtime may update encounter-only state during selection (for example PRoPHET's direct encounter update), but any state that depends on whether bytes/custody were actually transferred must be committed only from `observe_contact`.

## Post-contact observation

The observation should expose existing evidence, not invent a second report hierarchy. Minimum fields/references:

```text
window
source_id
target_id
selected bundle IDs
StrategyWindowReport / BearerSchedulingReport
current custody ledger view
```

This is enough for a Spray-and-Wait runtime to distinguish:

- selected but no transferable bytes;
- partial transfer;
- target obtained complete verified custody;
- duplicate/zero-wire contact.

It also lets future algorithms inspect only information explicitly available in the experimental model.

## Binary Spray-and-Wait semantic decision needed

Pollicino objects may be chunked and partially held by a relay, while classic Spray-and-Wait normally reasons about copies of a complete message.

The first baseline should therefore use a conservative rule:

> a Spray copy ticket is transferred only when the target obtains complete verified custody of the bundle/object.

Partial chunks may be cached by Pollicino transport, but a peer without a copy ticket is not allowed to act as an independent Spray relay for that bundle.

This keeps the literature copy-budget concept auditable while preserving Pollicino exact/chunk semantics.

If this rule proves inappropriate for a concrete use case, chunk-level copy budgets require a separate gate and experiment.

## PRoPHET state

A future runtime will need at least:

- per-peer delivery predictability;
- last update/aging time;
- direct encounter update;
- transitive update;
- deterministic parameter configuration;
- optional exported state snapshots for debugging/evidence.

No geography, RSSI or physical delivery probability should be silently mixed into PRoPHET predictability unless an explicit experiment defines that extension.

## Repetition test required before adoption

The lifecycle implementation is not accepted until a test demonstrates:

```text
same scenario object
same strategy configuration
run benchmark twice
=> byte-for-byte equivalent reports
```

for both a stateful dummy strategy and the first real stateful baseline.

This prevents hidden runtime state from surviving a benchmark invocation.

## Decision

**PROTOTYPE/JUSTIFIED for the experiment harness.**

Implement the smallest optional runtime/post-contact mechanism required by Binary Spray-and-Wait and PRoPHET. Do not introduce a general production plugin/runtime framework at this stage.
