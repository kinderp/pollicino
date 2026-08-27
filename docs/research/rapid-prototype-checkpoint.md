# RAPID prototype checkpoint

Status: 2026-08-27 — utility + meeting/control foundations validated

## Why RAPID work is now justified

Two independent use cases need application usefulness deadlines:

- `UC-EDU-001` — deliver classroom resource descriptors before a lesson/deadline;
- `UC-EMERG-001` — deliver time-sensitive bulletin/status information before it becomes stale.

The preregistered EDU discrimination experiment additionally demonstrated that eventual delivery ratio can hide a real application failure:

```text
application deadline = 1030

Direct Delivery          -> undelivered
Epidemic                 -> delivered 1025, on time
Binary Spray-and-Wait L2 -> delivered 1065, late
PRoPHET                   -> delivered 1025, on time
```

Thus deadline-aware utility is not speculative complexity.

## Literature checkpoint

The implementation plan follows the structure of the original RAPID work rather than using the name for a generic deadline sorter.

RAPID has three coupled components:

1. selection by marginal utility per resource unit;
2. inference of delivery probability/delay;
3. a control channel that propagates meeting, replica and delivery metadata.

For missed-deadline optimization, the paper defines utility from the probability that a packet is delivered within its deadline. At each opportunity RAPID prioritizes replication by marginal utility divided by packet size.

Primary reference:

- A. Balasubramanian, B. N. Levine, A. Venkataramani, *DTN Routing as a Resource Allocation Problem*, ACM SIGCOMM 2007, https://people.cs.umass.edu/~arun/papers/RAPID.pdf

## Implemented layer 1 — deadline utility

Module: `pollicino.net.rapid_deadline_utility`

The current component models the tractable independent-exponential case from the RAPID inference discussion.

For each existing replica carrier:

```text
effective hazard = 1 / (mean direct meeting time * meetings needed)
```

Across replicas:

```text
P(delivery within t) = 1 - exp(-t * sum(hazards))
```

For a proposed replica:

```text
marginal utility = P_after - P_before
score = marginal utility / transfer_bytes
```

Validated properties:

- probability increases with useful replicas;
- marginal gain falls as useful replicas accumulate;
- a carrier expected to reach the destination sooner has greater deadline utility;
- equal benefit with larger transfer size produces lower utility per byte;
- queue pressure represented as additional required meetings lowers effective hazard;
- utility becomes zero after the usefulness deadline.

This is a mathematical component, **not a RAPID router**.

## Implemented layer 2 — meeting/control knowledge

Module: `pollicino.net.rapid_meeting_control`

Each node maintains local direct encounter history and learns an arithmetic mean inter-meeting interval after repeated encounters.

Nodes can exchange changed meeting-time metadata. The model:

- keeps per-peer generation watermarks;
- sends only entries that changed since the previous metadata exchange with that peer;
- accepts fresher estimates and rejects stale gossip;
- does not immediately echo metadata just received from the same peer;
- estimates expected meeting time through the locally known graph with a maximum 3-hop path.

The 3-hop bound mirrors the practical meeting-time estimation approach described in the RAPID paper.

### Important accounting rule

The control model reports **metadata entry counts**, not wire bytes.

No serialization has been selected yet, therefore:

```text
control entry count != control wire bytes
```

The first exchange can legitimately contain redundant knowledge. Example validated in tests:

```text
A knows A-B
B knows A-B and B-D
first A<->B exchange:
  A sends 1 entry
  B sends 2 entries
  total = 3

next unchanged exchange:
  total = 0
```

That bootstrap cost is preserved instead of being optimized away by assumption.

## What is still missing before a RAPID routing strategy

### Layer 3 gate — replica-location + delivery acknowledgement metadata

The next prototype must model the minimum distributed state needed to answer two questions without oracle knowledge:

```text
where are complete replicas believed to exist?
has a final destination already received the bundle?
```

The first model is deliberately separate from PNB1/PNC1 and radio ACKs:

- a **replica advertisement** is authored by the carrier it describes and has a monotonic per-bundle sequence;
- advertisements can say `present=true` or `present=false`, so a later storage-eviction experiment can publish a tombstone rather than letting stale gossip resurrect a deleted replica;
- only **complete, verified replicas** count in the first RAPID utility model; partial chunks remain Pollicino reconciliation state and are not silently treated as full RAPID copies;
- a **delivery acknowledgement** is authored by the final destination and is monotonic: once a destination has delivered a bundle, gossip can propagate that fact and suppress future utility/replication work;
- metadata exchange is delta-based with per-peer watermarks and reports entry counts only;
- no control byte cost is assigned until a separate encoding experiment is justified and benchmarked.

This is research metadata, not authenticated production state. Before field use, a separate security gate must define authenticity, replay protection and rollback resistance for carrier/destination-authored control facts.

### Buffer/queue inference

The full delay estimate depends on packet position and expected transfer opportunity. Current deadline utility exposes `meetings_needed`, but a routing strategy must derive it from explicit workload/buffer assumptions rather than inventing it.

### Control encoding

Only after the required metadata schema is stable should an encoding experiment convert control entries into bytes and include them in a separate routing-control accounting line.

### Storage pressure

RAPID can delete low-utility packets under storage pressure. Pollicino already has relay quota/retention/GC, but routing-integrated utility eviction remains a separate gated experiment. Replica tombstones prepare the control model for that future without implementing eviction now.

## Next implementation order

```text
replica-location metadata
        |
delivery-ack metadata
        |
meeting + replica control exchange
        |
queue / transfer-opportunity estimator
        |
RAPID deadline selection strategy
        |
paired comparison with
Direct / Epidemic / Spray / PRoPHET
```

Do not skip directly to the last line.

## Validation

Latest complete validation at this checkpoint:

- GitHub Actions run `33065224388` — PASS;
- project test suite — PASS;
- deadline + RAPID targeted suite — PASS.

An earlier run intentionally exposed one incorrect test expectation about bootstrap metadata count; the model was retained and the test corrected from 2 to the actual 3 entries.

## API status

The RAPID prototype components are intentionally **not promoted into `pollicino.net` top-level exports yet**. They remain explicit research modules until a complete routing experiment establishes a stable interface.

## Evidence boundary

All current results are `MODEL_SYNTHETIC`.

No physical meeting distribution, LoRa capacity, energy or real deadline-delivery claim is made.

**GATE PROVE FISICHE HW-006** remains unchanged for physical claims.
