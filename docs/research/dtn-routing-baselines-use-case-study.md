# DTN routing baselines — use-case-gated study

Status: literature checkpoint, 2026-08-25

This study applies the project `Use-Case Justification Gate` to established DTN/opportunistic-routing families before any further PollicinoNet routing invention.

## Executive decision

PollicinoNet should not add more proprietary routing strategies until its benchmark contains canonical baselines that solve materially different use cases.

The minimum scientific baseline set should be:

1. Direct Delivery / First Contact — trivial low-state baselines.
2. Epidemic Routing — high-delivery / high-replication reference.
3. Spray-and-Wait — bounded-copy reference.
4. PRoPHET — encounter-history / transitivity reference.
5. RAPID-like — explicit resource-allocation / objective-driven reference.
6. MaxProp later — forwarding + drop scheduling under finite buffers.

These are not features to adopt as the production routing policy. They are controls against which PollicinoNet-specific policies must be measured.

## 1. Direct Delivery / First Contact

### Use case

A network is so sparse or resource-constrained that keeping almost no routing state and creating no redundant copies is more important than delivery probability or delay.

### Baseline behavior

- Direct Delivery: keep the bundle until meeting the destination.
- First Contact: hand the single copy to the first eligible encountered relay.

### Why PollicinoNet needs this baseline

Any complex policy that cannot materially beat a single-copy zero-intelligence baseline on a target use case does not justify its extra state/control traffic.

### Gate

**Decision: ADOPT AS BENCHMARK BASELINE.**

Implementation is small and gives a necessary lower-complexity reference.

## 2. Epidemic Routing

### Use case

Delivery probability and delay matter more than radio, storage and energy cost; every useful encounter should receive a copy.

Epidemic routing is the canonical flooding-style DTN baseline. Pairwise encounters exchange summary information and replicate messages the peer lacks.

### Relationship to PollicinoNet

Current `FloodAllStrategy` is conceptually related but should not be called a canonical Epidemic implementation until it reproduces the established summary-vector / replication semantics relevant to our bundle model.

### Metrics

- delivery rate;
- delivery latency;
- transmissions / modeled wire bytes per delivered bundle;
- duplicate copies;
- storage pressure;
- LoRa control overhead.

### Gate

**Decision: ADOPT AS BENCHMARK BASELINE.**

No claim about routing efficiency is meaningful without a high-redundancy reference.

## 3. Spray-and-Wait

Spyropoulos, Psounis and Raghavendra introduced Spray-and-Wait for intermittently connected networks where flooding has high delivery probability but wastes energy and creates contention.

The protocol separates routing into:

1. `spray`: distribute a bounded number `L` of copies to distinct relays;
2. `wait`: once copy budget is exhausted, holders deliver directly to the destination.

Binary Spray-and-Wait redistributes remaining copy tokens approximately by halving them.

### Concrete PollicinoNet use case

A student-network EMERGENCY bundle needs redundancy, but unbounded LoRa replication is unacceptable because airtime, relay storage and battery are scarce.

### Hypothesis

For some generated mobility/contact families, a bounded replication budget can retain most of Flood/Epidemic delivery probability while reducing scarce-bearer traffic substantially.

### Experiment

Sweep copy budget `L`, including at least 1, 2, 4, 8, 16 and an effectively-unbounded reference.

Measure:

- delivery probability;
- EMERGENCY delivery probability;
- latency;
- LoRa source/wire bytes;
- number of bundle replicas;
- storage occupancy;
- expiry rate.

### Kill criterion

If bounded-copy routing gives no useful traffic/storage reduction at a tolerable delivery/latency cost in any target scenario family, do not retain it beyond baseline status.

### Gate

**Decision: ADOPT AS BENCHMARK BASELINE; production use remains unproven.**

## 4. PRoPHET

RFC 6693 describes PRoPHET as a probabilistic routing protocol that exploits non-random mobility. Each node maintains a destination-specific `delivery predictability` based on:

- direct encounters;
- aging when encounters do not recur;
- transitivity: if A often meets B and B often meets C, B may be a useful carrier toward C.

PRoPHET peers exchange predictability state before using it to guide forwarding.

### Concrete PollicinoNet use case

Student and commuter movement can be repetitive rather than random: home -> school -> town -> gateway patterns may recur daily. A relay that frequently reaches a gateway or a gateway-connected peer could be more valuable than a random encountered node.

### Important cost

PRoPHET is not free intelligence. It requires destination/predictability state and control exchange. On LoRa, the routing-state bytes can become as important as the data bytes saved.

### Hypothesis

Encounter-history routing improves delivery/latency per scarce-link byte when mobility has repeatable structure, but may lose to simpler bounded replication when mobility is highly random or the predictability exchange is expensive.

### Experiment

Compare at minimum:

- repeated school/commute patterns;
- random contacts;
- changing patterns / stale history;
- sparse gateways;
- many destinations.

Account PRoPHET control-plane bytes explicitly in TRC; do not compare only payload forwarding bytes.

### Kill criterion

If predictability-state exchange costs more scarce-link traffic than it saves, or if it does not improve target metrics under repeatable mobility, keep it only as literature baseline.

### Gate

**Decision: PROTOTYPE AS CANONICAL BASELINE.**

## 5. RAPID-like routing

RAPID (`DTN Routing as a Resource Allocation Problem`, SIGCOMM 2007) treats routing as explicit resource allocation. A packet is replicated when its marginal utility justifies the resource cost, and the utility depends on the administrator-selected objective such as:

- average delay;
- worst-case delay;
- fraction delivered before deadline.

RAPID also exchanges network-state information through an in-band control plane, so the benefit of smarter decisions has a communication cost.

### Concrete PollicinoNet use case

A short contact contains competing bundles:

- EMERGENCY with deadline;
- sensor update becoming stale soon;
- normal DNA/object metadata;
- large non-urgent content.

The desired outcome is not merely `deliver as many bundles eventually as possible`; it can be `maximize useful deliveries before expiry/deadline per scarce bearer byte`.

### Relationship to current Pollicino scheduler

PollicinoNet already has TTL, priority classes, logical contact budgets and fairness. RAPID is therefore a stronger scientific baseline than inventing another heuristic score. It directly tests whether our local priority/fairness decisions approximate a more explicit utility allocation.

### Experiment

Start with a deliberately reduced RAPID-like baseline rather than claiming full protocol compatibility:

- utility = delivery-before-deadline or expected delay reduction;
- explicit cost = selected source bytes / modeled wire bytes;
- no hidden oracle unless marked as such;
- control-state bytes counted separately.

### Kill criterion

If utility-driven state/control complexity does not materially improve deadline/latency outcomes compared with simple priority + Spray-and-Wait, keep RAPID only as a benchmark reference.

### Gate

**Decision: PROTOTYPE AS BENCHMARK BASELINE.**

## 6. MaxProp

MaxProp was evaluated on real vehicle DTN traces and combines:

- path-likelihood estimates from encounter history;
- prioritization of packets to transmit;
- prioritization of packets to drop;
- acknowledgments;
- a head-start for new packets;
- knowledge of previous intermediaries.

### Concrete PollicinoNet use case

A relay has finite storage and short contacts, so forwarding priority and garbage-collection/drop priority must be coordinated rather than designed independently.

### Why not implement now

Current PollicinoNet already has separate routing comparison, scheduling and relay GC. MaxProp becomes most informative after the simpler baselines above exist and after benchmark families include real buffer pressure.

### Gate

**Decision: DEFER, then add as combined routing+buffer baseline.**

## 7. Benchmark ordering

Recommended implementation order under the use-case gate:

1. Direct Delivery / First Contact;
2. canonical Epidemic;
3. Spray-and-Wait / Binary Spray-and-Wait;
4. PRoPHET;
5. reduced RAPID-like utility baseline;
6. MaxProp once finite-buffer experiments are active.

Do not add another custom routing algorithm before these baselines unless a new concrete use case cannot be represented by them.

## 8. Scientific comparison rule

Every routing result should expose at least:

- delivered bundle rate;
- EMERGENCY / deadline success rate;
- synthetic or measured latency;
- scarce-bearer source bytes;
- complete modeled wire bytes including routing/control exchange;
- replicas created;
- storage occupancy / evictions;
- expired bundles;
- CPU/RAM if stateful prediction/optimization is used;
- evidence class (synthetic, replay, physical measurement).

A routing policy is not `better` simply because it sends fewer bytes. Delivery, delay, state, energy proxy and complexity remain separate axes.

## References

- A. Vahdat, D. Becker, *Epidemic Routing for Partially Connected Ad Hoc Networks*, 2000.
- T. Spyropoulos, K. Psounis, C. S. Raghavendra, *Spray and Wait: An Efficient Routing Scheme for Intermittently Connected Mobile Networks*, ACM WDTN 2005, DOI 10.1145/1080139.1080143.
- A. Lindgren et al., *Probabilistic Routing Protocol for Intermittently Connected Networks*, RFC 6693, 2012.
- A. Balasubramanian, B. N. Levine, A. Venkataramani, *DTN Routing as a Resource Allocation Problem*, ACM SIGCOMM 2007, DOI 10.1145/1282380.1282422.
- J. Burgess et al., *MaxProp: Routing for Vehicle-Based Disruption-Tolerant Networks*, IEEE INFOCOM 2006, DOI 10.1109/INFOCOM.2006.228.
