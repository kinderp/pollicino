# UC-NEED-001 — Offline need/offer resource matching

Status: PROTOTYPE / EMERGENCY-ADJACENT, software-first and non-operational until governance/security are independently validated

## Problem

During a disruption, different groups can know different pieces of the local resource picture. One point may need batteries, water, blankets or a sensor kit while another point has spare stock, but neither has continuous connectivity to a central coordinator.

A bulletin can say that a need exists. A task board can assign work. A service directory can advertise a capability. This use case asks a different question:

> can small, expiring **need** and **offer** records be ferried across disconnected clusters and reconciled into partial or complete matches without double-counting scarce resources?

This is distinct from `UC-ASSET-001`, which concerns durable reservable assets, and from `UC-TASK-001`, which concerns work claims/leases. NEED models consumable quantities and partial fulfillment under stale state.

## Actors / nodes

- school/teacher coordinator in the first synthetic pilot;
- pseudonymous logical collection/distribution points;
- student-carried relay nodes;
- optional fixed school/home gateways;
- later, only after separate governance, authorized civil-protection/community actors;
- matching/audit tool that keeps human approval explicit.

## Why PollicinoNet fits

Need/offer records are compact, time-sensitive and naturally tolerate delayed delivery better than large logistics databases.

A minimal application record might contain:

```text
record_id
kind = NEED | OFFER
resource_code
quantity
unit
coarse_area
priority
issued_at
expires_at
remaining_quantity
authority/provenance
```

Pollicino's exact object identity, duplicate suppression, custody, TTL/hop governance and store-carry-forward can move those records while a higher layer decides whether a proposed match is acceptable.

The network core should not autonomously allocate real emergency resources.

## Possible bearers

- LoRa: compact needs/offers, partial-fulfillment receipts and cancellation generations;
- BLE/NFC/QR: local handoff at a supervised collection point;
- Wi-Fi/LAN/Internet: full inventory/dashboard and authoritative coordination;
- physical carry: student nodes transport state between school and logical territorial clusters.

## What we can test immediately in software

Use synthetic resources only, for example colored tokens or virtual stock:

```text
cluster A: NEED 12 x RESOURCE-WATER-DEMO
cluster B: OFFER 5
cluster C: OFFER 10
cluster D: NEED 3
```

Compare:

1. central-only coordinator that sees records only when they reach school;
2. local exact-code matching with quantity/expiry;
3. partial fulfillment with signed receipt generations;
4. optional simple priority/deadline ordering.

Inject:

- two relays carrying the same offer;
- partial fulfillment followed by stale replay of the original quantity;
- cancelled need that propagates late;
- offer expiration;
- partition where two groups believe they can claim the same scarce stock;
- delayed receipt after physical delivery;
- conflicting authoritative corrections.

Metrics:

- fraction of synthetic need quantity satisfied before expiry;
- duplicate/over-commit attempts;
- stale matches suppressed;
- scarce-link bytes per useful matched unit;
- time from publication to proposed match;
- number of human approvals required;
- convergence time for remaining quantities.

Start with exact resource codes; do not add semantic/LLM matching until simple matching demonstrably fails.

## Messina student-network scenario

A safe educational exercise can model four logical areas such as `Rometta-like`, `Spadafora-like`, `Saponara-like` and `Villafranca-like` with students carrying only synthetic inventory records.

For example, teams may exchange cardboard tokens representing batteries, water packs, blankets or robot-kit parts. The physical tokens make partial fulfillment visible, while Pollicino carries the delayed digital state.

No real household needs, medical requirements or emergency locations should be used in the first field experiments.

## What requires real hardware

After HW-006 and an application-specific governance gate:

- measured time for needs/offers/receipts to propagate through real student contacts;
- actual conflict rate under intermittent connectivity;
- supervised physical-token/item handoff;
- embedded signature/persistence cost;
- behavior across reboot/power loss while a partial fulfillment is pending.

Any real civil-protection/logistics integration requires authoritative actors, operational procedures and independent validation far beyond a student prototype.

## Privacy and security

- use synthetic resources and coarse logical areas first;
- avoid household addresses, health needs, names or vulnerable-person data;
- authenticate authoritative corrections, cancellations and fulfillment receipts;
- prevent stale replay from recreating consumed stock;
- treat priority as application policy, not an invitation to infer personal vulnerability;
- keep human approval in the loop for any real allocation;
- log provenance so a receiver can distinguish an offer from hearsay.

## Difficulty

**Medium** for synthetic matching; **high** for any operational emergency use because trust, stale state and real-world allocation dominate the problem.

## Success / kill criteria

Continue if simple quantity/expiry reconciliation materially reduces double counting and improves synthetic fulfillment under partitions with modest wire cost.

Reject automatic matching/allocation if human review is required for most cases or if stale-state conflicts cannot be bounded safely.

## Related-work note

Humanitarian systems and research have long treated matching needs with offers as a concrete coordination problem. Examples include NeedsList and NARMADA-style need/availability matching. PollicinoNet's research angle is not inventing resource matching; it is testing whether **small matching state can remain useful when it must travel by store-carry-forward and human mobility**.

## Physical evidence boundary

This use case authorizes no operational emergency claim. Real delivery latency, reachable collection points and usable bytes per contact remain behind HW-006 and separate emergency-governance/security validation. The frozen LoRa PHY remains unchanged.