# PollicinoNet experimental evaluation methodology

Status: preregistration framework before the next routing/reconciliation implementation round

## Purpose

PollicinoNet should not add algorithms and then search for metrics that make them look good. For every substantial prototype, define the use case, competing baseline, workload, metrics and success/kill criteria **before** the implementation intended to support an adoption claim.

This methodology is informed by classic DTN evaluation practice (Epidemic/Spray-and-Wait/PRoPHET/RAPID), The ONE simulator/report model, Bundle Protocol resource constraints and LoRa airtime accounting.

It is not a single score. Results should expose a Pareto surface between delivery, delay, scarce-link traffic, storage, control overhead and implementation complexity.

## 1. Evidence classes

Every result must carry one evidence class.

### MODEL_SYNTHETIC

Generated topology/contact windows, logical byte budgets and synthetic bearer behavior.

May support:

- algorithm correctness;
- relative behavior under controlled assumptions;
- sensitivity analysis;
- scale/performance of software.

May not support:

- real LoRa range;
- real contact capacity;
- real packet-loss probability;
- physical energy consumption;
- claims that a strategy is superior on the future student field network.

### TRACE_DRIVEN

A deterministic replay of externally measured or established encounter/contact traces.

May support stronger mobility/contact realism, but radio behavior remains only as real as the trace fields being replayed.

### PHYSICAL_REPLAY_LOWER_BOUND

Replay derived from actual Pollicino hardware evidence where ambiguity is preserved and no missing physical observations are invented.

### PHYSICAL_MEASURED

Direct hardware campaign with explicitly measured PHY/profile, distance/environment, packet sizes, RSSI/SNR, success/failure and timing.

### FIELD

Real multi-node deployment with privacy-safe topology/contact logging and documented hardware/configuration.

Never mix evidence classes into one unlabeled aggregate.

## 2. Fair-comparison rule

Two strategies may be compared only when they receive equivalent initial conditions:

- same scenario/contact trace;
- same generated objects/messages;
- same creation times and TTL/deadlines;
- same destination set;
- same initial cache/content state;
- same storage limits;
- same bearer/contact budgets;
- same random seed where randomness is part of the algorithm;
- independent cloned mutable state per strategy.

The current routing comparator already clones peer stores, custody ledgers and fair-scheduler state. Future benchmarks must preserve this property.

## 3. Scenario pairing and seeds

Use paired experiments whenever possible.

For a family of seeds:

```text
seed 1: strategy A, B, C, D
seed 2: strategy A, B, C, D
...
seed N: strategy A, B, C, D
```

Do not compare A on one random topology with B on a different topology.

Report:

- number of seeds/scenarios;
- exact generator version/config;
- scenario tags/family;
- median and distribution, not only arithmetic mean;
- zero-delivery cases explicitly.

If parameters are tuned, separate tuning seeds/traces from evaluation seeds/traces where practical. Avoid choosing parameters after looking at the final benchmark results.

## 4. Primary network outcomes

### 4.1 Delivery ratio

```text
delivered eligible objects / eligible objects offered
```

Break down by:

- priority;
- topic/class where relevant;
- object-size regime;
- source/destination category;
- scenario family.

For deadline-sensitive cases also report:

```text
delivered before deadline / deadline-eligible objects
```

A high eventual delivery ratio can hide a uselessly late protocol.

### 4.2 Delivery latency

For each delivered object:

```text
first_complete_delivery_time - object_creation_time
```

Report at least:

- median;
- mean when useful for literature comparability;
- p90/p95 when sample count supports it;
- latency distribution/CDF;
- deadline miss rate.

Do not assign finite latency to undelivered objects. Delivery ratio and conditional latency remain separate dimensions.

### 4.3 Worst-case / tail latency

RAPID literature demonstrates that optimizing average delay, worst-case delay and deadline delivery are distinct objectives. Do not assume a strategy good for one is good for all.

When the use case is emergency/urgent traffic, predeclare which tail/deadline metric matters.

## 5. Replication and routing cost

Classic Spray-and-Wait evaluation compares delivery delay against the number of transmissions. PollicinoNet must retain that baseline and add byte-accurate accounting.

Track:

- logical forwarding actions;
- object replicas created;
- data transmissions;
- duplicate transmissions;
- transmissions per delivered object;
- source payload bytes;
- total modeled wire bytes;
- bytes by bearer;
- bytes by message/control type.

Do not report only packet count when packet sizes differ materially.

## 6. Control-plane overhead

Control traffic is not free.

Include explicitly:

- discovery/HELLO;
- routing-state exchange;
- PRoPHET predictability exchange;
- acknowledgements;
- custody receipts;
- PNB/PNC governance;
- PCM/PNA availability state;
- wanted/reference announcements;
- LoRaMesher routing/TDMA/network-formation traffic when measured or modeled explicitly.

For each experiment report both:

```text
payload/data wire bytes
control wire bytes
```

and their ratio.

A routing method that saves payload but spends more on control may still lose on a scarce link.

## 7. Pollicino Transmission Reconstruction Cost (TRC)

TRC remains the project-specific byte-accounting lens:

```text
TRC =
    discovery
  + rendezvous
  + manifest
  + reconciliation/reference/residual payload
  + acknowledgements/custody
  + retry/retransmission
  + explicitly modeled FEC/control
```

TRC must be reported per bearer and must not double-count overlapping evidence.

Keep separately:

- scarce-link TRC;
- rich-link bytes used later for final retrieval;
- local disk/cache bytes;
- compute time.

A reference mule may reduce scarce-link TRC while still causing gigabytes to move later over Wi-Fi/Internet. That is a valid result only if both costs are visible.

## 8. Airtime and energy

### 8.1 Airtime

For a fixed real or modeled LoRa PHY, compute/measure time-on-air per transmitted frame and aggregate:

- TX airtime;
- RX/listening time where known;
- airtime by control/data category;
- rolling channel occupancy/duty metric.

Semtech documents time-on-air as a function of the LoRa modem/packet configuration and provides a calculator; this is a valid **modeled airtime** source when the exact PHY and packet size are explicit.

Never infer physical useful-byte capacity solely from a synthetic contact duration.

### 8.2 Energy proxy

Before electrical measurement, the only permitted energy result is explicitly labelled **MODELED ENERGY PROXY**.

Example:

```text
proxy charge ~= TX_time * datasheet_TX_current
              + RX_time * datasheet_RX_current
```

This ignores MCU, regulator, display, flash and board-level effects unless modeled separately; therefore it is not a measured battery-life claim.

For the SX1276, use the Semtech datasheet/product values associated with the actual power path/profile being modeled. Do not assume a single current value for every TX power/configuration.

Actual node energy/battery claims require instrumentation in a later physical campaign.

## 9. Storage pressure

DTN performance depends on finite relay storage.

Track:

- mean and peak occupied bytes per node;
- object/chunk count;
- evictions by reason;
- expired bytes reclaimed;
- pinned bytes;
- shared-reference savings;
- time an object spends buffered;
- undelivered objects lost to quota pressure.

Compare routing schemes under identical storage limits. Unlimited buffers can hide replication pathologies.

## 10. Fairness and priority

Track delivery/latency by priority class:

- BULK;
- NORMAL;
- HIGH;
- EMERGENCY.

Also track:

- starvation/rescue events;
- oldest waiting age;
- bytes delivered per priority;
- low-priority delivery collapse under emergency load.

An emergency policy must not be evaluated only on total delivery ratio.

## 11. Exactness and integrity

For EXACT objects:

```text
SHA256(reconstructed) == SHA256(authoritative object)
```

Track:

- exact reconstructions;
- corrupt/incomplete reconstructions;
- reconciliation false success/failure;
- manifest/chunk validation failures.

Compact reconciliation or routing optimizations may reduce traffic but must never weaken the final exactness oracle.

Checksums are corruption detection, not authentication/security evidence.

## 12. Reconciliation-specific methodology

For PNA/PNA2 experiments vary independently:

- manifest chunk count N within current PCM1 limits;
- missing/difference count d;
- difference density d/N;
- random vs clustered/range-like missing indices;
- complete-source -> partial-receiver;
- partial-relay <-> partial-relay;
- known vs unknown difference cardinality;
- one-way vs bidirectional contact.

Measure:

- encoded availability/reconciliation bytes;
- rounds/messages required;
- CPU time;
- peak RAM;
- decode failure probability;
- fallback/retry bytes;
- final exactness.

Compare simplest codecs first:

```text
PNA1 bitmap
sparse uint16 index list
range/RLE
compressed bitmap
minisketch/PinSketch
IBLT/rateless only if justified
```

Do not select one codec globally if a small regime-selection rule dominates it.

## 13. Content/reference-mule methodology

For `UC-CONTENT-001`, separate these outcomes:

- reference accepted/cached;
- reference eventually resolved;
- object eventually retrieved;
- exact object verified;
- reference expired/unresolvable;
- provider became unavailable;
- direct chunk transfer used instead.

Report:

```text
scarce-link bytes before home/gateway
rich-path bytes after home/gateway
time to eventual retrieval
```

Compare opaque existing references (URL/magnet/CID) against any proposed typed Pollicino representation. A new representation must beat the existing opaque form in a real regime before adoption.

## 14. School-hub / student-data-mule methodology

For `UC-DNA-001`, generate privacy-safe abstract phases:

```text
morning: dense school hub
transition: students physically carry state
afternoon: sparse territorial clusters
later: optional gateway/home connectivity
```

Compare with and without the school mixing phase while holding the afternoon network constant.

Track:

- additional territorial deliveries attributable to morning mixing;
- bytes exchanged during the dense phase;
- topic-filtered candidate reduction;
- reconciliation savings after filtering;
- number of physical carries;
- stale/expired information suppressed.

Do not encode exact student homes or stable personal identities in synthetic/field datasets.

## 15. Mobility/contact families

Do not rely on one random mobility model.

At minimum retain distinct families such as:

- sparse random contacts;
- dense school hub -> dispersed clusters;
- data-mule bridge between disconnected clusters;
- repeated habitual encounters suitable for PRoPHET;
- adversarial/non-predictive encounters where PRoPHET should not gain an unfair assumption;
- gateway-scarce network;
- emergency burst load;
- bulk + emergency contention;
- connected-mesh periods embedded inside disconnected DTN periods.

This is necessary because PRoPHET specifically relies on non-random/repeated mobility; evaluating it only on a mobility pattern tailored to its assumptions would be misleading.

## 16. Baseline matrix

Before custom routing claims, include where applicable:

```text
Direct Delivery
First Contact / simple single-copy
Epidemic
Binary Spray-and-Wait
PRoPHET
RAPID-like utility allocation
```

Additional baselines are added only when justified by the use case.

For LoRa connected segments compare where applicable:

```text
raw direct LoRa
FreakWAN-style flood baseline
LoRaMesher connected mesh
Pollicino DTN overlay
```

Do not compare unlike layers without stating what each system is responsible for.

## 17. The ONE interoperability target

The ONE is an established DTN/opportunistic simulator supporting mobility traces, routing protocols and reports including message-delivery statistics. PollicinoNet should eventually import/export an encounter/contact trace representation sufficient to reproduce at least:

- node IDs;
- contact start/end;
- directional/undirected contact semantics;
- optional link rate/capacity when the source trace contains it;
- message/object creation/destination/time information where appropriate.

The goal is not to replace The ONE. The goal is to allow published/standard scenarios to be replayed through Pollicino's object/reconciliation accounting and allow our generated contact families to be exported for independent comparison.

## 18. Reporting format

Every benchmark report should identify:

```text
experiment_id
code_commit
scenario_generator_version
scenario/config hash
seed(s)
strategy + parameters
object/workload definition
bearer profiles
evidence class
hardware/PHY if physical
start/end definition
all metric definitions
known limitations
```

Never publish only a chart without the configuration needed to reproduce it.

## 19. Adoption discipline

Before a prototype becomes stable architecture, summarize:

```text
use case
baseline
measurable hypothesis
experiment matrix
evidence class
result distributions
complexity/security cost
success/kill criterion outcome
ADOPT / DEFER / REJECT
```

A statistically or numerically better result is not sufficient if the improvement is irrelevant to an actual use case or is purchased with disproportionate implementation/security complexity.

## 20. Immediate implication

The next routing implementation round should begin only after the benchmark harness can account for:

1. delivery ratio + deadline success;
2. conditional latency distribution;
3. transmissions/replicas;
4. data vs control wire bytes;
5. per-bearer TRC;
6. storage pressure;
7. priority/fairness outcomes;
8. exactness;
9. evidence class.

The next PNA2 round should use the reconciliation-specific matrix above and test simple codecs before sketch structures.

The next physical LoRa performance claim remains blocked by **HW-006**.

## References used for methodology

- Spyropoulos, Psounis, Raghavendra, *Spray and Wait: An Efficient Routing Scheme for Intermittently Connected Mobile Networks*, ACM WDTN 2005, DOI 10.1145/1080139.1080143.
- IETF RFC 6693, *Probabilistic Routing Protocol for Intermittently Connected Networks (PRoPHET)*.
- Balasubramanian, Levine, Venkataramani, *DTN Routing as a Resource Allocation Problem (RAPID)*, ACM SIGCOMM 2007.
- Keränen et al., *The ONE / Opportunistic Network Environment* simulator and `MessageStatsReport` tooling.
- IETF RFC 9171, *Bundle Protocol Version 7*.
- Semtech SX1276 product/datasheet material and LoRa Calculator for explicit PHY time-on-air/current modeling.
