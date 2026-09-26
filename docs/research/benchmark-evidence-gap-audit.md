# Routing benchmark evidence gap audit

Status: post-methodology checkpoint

This audit compares the current synthetic routing benchmark with `experimental-evaluation-methodology.md` and records which metrics are already supported, which were added without protocol changes, and which remain deliberately deferred.

## Already present before this checkpoint

The benchmark already reported:

- scenario count;
- offered bundle count;
- delivered bundle count and delivery rate;
- EMERGENCY offered/delivered count and rate;
- expired-undelivered count;
- synthetic first-delivery latency samples;
- mean/median delivery latency;
- logical source bytes;
- total wire bytes;
- skipped windows;
- per-bearer logical/wire use;
- isolated cloned state between strategies.

This was already enough to avoid a hidden global winner score and expose basic delivery/traffic tradeoffs.

## Added in this checkpoint

These metrics were derivable from existing reports and therefore required no new wire protocol or forwarding semantics:

- explicit benchmark evidence class: `model_synthetic`;
- forwarding-decision count;
- transferred-chunk count;
- fairness rescue count;
- primary content-payload wire bytes;
- primary protocol-metadata wire bytes;
- primary ACK wire bytes;
- retransmission data wire bytes;
- retransmission ACK wire bytes;
- same classification per bearer.

The classified byte categories are required to sum exactly to the existing `total_wire_bytes`; tests fail closed if they do not.

### Classification boundary

`payload_primary_wire_bytes` is the primary wire cost of chunk payload packets.

`protocol_metadata_primary_wire_bytes` includes existing PNB1/PNC1 governance plus PCM1 manifest and PNA1 availability primary data.

ACKs are separate.

Retransmission data is intentionally **not** forced into payload-vs-metadata subcategories because the current lower report aggregates retry data across manifest, availability, payload and governance transfers. Calling all retransmission data “payload” or “control” would invent evidence.

A later need for retry subtype accounting must justify preserving per-transfer-category retry breakdown at a lower layer.

## Validated fairness aggregation

A benchmark test now contains two bundles competing under a one-bundle/64-byte contact budget:

1. a HIGH bundle is served in the first encounter;
2. a NORMAL bundle is observed but deferred;
3. after the configured starvation interval, the NORMAL bundle is served through the fairness rescue path.

The aggregate benchmark records one rescue event. This confirms the metric is not permanently zero or inferred indirectly.

## Deliberately deferred gaps

### Application deadline success

Current bundles have protocol TTL/expiry, but there is no separate application deadline field in `ScheduledBundle`/benchmark workload.

RAPID-style experiments may need a distinction between:

```text
protocol expiry
vs
application usefulness deadline
```

Do not silently equate them.

**Decision: DEFER until a concrete deadline-sensitive use case defines semantics.**

Likely use cases:

- DNA micro-information that becomes useless before its protocol retention lifetime;
- emergency/status information with a usefulness deadline;
- content/reference requests where late delivery has reduced utility.

### Storage pressure inside routing comparison

Relay quota/retention/GC exists separately, but the current routing comparator clones in-memory peer stores and does not drive `RelayStorageCatalog` occupancy/eviction during the strategy run.

Therefore the benchmark cannot yet honestly report:

- peak occupied relay bytes;
- routing-induced evictions;
- undelivered losses caused by quota pressure;
- replica pressure per strategy.

**Decision: DEFER to a dedicated benchmark-integration experiment.**

This is justified before MaxProp/RAPID-style buffer-pressure claims, not before the simpler routing baselines.

### Mode/bearer transition integrity

`UC-DNA-001` and `UC-CONTENT-001` both require state to survive transitions between dense/connected, opportunistic and rich-network phases.

The scenario generator can already represent different bearer windows, but there is not yet a formal runtime mode-transition report.

**Decision: PROTOTYPE later, after the connected/off-grid bearer-runtime abstraction itself passes its architecture gate.**

### Rich-path bytes after reference resolution

The routing benchmark measures its own modeled network traffic. `UC-CONTENT-001` additionally requires later home/Internet/NAS retrieval bytes to be reported separately.

Do not add those bytes to scarce-link TRC.

**Decision: implement in the content/reference resolver experiment, not generic routing benchmark.**

### Airtime / energy

The deterministic scarce-link profile can model transmission timing, but routing benchmark totals currently expose bytes rather than aggregate airtime categories.

Adding modeled airtime is reasonable only when an explicit PHY profile is part of the experiment. Electrical energy remains a modeled proxy until hardware instrumentation exists.

**Decision: add model airtime after canonical routing baselines if required for a LoRa-specific comparison; real energy remains physical-gated.**

## Readiness for canonical routing baselines

The benchmark is now ready for a first canonical routing round comparing algorithms on:

- delivery;
- conditional latency;
- forwarding/replication activity;
- exact byte cost;
- protocol overhead;
- retries;
- per-bearer usage;
- fairness interactions.

The next baseline implementation should therefore start with the simplest scientifically useful sequence:

```text
Direct Delivery / single-copy baseline
Epidemic
Binary Spray-and-Wait
PRoPHET
RAPID-like only after deadline/utility semantics are explicitly selected
```

RAPID should not be implemented as a name-only approximation: its use case is intentional utility/resource allocation, so the utility metric must be preregistered first.

## Validation

The benchmark-evidence change was validated with:

- complete project test suite;
- targeted `tests/test_net_routing_benchmark.py`;
- non-overlapping wire-classification equality checks;
- non-zero fairness-rescue aggregation fixture.

No H2/PHY or wire-format change was introduced.
