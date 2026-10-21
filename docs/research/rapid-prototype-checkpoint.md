# RAPID prototype checkpoint

Status: 2026-08-27 — utility + distributed control + queue inference + read-only candidate inference validated

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

RAPID has three coupled responsibilities:

1. selection by marginal utility per resource unit;
2. inference of delivery probability/delay;
3. a control channel that propagates meeting, replica and delivery metadata.

For missed-deadline optimization, the paper defines utility from the probability that a packet is delivered within its deadline. At each opportunity RAPID prioritizes replication by marginal utility divided by packet size.

Primary reference:

- A. Balasubramanian, B. N. Levine, A. Venkataramani, *DTN Routing as a Resource Allocation Problem*, ACM SIGCOMM 2007, https://people.cs.umass.edu/~arun/papers/RAPID.pdf

## Layer 1 — deadline utility

Module: `pollicino.net.rapid_deadline_utility`

For each existing replica carrier:

```text
effective hazard = 1 / (mean meeting time * meetings needed)
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
- a faster expected carrier has greater deadline utility;
- equal benefit with larger transfer size produces lower utility per byte;
- queue pressure represented as additional required meetings lowers effective hazard;
- utility becomes zero after the usefulness deadline.

This is a mathematical component, **not a RAPID router**.

## Layer 2 — meeting/control knowledge

Module: `pollicino.net.rapid_meeting_control`

Each node maintains direct encounter history and learns an arithmetic mean inter-meeting interval after repeated encounters.

Metadata exchange:

- uses per-peer generation watermarks;
- sends only changed entries after bootstrap;
- accepts fresher estimates and rejects stale gossip;
- avoids immediate echo back to the same peer;
- can estimate an expected meeting path from local knowledge with a maximum 3-hop path.

The control model reports **metadata entry counts**, not wire bytes. No control serialization has been selected yet.

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

## Layer 3 — replica-location and final-delivery knowledge

Module: `pollicino.net.rapid_replica_control`

The model answers, using delayed gossip rather than future knowledge:

```text
where are complete replicas believed to exist?
has a final destination already received the bundle?
```

### Complete-replica advertisement

A carrier publishes:

```text
bundle_id
carrier_id
sequence
present = true | false
updated_at_s
```

Only complete verified replicas are represented. Partial Pollicino chunks remain reconciliation/cache state and are not silently counted as RAPID replicas.

`present=false` is a monotonic tombstone. After a newer deletion is observed, older gossip cannot resurrect that replica. A later reacquisition uses a still-higher sequence.

### Final-delivery acknowledgement

A final destination publishes:

```text
bundle_id
destination_id
sequence
delivered_at_s
```

This is distinct from radio/link ACKs, PNF1 frame ACKs and PNC1 custody receipts.

Replica/delivery exchange is delta-based and reports metadata entry counts only.

Validated properties:

- replica discovery through gossip;
- quiet repeated exchange after synchronization;
- stale-replica resurrection prevented by tombstones;
- reacquisition after deletion;
- delivery ACK propagation independently from replica state;
- same-sequence conflicting facts fail closed;
- bootstrap duplicate knowledge remains visible.

### Security boundary

The synthetic model assumes carrier-authored replica facts and destination-authored delivery facts. Cryptographic authentication is not implemented yet. Field use requires a separate security gate for authenticity, replay protection and rollback resistance.

## Layer 4 — queue / transfer-opportunity inference

Module: `pollicino.net.rapid_queue_inference`

The model estimates queue pressure without manufacturing physical capacity.

A local `RapidTransferOpportunityEstimator` observes only explicit opportunity-byte samples supplied by an experiment or measured adapter. It never derives capacity from contact duration, bearer kind or bitrate labels.

Given an explicit queue and an observed mean opportunity:

```text
bytes through selected bundle
--------------------------------  -> future meetings needed
expected bytes per opportunity
```

using a ceiling to identify the meeting on which that bundle could complete.

If no destination opportunity has ever been observed, the estimate is `None`; there is no built-in default.

Validated properties:

- arithmetic mean from observed opportunities;
- bytes ahead increase meetings needed;
- one large object may need several future meetings;
- no-history returns unknown;
- no duration-to-capacity inference exists in the API.

## Layer 5 — read-only deadline inference facade

Module: `pollicino.net.rapid_inference`

This layer combines current local knowledge without mutating any control state:

```text
meeting knowledge
+ known complete replicas
+ final delivery ACKs
+ explicit queue meetings-needed knowledge
+ application deadline
+ transfer bytes
        |
        v
candidate marginal deadline utility
```

Important fail-closed rule:

> If a known existing replica lacks its meeting estimate or queue estimate, the facade does not ignore that replica and compute an optimistically inflated marginal utility. The inference is marked incomplete and no rankable utility is returned.

Other validated cases:

- final delivery ACK forces marginal utility to zero;
- a candidate that already has a complete replica is not rankable;
- passed application deadline returns zero utility;
- inference is observational and leaves meeting/replica state unchanged.

## Remaining work before a RAPID routing strategy

### Candidate queue knowledge exchange

The current facade deliberately receives `meetings_needed_by_carrier` as explicit caller knowledge. A distributed router still needs a way to obtain the candidate/current carriers' queue estimates during control exchange without oracle access.

### Selection interface constraint

The current Pollicino routing strategy API filters bundles, while the common scheduler later reorders them by application priority/expiry/completion policy. RAPID requires ordering by `marginal utility / byte`.

Do **not** overload application priority to fake RAPID ordering.

The smallest next experiment is therefore a **one-selection-per-encounter RAPID prototype**: the strategy returns only the single highest-utility candidate, so the common scheduler cannot reorder multiple RAPID candidates. This tests the selection hypothesis without adding a new global scheduling abstraction.

A general strategy-controlled ranking hook should be considered only if a second concrete use case needs it.

### Control encoding

Only after the metadata schema and required candidate-queue exchange stabilize should an encoding experiment convert control entries into bytes and add a separate routing-control accounting line.

### Storage pressure

RAPID can delete low-utility packets under storage pressure. Pollicino already has relay quota/retention/GC, but routing-integrated utility eviction remains a separate gated experiment. Replica tombstones prepare the control model for that future without implementing eviction now.

## Next implementation order

```text
candidate/local queue estimate exchange
        |
one-selection-per-encounter RAPID prototype
        |
paired deadline comparison with
Direct / Epidemic / Spray / PRoPHET
        |
control encoding / byte accounting
        |
only then consider general ranking API
or storage-pressure utility eviction
```

## Validation

Validated checkpoints:

- canonical DTN baselines: Actions `33064225835` — PASS;
- deadline evaluator: Actions `33064502525` — PASS;
- preregistered EDU deadline discrimination: Actions `33064648987` — PASS;
- RAPID utility + meeting/control: Actions `33065224388` — PASS;
- RAPID replica/delivery control: Actions `33065697210` — PASS;
- RAPID queue inference: Actions `33065961577` — PASS;
- complete read-only RAPID inference chain: Actions `33066156183` — PASS.

Temporary validation workflows are removed after green runs.

## API status

The RAPID prototype components are intentionally **not promoted into `pollicino.net` top-level exports yet**. They remain explicit research modules until a complete routing experiment establishes a stable interface.

## Evidence boundary

All current results are `MODEL_SYNTHETIC`.

No physical meeting distribution, LoRa capacity, energy or real deadline-delivery claim is made.

**GATE PROVE FISICHE HW-006** remains unchanged for physical claims.
