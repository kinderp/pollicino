# UC-108 — Queue-Pressure Backpressure and Admission-Control Courier

## Idea

Let PollicinoNet relays advertise **compact queue-pressure state** so upstream nodes can slow, defer, reroute or reject new work before scarce relay buffers overflow.

This is not TCP-style end-to-end congestion control and it does not modify the frozen LoRa PHY. It is an application/store-and-forward policy for a network where a relay may stay congested for minutes or hours before the next useful contact.

## Problem solved

A real student network can create backlog faster than some relays can drain it:

- several students publish large course/model updates at once;
- one popular bridge between two communities becomes a bottleneck;
- a relay has little free storage under UC-095;
- an epidemic/groupcast campaign creates too many copies;
- a sink is temporarily unreachable and queues keep growing;
- urgent small messages are trapped behind large low-priority objects.

Without an explicit pressure signal, nodes may continue accepting traffic until they are forced to drop it after spending storage, airtime and contact time.

## Actors / nodes

- producers/requesters generating bundles or transfer jobs;
- volunteer relay/store-and-forward nodes;
- bottleneck relay(s) between intermittently connected groups;
- destinations/sinks;
- optional UC-008/UC-098 observatory for later analysis;
- optional policy coordinator providing safe defaults while each relay keeps local authority.

## Why PollicinoNet fits

Store-carry-forward already makes queue state persistent. A compact, coarse pressure signal can therefore be useful even when the next hop is not continuously connected.

- **DISCOVERY:** pressure class such as `LOW / MEDIUM / HIGH / REFUSE`, accepted traffic classes and approximate free-buffer class;
- **EXACT:** pressure epoch, relay pseudonym, policy ID, queue class, item size, expiry/deadline and admission decision bound to one transfer intent;
- **SEMANTIC:** human labels such as `bridge-congested` or `defer-large-public`, never a substitute for exact policy fields.

LoRa carries the small pressure/admission state. Bulk objects continue to use BLE/Wi-Fi/LAN/Internet or physical carry. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** pressure class, admission/refusal reason, queue summary, transfer intent, expiry and small control acknowledgements;
- **BLE:** nearby queue negotiation and small transfers;
- **Wi-Fi/LAN:** admitted bulk transfer;
- **Internet:** optional fast path that drains backlog when available;
- **physical transport:** student/teacher devices carry already-admitted objects between islands.

## What we can test now in software

Extend the contact/queue simulator with finite relay buffers and persistent backlog.

Compare:

1. no pressure feedback;
2. hard admission threshold;
3. hysteresis (`HIGH` does not immediately oscillate back to `LOW`);
4. class-aware admission that protects small/urgent traffic;
5. pressure-aware rerouting when another relay exists;
6. pressure plus UC-095 fair-share budgets;
7. conservative mode that returns `UNKNOWN` when queue state is stale.

Inject:

- a burst of large AI artifacts;
- a temporarily unreachable sink;
- stale pressure advertisements;
- pressure oscillation;
- a lying/misconfigured node advertising low pressure while full;
- one highly connected bottleneck relay;
- a producer that ignores `REFUSE` and retries aggressively;
- emergency/drill traffic mixed with ordinary traffic;
- duplicated groupcast copies from UC-102.

Useful software metrics include buffer overflow count, dropped objects, completed objects, admission refusals, starvation time, backlog age, duplicate bytes and fairness. These are queueing/simulation metrics only; no physical radio improvement is claimed.

A key invariant is:

> `REFUSE` or `DEFER` is a valid flow-control outcome. A producer must not bypass a relay's local resource policy merely because another copy of the request arrives later.

## What requires real hardware

A first field experiment needs:

- 6–10 boards;
- at least one deliberately small relay buffer;
- two source groups and one constrained bridge relay;
- a bounded scripted workload containing small and large objects;
- repeated trials with pressure feedback disabled and enabled;
- measured queue occupancy, accepted/rejected objects, completed deliveries and real contact durations.

Energy effects require separate current/energy instrumentation. Range/PDR improvements must not be inferred from queue behavior.

## Messina teaching scenario

Create two or three coarse islands such as `Messina/Villafranca` and `Rometta/Venetico/Spadafora`, joined for part of the day by one student-carried relay with a deliberately small storage budget.

Publish simultaneously:

```text
A: small private mailbox messages
B: normal course updates
C: one large public model/dataset artifact
```

Students compare what happens when every source keeps pushing versus when the bridge advertises `HIGH` pressure and temporarily refuses C while A/B continue. UC-097 can provide the exact experiment manifest; UC-098 can sample actual forwarding receipts.

## Privacy / security

Queue state can leak usage patterns if it is too detailed.

- advertise coarse pressure classes, not per-user queue contents;
- do not reveal private message topics or correspondent identities;
- authenticate pressure/admission messages;
- bind an admission decision to an epoch so stale `ACCEPT` cannot be replayed indefinitely;
- rate-limit retries after `REFUSE`;
- preserve UC-095 volunteer budgets and local opt-out;
- avoid public rankings of students by how much traffic they carry;
- keep emergency priority as a controlled drill policy, not a claim of operational public-safety QoS.

## Difficulty

**Medium–High.** The state machine is straightforward; avoiding oscillation, stale feedback, starvation and policy bypass under long delays is the interesting part.

## Why this is distinct

- **UC-045:** chooses what a mobile harvester downloads during a short contact.
- **UC-095:** defines volunteer resource budgets and fairness.
- **UC-102:** studies multi-destination dissemination and duplicate control.
- **UC-108:** propagates **current downstream queue pressure** so upstream nodes can admit, defer or reroute traffic before overload occurs.

## Research / implementation signal

DTN research continues to treat buffer space and contact duration as coupled scarce resources. A 2026 Computer Communications paper studies joint scheduling and buffer management, while a 2026 Wireless Networks paper focuses on preventing buffer exhaustion under multi-copy DTN routing. These results motivate the experiment but do not predict PollicinoNet field performance.

References:

- https://doi.org/10.1016/j.comcom.2026.108432
- https://doi.org/10.1007/s11276-025-04075-2
- https://www.rfc-editor.org/rfc/rfc9171.html
