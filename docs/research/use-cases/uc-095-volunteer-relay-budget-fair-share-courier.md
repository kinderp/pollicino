# UC-095 — Volunteer Relay Budget and Fair-Share Courier

## Idea

Treat student-owned or voluntarily hosted PollicinoNet nodes as **bounded shared resources**, not free infrastructure. Each relay advertises a small local participation policy such as maximum storage, bytes per period, accepted traffic classes and battery reserve. The forwarding scheduler then tries to make useful progress without exhausting one generous node or starving lower-priority flows forever.

## Problem solved

In a real network distributed across students, relay resources are unequal:

- one node may be mains-powered, another battery-powered;
- one student may consent to 100 MB of cached course data, another only a few MB;
- some nodes may accept public school content but not private mail;
- popular routes may overload the same few students;
- emergency/drill traffic may temporarily deserve priority, but normal traffic must recover afterward.

If PollicinoNet ignores these limits, the network can become unfair, waste energy/storage, and discourage participation.

## Actors / nodes

- volunteer relay/store-and-forward nodes;
- message/content producers;
- recipients;
- school policy coordinator for optional defaults;
- network observatory/collector for aggregate fairness measurements.

## Why PollicinoNet fits

Store-carry-forward already requires buffer and scheduling decisions. Making **consent, budget and fairness explicit inputs** is more realistic than assuming every contact can carry everything.

- **DISCOVERY:** relay can currently carry traffic class X under policy profile P;
- **EXACT:** local budget epoch, queue class, item size/hash, TTL/deadline, privacy class and per-flow accounting counters;
- **SEMANTIC:** labels such as `budget-low`, `temporarily-refusing`, or `fair-share-deferred` are local policy outcomes, not global truth.

Nothing changes the frozen LoRa PHY. This is an application/queueing policy above the bearer.

## Possible bearers

- **LoRa:** compact capability/budget class, queue pressure, refusal reason and transfer intent;
- **BLE:** nearby negotiation and small transfers;
- **Wi-Fi/LAN:** bulk data transfer once both sides accept the budget;
- **Internet:** optional fast path that may bypass scarce relay resources;
- **physical transport:** the student device carries accepted cached items between contacts.

## What we can test now in software

Model relays with different profiles:

```text
relay_policy_id
max_buffer_bytes
max_forward_bytes_per_day
battery_reserve_class
accepted_traffic_classes[]
per_flow_cap
priority_rules
privacy_rules
```

Compare scheduling strategies such as:

- greedy highest-priority only;
- FIFO;
- weighted fair share;
- per-source/per-topic quotas;
- deadline-aware plus minimum service for ordinary traffic;
- emergency/drill burst with bounded recovery to normal fairness.

Inject:

- one highly connected relay with a tiny budget;
- several lightly connected relays with spare storage;
- abusive producer flooding many small messages;
- large content that would monopolize one contact;
- private traffic rejected by policy;
- policy changes while items are already queued;
- relay reboot and accounting-epoch rollover.

Useful metrics include delivery ratio by traffic class, bytes relayed per node, maximum share carried by one node, starvation time, rejected bytes, buffer occupancy, budget violations and Jain-style fairness indices where appropriate.

The important rule is:

> A relay saying “no” or “not now” is a valid network state, not a failure to be routed around by violating its policy.

## What requires real hardware

A first field test needs 5–8 boards with deliberately different artificial budgets. Keep all devices on bench power at first so energy claims are not confounded by unknown batteries.

Generate the same traffic mix through repeated controlled contacts, then compare how many bytes each node actually stores/forwards under FIFO versus fair-share policies.

Only after that should we repeat with battery-powered nodes and measure real current/energy if energy budgeting becomes part of the claim.

## Messina teaching scenario

Use student nodes across school/Messina, Villafranca, Rometta/Venetico and Spadafora. Some nodes are designated `small-volunteer`, some `normal`, and one school node `mains-cache`.

A useful experiment is to publish three simultaneous flows:

```text
A: small private mailbox messages
B: course/document updates
C: large public AI/model artifact
```

Then verify whether C can consume every contact or whether A/B still make bounded progress. The class can inspect fairness versus efficiency trade-offs using real contact traces from UC-008.

## Privacy / security

- participation budgets are opt-in and locally enforceable;
- do not broadcast exact battery percentage if that creates unwanted device/user profiling; coarse classes are usually enough;
- do not expose which private conversations a relay is carrying;
- authenticate traffic class and item size metadata used for policy decisions;
- rate-limit producers so they cannot evade quotas with many identities/items;
- separate network fairness from social scoring: no public leaderboard of “good/bad students”;
- no monetary or punitive incentive scheme in the initial experiment;
- keep accounting epoch-scoped and minimize retained per-user metadata.

## Difficulty

**Medium-high.** Scheduling algorithms are manageable; defining fair behavior without leaking metadata or overriding volunteer consent is the more important design challenge.

## Why this is distinct from nearby use cases

- **UC-045:** decides what a mobile harvester collects first during a short contact; UC-095 governs long-lived relay participation budgets and fairness across flows/nodes.
- **UC-073:** decides where a courier should go next; UC-095 decides how much/which traffic a contacted volunteer relay is willing to carry.
- **UC-074:** adapts sensor sampling duty cycle; UC-095 manages forwarding/storage resources.
- **UC-015:** reconciles application resources/reservations; UC-095 is network participation policy and queue fairness.

## Research / implementation signal

DTN literature has long treated buffer space, energy and bandwidth as scarce resources, with scheduling/drop policy affecting delivery and overhead. Recent opportunistic-network work in 2026 continues to model routing under energy and buffer constraints. PollicinoNet's specific contribution here would be to make a volunteer node's local consent/budget an explicit hard constraint and then compare fair scheduling policies on real student contact traces.

References:

- https://www.benthamscience.com/article/133728
- https://ieeexplore.ieee.org/document/11397273/
