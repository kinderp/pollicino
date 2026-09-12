# UC-PREFETCH-001 — Mobility-aware cache prepositioning

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING SCHEDULING

## Problem

The morning school phase is a rare moment when many student-carried nodes are co-located. Instead of waiting for an afternoon request and then trying to route content after the network has fragmented, PollicinoNet can use that dense phase to **pre-position a bounded set of useful objects or references on the students most likely to reach each territorial cluster later**.

The concrete question is not generic caching. It is:

> given finite node storage and scarce later contacts, which objects should be copied to which carriers *before* the topology fragments?

Examples include:

- public classroom-resource references likely to be needed that afternoon;
- fresh sensor summaries for a home cluster;
- signed configuration generations for nodes expected to be encountered later;
- compact map/service deltas for one area;
- public DNA/topic micro-information whose subscriptions are known at coarse scope;
- a small emergency-drill fixture that must already be near the right cluster before connectivity degrades.

## Actors / nodes

- school mixing hub / optional rich gateway;
- student-carried Pollicino nodes;
- pseudonymous territorial clusters;
- optional home gateways, fixed sensors or kiosks;
- policy/application layer that supplies object relevance, expiry and priority;
- Pollicino cache/store-and-forward layer.

## Messina educational scenario

Use public place names only as logical cohort labels, never as claimed radio coverage.

At 08:00, nodes from Rometta-like, Spadafora-like, Saponara-like and Villafranca-like cohorts are together at school. The school knows only coarse, privacy-safe expectations such as `carrier C usually returns to cluster-B after school`, not a student's exact home address or route.

Before the school graph disperses, the system may choose to place:

- sensor summary `S18` on two carriers likely to reach cluster-B;
- assignment reference `A22` on carriers from cluster-C;
- config generation `G44` on carriers expected to encounter three stale nodes;
- no copy of already-known or irrelevant objects.

The afternoon network then runs ordinary Pollicino store-carry-forward. The experiment asks whether deliberate morning placement improves useful delivery per stored/transmitted byte.

## Why PollicinoNet fits

PollicinoNet already has the needed lower-level ingredients:

- exact object identity and reconstruction;
- persistent caches;
- bundle TTL/hop governance;
- store-carry-forward;
- availability/reconciliation;
- routing/contact models;
- a school-mixing + territorial-carry primary use case.

This use case adds a **placement decision before separation**, not a new transport protocol.

It also creates a concrete reason to reuse future TRACE/contact-history evidence without exposing precise student locations.

## Possible bearers

- school Wi-Fi/LAN for bulk cache seeding when available;
- connected LoRa mesh for small objects/references and controlled experiments;
- BLE for local peer seeding if enabled later;
- opportunistic LoRa after school;
- physical carry between school and territorial clusters;
- Internet only as an optional rich source/sink.

No LoRa PHY change is required.

## What can be tested now in software

1. synthetic morning mixing followed by afternoon cluster separation;
2. finite carrier storage quotas;
3. objects with topic/cluster relevance, priority and expiry;
4. random placement baseline;
5. popularity-only placement baseline;
6. destination/cluster-aware greedy placement;
7. contact-history-aware placement using synthetic or later privacy-safe TRACE summaries;
8. one-copy versus bounded redundant placement;
9. carrier absence / missed school day;
10. wrong mobility prediction;
11. cache churn and eviction;
12. compare pre-positioning against pure reactive forwarding under identical contacts;
13. evaluate references separately from full micro-objects;
14. verify that already-known state is removed by reconciliation before seeding.

Start with explicit lists and simple greedy rules. Do not introduce an optimizer/ML policy unless the simple baseline fails on a concrete workload.

## Minimal measurable hypotheses

- H1: bounded pre-positioning during the dense school phase increases afternoon useful-delivery ratio compared with reactive forwarding alone.
- H2: cluster-aware placement reduces scarce-link bytes or copies compared with random/popularity-only placement at equal delivery.
- H3: coarse mobility classes are sufficient to obtain most of the benefit without exact student trajectories.
- H4: reconciliation prevents morning cache seeding from wasting capacity on objects already present in the destination cohort.

## Metrics

- useful objects delivered before deadline;
- stored bytes per carrier;
- morning seeding wire bytes by bearer;
- afternoon scarce-link bytes;
- duplicate copies;
- cache hit ratio;
- wasted seeded objects that never become useful;
- delivery gain per additional seeded byte;
- prediction error sensitivity;
- fairness across territorial clusters;
- expired objects suppressed.

## What requires real hardware

Real nodes are required before claiming:

- how many carriers are simultaneously reachable at school;
- how much can be seeded over real LoRa windows;
- real battery cost of morning seeding;
- real storage/restart behavior on the target device;
- real student encounter distributions;
- whether predicted cluster return patterns are stable enough to help.

HW-006 remains the first RF gate. The frozen first campaign remains 42-byte frames / 2 dBm, same-room -> separation -> wall -> multi-wall/floor -> outdoor.

## Privacy / security

The obvious danger is turning a cache-placement feature into mobility profiling.

Requirements:

- pseudonymous node IDs;
- coarse cluster labels, not exact addresses;
- no GPS required by the protocol;
- short retention for contact-derived placement state;
- do not infer or publish student home locations;
- application authorization still decides whether an object may be copied;
- encrypted/private objects remain subject to their own access rules;
- emergency or security-state objects require provenance/signature policies from their parent use cases.

## Implementation difficulty

**Medium.** The first useful prototype is mostly scheduling and accounting on top of existing cache/DTN primitives. Difficulty becomes high only if we prematurely add prediction/optimization machinery.

## Relationship to existing use cases

- Not `UC-CONTENT-001`: CONTENT asks how to carry a known reference/object; PREFETCH asks *which carrier should receive which object before separation*.
- Not `UC-MOBILITY-001`: MOBILITY studies repeated routes as relays; PREFETCH uses expected mobility to make a cache-placement decision.
- Not `UC-DNA-001`: DNA supplies relevance/subscriptions; PREFETCH is transport/cache scheduling after relevance is known.
- Not `UC-TRACE-001`: TRACE measures contacts; PREFETCH may consume privacy-safe TRACE-derived statistics later.

## Success / kill criterion

**Continue** if a preregistered synthetic day shows a regime where simple bounded pre-positioning materially improves deadline delivery or scarce-link efficiency over reactive forwarding at comparable storage cost.

**Defer/reject richer prediction** if random/popularity/simple cluster-greedy placement performs equivalently with much less state.

## Gate decision

**PROTOTYPE / CONTINUE.** This is a strong candidate for the real student network because the school mixing phase is already central to PollicinoNet and the experiment can begin entirely in software.

## Related precedent

Mobility-aware and proactive caching are established research areas. Examples include MobiCacher (mobility-aware caching) and context-aware proactive caching. These works motivate cache-placement questions but provide no evidence for PollicinoNet, LoRa or Messina.

- https://arxiv.org/abs/1407.1307
- https://arxiv.org/abs/1606.04236
