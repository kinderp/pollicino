# UC-MOBILITY-001 — Scheduled vehicle / commuter relay between territorial clusters

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Problem

Student movement is useful but partly unpredictable. Some mobile nodes instead follow **repeated routes**: school buses, public transport, teacher/parent commutes, service vehicles or a deliberately operated test vehicle.

A repeated route can become a predictable store-carry-forward bridge between disconnected local clusters and a school/Internet gateway without requiring a permanent radio path between them.

This use case does not assume that any existing bus company or public vehicle will host hardware. The first experiments can use synthetic schedules and later a privately controlled supervised vehicle.

## Actors / nodes

- mobile vehicle/commuter relay;
- fixed school gateway;
- territorial fixed nodes;
- student-carried nodes encountered near the route;
- optional home/Internet gateways.

## Messina educational scenario

Model a repeated morning/afternoon route connecting logical clusters inspired by towns in the province, for example:

```text
cluster Rometta
      |
      v
cluster Spadafora
      |
      v
school hub
      |
      v
cluster Villafranca
```

The model represents a **contact schedule**, not measured LoRa coverage along roads. Each stop/segment can create an encounter window with an explicit synthetic byte budget.

## Why PollicinoNet fits

A scheduled mobile relay creates a useful middle ground between:

- purely opportunistic routing with no future knowledge; and
- a permanently connected routed mesh.

PollicinoNet already has bundles, custody, contact windows, priorities, multiple bearers and synthetic scenario families. This use case lets us test whether modest schedule knowledge can improve delivery without inventing a general geographic routing protocol.

## Possible bearers

- LoRa for compact exchange during passing/stop contacts;
- BLE for close-range rendezvous;
- Wi-Fi at a depot/school/home for large synchronization;
- Internet at gateways;
- physical vehicle movement as the dominant carry mechanism.

## What can be tested now in software

Immediately testable:

1. periodic contact traces with jitter and missed stops;
2. generic Direct Delivery/Epidemic/Spray-and-Wait/PRoPHET baselines;
3. a simple schedule-aware policy that knows only the next expected gateway/cluster encounter;
4. high-priority versus bulk bundles;
5. content/reference mule and sensor workloads on the same route;
6. resilience when the scheduled relay misses one complete cycle.

This is a strong use case for `TRACE_DRIVEN` experiments later, because an observed timetable/contact trace can replace synthetic contact generation without changing the object layer.

## What requires real hardware

Real hardware is required before claiming:

- that a moving vehicle can actually exchange useful data at a given speed/location;
- contact duration near a stop or along a road;
- antenna placement performance;
- coverage through vehicle body/windows;
- reliable scheduled contact budgets;
- any geographic route coverage.

No hardware should be mounted on a public/shared vehicle without owner/operator permission and a safe installation.

## Privacy / security

A repeated mobile node can become a tracking beacon if designed badly.

Requirements:

- rotating/scoped node identity;
- publish logical route/cluster IDs rather than precise passenger location;
- do not store student travel histories by default;
- avoid exact home-stop association in experiments;
- authenticate privileged gateway/relay roles;
- bound retained contact metadata.

## Implementation difficulty

**Medium.** Synthetic route generation and schedule-aware scoring are straightforward. Real deployment is harder because of mobility, mounting, power and privacy.

## Minimal measurable hypotheses

- H1: repeated-route knowledge reduces delivery latency or replication bytes compared with topology-agnostic routing under the same contact trace.
- H2: one predictable mobile bridge can materially improve delivery between otherwise disconnected territorial clusters in some synthetic regimes.
- H3: schedule-aware forwarding remains useful under realistic jitter/missed-contact perturbations rather than only with a perfect oracle timetable.

## Metrics

- delivery ratio;
- latency and delivery cycles;
- deadline success where applicable;
- forwarding copies;
- wire/TRC bytes;
- storage time on mobile relay;
- missed-contact sensitivity;
- benefit versus simple Spray-and-Wait;
- privacy/contact-metadata exposure.

## Gate decision

**PROTOTYPE.** It is concrete, distinct from random student mobility and especially relevant to a territorial pilot. Start with a deliberately simple schedule-aware baseline; do not promote a new routing family unless it beats canonical baselines across perturbed schedules.

## Related research precedent

Vehicular DTNs explicitly use store-carry-forward where sparse vehicle contacts prevent continuous end-to-end paths: https://doi.org/10.1016/j.comcom.2014.03.024 . DakNet is an older but highly relevant example of asynchronous connectivity using physical transport plus short wireless contacts: https://www.media.mit.edu/publications/daknet-rethinking-connectivity-in-developing-nations/ .