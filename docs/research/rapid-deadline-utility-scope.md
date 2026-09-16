# RAPID deadline utility prototype scope

Status: PROTOTYPE COMPONENT, not yet a RAPID router

## Why this is gated now

`UC-EDU-001` and `UC-EMERG-001` require delivery-before-application-deadline metrics. The deterministic deadline discrimination experiment demonstrates that eventual delivery can hide a meaningful late-delivery failure.

The original RAPID paper explicitly supports minimizing missed deadlines by defining per-packet utility as the probability of delivery within a deadline and then selecting replications by marginal utility per unit resource.

Reference:

- Balasubramanian, Levine, Venkataramani, *DTN Routing as a Resource Allocation Problem*, SIGCOMM 2007: https://people.cs.umass.edu/~arun/papers/RAPID.pdf

## RAPID has three distinct components

The paper separates:

1. **selection** — rank candidate replications by marginal utility / packet size;
2. **inference** — estimate delivery probability/delay from replica and meeting information;
3. **control channel** — exchange metadata needed by the inference step.

PollicinoNet must not implement only (1) and silently call the result a faithful RAPID protocol.

## First implementation boundary

Implement only the deadline-utility math for the paper's tractable exponential-meeting model.

For a packet with remaining useful time `t`, and independent replica carriers whose direct meeting times with the destination are modeled as exponentials, the aggregate delivery hazard is the sum of each replica's effective hazard.

For replica `j`:

```text
hazard_j = 1 / (mean_direct_meeting_seconds_j * meetings_needed_j)
```

Then:

```text
P(deliver within t) = 1 - exp(-t * sum(hazard_j))
```

`meetings_needed_j` represents queue/bandwidth pressure in the same spirit as the paper's `n_j(i)` term; the initial tests use `1` unless an explicit workload provides a different value.

For a candidate new replica:

```text
marginal utility = P_after - P_before
score = marginal utility / transfer_bytes
```

If the application deadline has already passed, utility is zero.

## What this prototype can answer

- Does an additional replica improve deadline-delivery probability?
- Does marginal benefit fall when many useful replicas already exist?
- Does a faster expected carrier have greater value than a slow carrier?
- Does RAPID's per-byte ranking prefer a cheaper transfer when benefit is otherwise similar?

## What it cannot answer yet

It is **not yet a routing strategy** because it does not yet provide:

- per-node historical meeting-time estimation;
- dissemination/merging of meeting-time metadata;
- replica-location metadata;
- delivered-packet acknowledgements;
- queue ordering inferred from competing traffic;
- storage eviction by utility;
- explicit control-channel bytes;
- stale metadata behavior.

No comparison should label this component simply `RAPID` until those responsibilities are either modeled or explicitly isolated as an idealized variant.

## Next step after utility validation

Build a local historical meeting estimator and a control-state model. Keep control operations/counts separate from Pollicino content TRC until an actual control encoding exists.

Only after that should an encounter strategy implement the paper's sequence:

```text
exchange metadata
-> direct delivery first
-> compute marginal utility for remaining packets
-> replicate in descending marginal-utility-per-byte order
```

## Use-case decision

**Decision: PROTOTYPE.**

The utility component is justified by two active use cases and a benchmark result that proves deadline metrics distinguish behavior hidden by eventual delivery.

## Evidence / physical boundary

The math and synthetic routing experiments are `MODEL_SYNTHETIC`.

Real meeting distributions, transfer sizes and on-time delivery performance remain behind **GATE PROVE FISICHE HW-006** and later field evidence.
