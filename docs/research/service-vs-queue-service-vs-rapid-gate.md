# Destination Service vs queue-aware service vs RAPID

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-28

## Use-case question

A student-carried node can have the same historical gateway frequency and the same useful bytes per gateway contact as another node, yet have a large amount of higher-priority or earlier queued material to transmit first.

This is relevant to both:

- `UC-DNA-001`: many topic/alert micro-objects can compete for the next gateway contact;
- `UC-CONTENT-001`: references/manifests/chunks can share a destination-facing queue.

The question is whether `DestinationServiceStrategy` is still sufficient when **bytes ahead of the target object** differ.

## Controlled discriminator

A and C are deliberately identical under Destination Service:

```text
mean direct destination interval = 50 s
mean useful opportunity           = 64 B
object size                        = 64 B
```

Therefore:

```text
Destination Service(A) = 50 s
Destination Service(C) = 50 s
```

The only difference introduced is queue backlog:

```text
A: 256 B ahead + 64 B target = 320 B = 5 destination meetings
C:   0 B ahead + 64 B target =  64 B = 1 destination meeting
```

No bearer label, contact duration, recency advantage or future contact schedule is used to distinguish them.

## RAPID queue inference

The existing explicit queue estimator reports:

```text
A meetings_needed = 5
C meetings_needed = 1
```

Using those estimates with identical 50-second direct meeting means gives positive marginal utility for adding C as a replica before a usefulness deadline.

This proves a narrow point:

> queue backlog can contain routing-relevant information that mean interval × object-size/opportunity alone cannot represent.

## Simpler baseline first

Before promoting RAPID, `destination_queue_service.py` adds the smallest research baseline that captures exactly this missing dimension:

```text
meetings_needed
  = ceil((bytes_ahead + object_bytes) / mean_opportunity_bytes)

queue_service_seconds
  = mean_interval_seconds * meetings_needed
```

For the discriminator:

```text
A = 50 * 5 = 250 s
C = 50 * 1 =  50 s
```

The simple queue-aware service score therefore prefers C, matching the useful distinction made by RAPID's queue-aware utility without adding:

- deadline probability;
- replica-location gossip;
- transitive meeting graph;
- diminishing-return replica utility;
- future-contact knowledge.

## Gate decision

The routing ladder becomes:

```text
Destination Recency
    ↓ fails when recent != regular
Destination Interval
    ↓ fails when frequency != useful service capacity
Destination Service
    ↓ fails when equal service hides queue backlog
Destination Queue Service
    ↓
RAPID only if a concrete use case still defeats this simpler model
```

**Decision: RAPID remains RESEARCH / DEFER.**

Queue backlog is now justified as a research dimension, but full RAPID is not justified by this discriminator because a much simpler queue-aware service estimate captures the same distinction.

## What could still justify RAPID

The strongest remaining discriminators are dimensions that queue-aware local service cannot model naturally:

1. multiple existing replicas where another copy has diminishing marginal value;
2. multiple competing objects with different usefulness deadlines sharing one encounter;
3. transitive opportunity where the useful carrier does not directly meet the final gateway;
4. correlated/phase-sensitive mobility where equal means hide very different time-to-next-contact distributions.

Each should first be challenged by the smallest dedicated baseline.

## Validation

GitHub Actions `33164313518`: full project suite PASS and targeted queue-gate tests PASS.

## Evidence boundary

All inputs and results are deterministic `MODEL_SYNTHETIC` research evidence. No physical airtime, real queue behavior, energy, range or field-network superiority is claimed.

Real calibration remains behind **GATE PROVE FISICHE HW-006**.
