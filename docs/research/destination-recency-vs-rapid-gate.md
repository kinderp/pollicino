# Destination Recency vs RAPID — Use-Case Gate checkpoint

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-27

## Question

After fixing RAPID's triangular per-bundle queue-quote overhead with a shared opportunity quote, is the remaining RAPID complexity justified for the current school/data-mule micro-object use cases?

The Use-Case Justification Gate requires comparison against the simplest plausible alternative before promoting a richer routing architecture.

## Minimal alternative

`destination_recency.py` implements a deliberately small heuristic:

```text
node state:
    last direct encounter time with destination/gateway

on A -> B:
    if B saw D more recently than A:
        forward
    else:
        hold
```

Properties:

- exactly one final destination in the first prototype;
- no delivery probability;
- no transitive graph;
- no replica-location gossip;
- no queue state;
- no per-bundle routing state;
- no future-contact knowledge;
- direct delivery always allowed.

The only modeled decision-control item on a non-destination directed encounter is one target-to-source recency quote.

## Control representation

Two research encodings are counted, using the same basic assumptions as the RAPID control experiments:

1. full 128-bit pseudonymous destination reference;
2. shared u16 destination index plus one canonical four-node dictionary representation.

A quote carries:

```text
destination reference
+ u64 last-seen timestamp
```

A reserved timestamp value can represent UNKNOWN, so no extra boolean is required in this model.

Authentication/encryption remain outside the current MODEL_SYNTHETIC accounting.

## Workload

The same many-micro-object topology used by the RAPID amortization study:

```text
A -> X     one initially uninformed relay opportunity
A -> B     repeated useful relay opportunities
B -> D     repeated final-delivery opportunities
```

64-byte one-chunk objects, with checkpoints:

```text
1, 2, 5, 10, 20 objects
```

Explicit prior recency state:

```text
A last saw D at 900
B last saw D at 940
```

All prior observations precede the first routing window.

## Validation

GitHub Actions `33081651176`:

- full project suite: 266 passed, 2 skipped;
- targeted Destination Recency tests: PASS.

## Results

`delta = simple governed transfer + modeled recency control - Epidemic wire`.

Negative is cheaper.

| Objects | Epidemic wire | Recency governed transfer | Indexed control | Indexed delta | Full-ID control | Full-ID delta | Recency quotes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1890 | 1260 | 104 | -526 | 56 | -574 | 2 |
| 2 | 3780 | 2520 | 118 | -1142 | 84 | -1176 | 3 |
| 5 | 9450 | 6300 | 160 | -2990 | 168 | -2982 | 6 |
| 10 | 18900 | 12600 | 230 | -6070 | 308 | -5992 | 11 |
| 20 | 37800 | 25200 | 370 | -12230 | 588 | -12012 | 21 |

The recency quote count is linear:

```text
N + 1
```

for this topology: one initial A->X decision plus one A->B decision per object.

## Comparison with RAPID + shared opportunity quote

The immediately preceding RAPID checkpoint on the same transfer pattern produced indexed shared-quote deltas:

| Objects | RAPID shared-quote delta vs Epidemic | Destination Recency indexed delta |
| ---: | ---: | ---: |
| 1 | -134 | -526 |
| 2 | -229 | -1142 |
| 5 | -229 | -2990 |
| 10 | -229 | -6070 |
| 20 | -229 | -12230 |

Both approaches avoid the unnecessary A->X content replication and deliver through B. The simple heuristic therefore captures the useful routing decision in this workload with dramatically less modeled control state.

## A useful secondary result

For a tiny four-node campaign, the full-ID recency representation is cheaper than the indexed representation at 1 and 2 objects because the 76-byte dictionary bootstrap costs more than the ID savings. Indexed references become favorable only after enough quote reuse.

This reinforces the general Pollicino rule:

> shared context is valuable only when its establishment cost is actually amortized.

## Gate decision

### Destination Recency

**Decision: PROTOTYPE / mandatory simple baseline.**

It is not promoted to production routing yet, but every richer encounter-history strategy should have to beat it on relevant workloads.

### RAPID for UC-DNA-001 / UC-CONTENT-001 micro-object routing

**Decision: DEFER as an adoption candidate; keep as RESEARCH.**

RAPID works, but current evidence does not justify its extra meeting, replica, delivery and queue-control machinery for this use case because a much simpler heuristic achieves the same useful forwarding pattern at much lower modeled control cost.

RAPID should be reconsidered only when a concrete use case/scenario demonstrates a failure mode of Destination Recency that matters to the application, for example where recency alone cannot represent queue pressure, deadline utility, multiple competing replicas or heterogeneous service opportunity.

Do not invent such complexity first. Find the discriminating use case first.

## Architecture implication

This result argues against adding a general RAPID ranking hook to the common comparator now.

The next justified development priority can move away from routing complexity and back to a problem already justified directly by scarce-link use cases: **PNA2 reconciliation codec regimes**.

## Evidence boundary

All numbers are deterministic `MODEL_SYNTHETIC` accounting. No physical LoRa range, capacity, airtime, energy or field superiority is claimed. Those remain behind **GATE PROVE FISICHE HW-006**.
