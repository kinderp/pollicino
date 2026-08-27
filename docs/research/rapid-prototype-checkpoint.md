# RAPID prototype checkpoint

Status: 2026-08-27 — utility + meeting/control + replica/delivery control validated

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

The control model reports **metadata entry counts**, not wire bytes. No serialization has been selected yet.

A validated bootstrap example is:

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

That initial duplicate knowledge is preserved as real modeled control work.

## Implemented layer 3 — replica-location and final-delivery knowledge

Module: `pollicino.net.rapid_replica_control`

The model answers, using delayed gossip rather than future knowledge:

```text
where are complete replicas believed to exist?
has a final destination already received the bundle?
```

### Complete-replica advertisement

A carrier can publish its own state for a bundle:

```text
bundle_id
carrier_id
sequence
present = true | false
updated_at_s
```

Only complete verified replicas are represented in this layer. Partial Pollicino chunks remain reconciliation/cache state; they are not silently counted as RAPID message replicas.

The per-carrier/per-bundle sequence is monotonic. `present=false` is a tombstone. Once a node has observed a newer tombstone, older gossip cannot resurrect the deleted replica.

A carrier may later reacquire the object and publish a still-higher `present=true` sequence.

### Final-delivery acknowledgement

A final destination can publish a separate monotonic acknowledgement:

```text
bundle_id
destination_id
sequence
delivered_at_s
```

This is deliberately different from:

- radio/link ACK;
- PNF1 frame ACK;
- PNC1 custody receipt.

Its meaning is application/end-destination delivery knowledge for routing inference and future useless-copy suppression.

### Delta gossip

Replica and delivery facts use per-peer generation watermarks. Unchanged repeated exchange becomes zero-entry control work after bootstrap. Exchange reports counts by metadata type, but still **does not assign wire bytes**.

Validated properties include:

- complete replica discovery through gossip;
- unchanged delta exchange becomes quiet;
- tombstones prevent stale resurrection;
- reacquisition after deletion uses a higher authority sequence;
- delivery acknowledgements propagate independently from replica state;
- same-sequence conflicting facts fail closed;
- bootstrap duplicate knowledge is visible rather than silently removed.

### Security boundary

The synthetic model assumes that a carrier authors its own replica facts and a destination authors its own delivery acknowledgements. Cryptographic authentication is not implemented yet. Field use requires a separate security gate for authentication, anti-replay and rollback resistance.

## What is still missing before a RAPID routing strategy

### Layer 4 — queue / transfer-opportunity inference

The full delay estimate depends on packet position and expected transfer opportunity. Current deadline utility exposes `meetings_needed`, but a routing strategy must derive it from explicit workload/buffer assumptions rather than inventing it.

The next prototype should therefore use observable local queue state plus explicit transfer opportunity assumptions to derive a bounded estimate. It must not derive physical capacity from synthetic contact duration.

### Combined control view

Meeting knowledge and replica/delivery knowledge currently live in separate research modules. They should first be combined through a read-only inference facade rather than merged into one giant mutable state object.

### Control encoding

Only after meeting + replica + delivery metadata schemas are stable should an encoding experiment convert entries into bytes and add a separate routing-control accounting line.

### Storage pressure

RAPID can delete low-utility packets under storage pressure. Pollicino already has relay quota/retention/GC, but routing-integrated utility eviction remains a separate gated experiment. Replica tombstones prepare the control model for that future without implementing eviction now.

## Next implementation order

```text
queue / transfer-opportunity estimator
        |
read-only RAPID inference facade
(meeting + replicas + deadline utility)
        |
RAPID deadline selection strategy
        |
paired comparison with
Direct / Epidemic / Spray / PRoPHET
        |
control encoding / byte accounting
        |
storage-pressure experiment
```

Do not skip directly to the selection strategy.

## Validation

Validated checkpoints:

- canonical DTN baselines: Actions `33064225835` — PASS;
- deadline evaluator: Actions `33064502525` — PASS;
- preregistered EDU deadline discrimination: Actions `33064648987` — PASS;
- RAPID utility + meeting/control: Actions `33065224388` — PASS;
- RAPID replica/delivery control: Actions `33065697210` — PASS.

An earlier meeting-control run exposed one incorrect test expectation about bootstrap metadata count; the model was retained and the test corrected from 2 to the actual 3 entries.

## API status

The RAPID prototype components are intentionally **not promoted into `pollicino.net` top-level exports yet**. They remain explicit research modules until a complete routing experiment establishes a stable interface.

## Evidence boundary

All current results are `MODEL_SYNTHETIC`.

No physical meeting distribution, LoRa capacity, energy or real deadline-delivery claim is made.

**GATE PROVE FISICHE HW-006** remains unchanged for physical claims.
