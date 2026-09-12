# UC-CORROBORATE-001 — Multi-source event corroboration

Status: PROTOTYPE / emergency-adjacent research

## Problem

A single sensor, observer or relay can be wrong. A rain gauge can fail, a student observation can be mistaken, a node can replay an old event, or one local source can be spoofed. For emergency-adjacent systems this makes "one report -> one alert" a dangerous design.

This use case studies a narrower and safer problem: carry small signed observations through PollicinoNet and decide when **independent sources corroborate the same event**. The output is a research-level event state such as `UNCONFIRMED`, `CORROBORATED` or `STALE`; it is not an operational civil-protection alert.

Messina is a useful scenario domain because official municipal notices regularly include meteo, hydrogeological and hydraulic risk. That makes synthetic rain/stream-level/landslide-indicator exercises locally meaningful without claiming that PollicinoNet is suitable for real warning operations.

## Actors / nodes

- fixed sensor nodes or synthetic sensor fixtures;
- student-carried Pollicino nodes acting as store-and-forward relays;
- optional human-observation clients using coarse area labels;
- school mixing hub;
- optional home/school Wi-Fi gateway;
- research event aggregator;
- later, only under a separate governance agreement, an external authoritative system as a read-only source/sink.

## Why PollicinoNet fits

The interesting part is not raw sensing. It is that evidence may arrive out of order, through different carriers, after long partitions, with duplicate copies and different freshness.

PollicinoNet already has the right primitives to study this:

- exact small objects;
- store-carry-forward;
- TTL/hop governance;
- provenance/custody state;
- duplicate suppression;
- application usefulness deadlines distinct from transport TTL;
- DNA/DNATrace-style topic/geo relevance as an optional upper layer.

The key new workload is **corroboration across independent delayed evidence**, not another sensor-ferry benchmark.

## Possible bearers

- LoRa: compact event observations, signatures/hashes, acknowledgements and corroboration state;
- BLE: nearby sensor-to-student or phone-to-board handoff;
- Wi-Fi/LAN: raw sensor logs and richer diagnostics;
- Internet: optional retrieval of authoritative public bulletins or upload of experiment results;
- physical carry: students moving observations between territorial clusters and the school hub.

## Minimal object shape

A software fixture can start with fields such as:

```text
event_type
coarse_area
source_pseudonym
generation
observed_at / time_uncertainty
value_or_category
confidence_class
expires_at
provenance_hash
signature_fixture
```

No production wire format is authorized by this use case.

## What we can test immediately in software

Use synthetic clusters labelled, for example, Rometta-like, Spadafora-like, Saponara-like and school-hub. The labels are topology names only, never RF claims.

Experiments:

1. 3 independent sources report the same event; one report is delayed.
2. 1 source reports a false event and the others remain normal.
3. an old valid event is replayed after its usefulness deadline;
4. two sources are correlated copies of the same upstream sensor and must not count as independent witnesses;
5. student mobility carries observations from different clusters to the school mixing hub;
6. compare simple threshold rules such as `2-of-3 independent fresh sources` against naive `first report wins`;
7. measure event-detection delay, bytes, duplicate traffic, stale evidence, false-corroboration rate in the synthetic fixture, and provenance completeness.

The simplest baseline is deliberately simple: no probabilistic fusion, no ML, no Byzantine consensus.

## What requires real hardware

After HW-006 only:

- real LoRa delivery timing for the chosen observation size;
- real sensor sampling and failure behavior;
- real battery/energy cost;
- real delay from fixed sensor -> student mule -> school hub;
- real contact diversity between independent carriers;
- controlled false-trigger experiments using harmless test sensors.

Actual flood, landslide, fire or civil-protection deployment requires a separate safety/security/authority process and cannot be inferred from a school pilot.

## Privacy and security

- no precise student home coordinates;
- coarse geographic scopes only;
- rotating/pseudonymous node identifiers where possible;
- signed or otherwise authenticated test observations before any trust claim;
- anti-replay generation/expiry checks;
- provenance must distinguish independent sources from replicated copies;
- no student identity embedded in event objects;
- no operational emergency alert may be generated from this prototype.

## Difficulty

**Medium-high.** The transport pieces already exist. The hard part is defining independence, freshness and trust without inventing unnecessary distributed-consensus machinery.

## Success / kill criteria

Continue if a small, explainable corroboration rule materially reduces false event promotion or stale-event promotion compared with `first report wins`, while keeping scarce-link overhead bounded.

Defer richer fusion/consensus if simple signed independent-source thresholds solve the synthetic and later measured pilot workloads.

## Physical evidence boundary

Nothing here changes the frozen LoRa PHY. No range, NLOS, capacity, energy or real-event detection claim is allowed before measured evidence. HW-006 remains the first physical gate at 42-byte frames / 2 dBm using the frozen progression.