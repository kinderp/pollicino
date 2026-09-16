# Replica quality and marginal-value routing gate

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-28

## Use-case question

A scarce school/off-grid contact may have room for only one additional object copy. Two candidate objects can look identical under all local carrier-service metrics, yet differ because one already has a very strong replica elsewhere while the other has only a weak replica.

This matters for both primary use cases:

- `UC-DNA-001`: many same-sized, similarly urgent topic objects may compete for one contact;
- `UC-CONTENT-001`: references/manifests can compete even when their local transfer cost is identical.

The question is whether another copy has the same value merely because object size, deadline, candidate carrier and replica count are equal.

## Controlled discriminator

Both objects deliberately share:

```text
object bytes              = 64
remaining useful time     = 120 s
candidate C mean to D     = 60 s
candidate meetings needed = 1
candidate queue/service   = identical
existing replica count    = 1
```

The only difference is the quality of the already-existing replica:

```text
Object X: existing replica reaches D every ~20 s
Object Y: existing replica reaches D every ~200 s
```

A replica-count heuristic sees a tie: one existing replica each.
A local Queue Service score for candidate C also sees a tie.

## Marginal-value result

Using the already implemented independent-exponential deadline utility:

- X has much higher probability of on-time delivery before adding C;
- Y has lower probability before adding C;
- adding the same candidate C has positive value for both;
- the marginal utility and marginal-utility-per-byte are materially greater for Y.

Therefore, under one scarce copy opportunity, Y is the better replication target even though local service, size, deadline and replica count are identical.

## Gate interpretation

This is the first discriminator in the current ladder that cannot be resolved by simply adding another local scalar about the encountered carrier (recency, interval, capacity, queue backlog) or by counting replicas.

It justifies a narrower primitive:

> **replica quality / marginal value matters when deciding which object deserves an additional copy.**

It does **not** yet justify adopting the complete RAPID control architecture. In particular this test does not require:

- full meeting-graph gossip;
- generalized transitive routing;
- production replica advertisements;
- a generalized RAPID ranking hook in the common routing API;
- any physical LoRa claim.

## Current routing ladder

```text
Recency
  ↓ recent contact can be irregular
Interval
  ↓ frequent contact can be thin
Service (interval × useful opportunity)
  ↓ equal service can hide queue backlog
Queue Service
  ↓ equal local service + equal replica count can hide replica quality
Replica marginal value
  ↓
full RAPID only if further use cases justify its wider control machinery
```

## Next gate

The next scientifically useful experiment is end-to-end **multiple-object competition in one bounded encounter**:

- same short contact budget;
- two or more objects;
- explicit usefulness deadlines;
- explicit existing replica locations/quality;
- compare a simple replica-quality/marginal-value selector against the current RAPID one-selection kernel.

If the narrow marginal-value selector reproduces RAPID, keep the narrow primitive. If it fails due transitivity/control-state interactions while RAPID succeeds, that would provide stronger justification for more of RAPID.

## Validation

GitHub Actions `33164468215`: full project suite PASS and targeted replica-marginal-value gate PASS.

## Evidence boundary

All values are deterministic `MODEL_SYNTHETIC` research evidence. The exponential meeting assumption is a tractable model, not a claim about real student mobility.

Real calibration remains behind **GATE PROVE FISICHE HW-006**.
