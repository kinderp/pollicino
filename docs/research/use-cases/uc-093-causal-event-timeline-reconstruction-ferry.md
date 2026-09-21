# UC-093 — Causal Event Timeline Reconstruction Ferry

## Idea

Reconstruct **what happened before what** across disconnected PollicinoNet nodes even when wall clocks are inaccurate, logs arrive late, and two events may genuinely be concurrent.

Each node keeps small local event records with causal references. Relays ferry compact event digests and dependency edges; richer logs can follow later over BLE/Wi-Fi or physical transport. A collector then builds a partial causal timeline instead of pretending that timestamp sorting is always correct.

## Problem solved

Distributed student nodes, sensors and robots will often have:

- imperfect or drifting clocks;
- long periods without NTP/Internet;
- delayed and reordered messages;
- reboots and missing log fragments;
- independent events that have no justified total order.

For debugging, experiments, incident analysis and robotics, `08:42:03` versus `08:42:04` is not enough if the clocks were not synchronized. We need to distinguish:

- **known-before**;
- **known-after**;
- **concurrent / no causal relation known**;
- **unknown because evidence is missing**.

## Actors / nodes

- student PollicinoNet boards;
- sensors and edge nodes;
- Romeo/robot workers;
- relay/store-and-forward students;
- school collector / timeline reconstructor;
- optional trusted-time checkpoints from UC-020.

## Why PollicinoNet fits

A DTN naturally creates partial histories that meet later. Causal metadata is small enough for the control plane, while full logs can remain local until requested.

- **DISCOVERY:** node has event-history fragments for experiment/session X;
- **EXACT:** event ID, node ID/pseudonym, local sequence, causal-parent/message references, content hash and optional time anchor;
- **SEMANTIC:** reconstructed labels such as `A happened-before B` or `A and B remain unordered`.

PollicinoNet is useful precisely because the evidence can converge after the original communication opportunities are gone.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact event IDs, causal links, session ID, sequence ranges, missing-range requests and hashes;
- **BLE:** nearby event-batch reconciliation;
- **Wi-Fi/LAN:** complete logs, traces and evidence packs;
- **Internet:** optional fast synchronization when available;
- **physical transport:** a student device carries event batches back to school.

## What we can test now in software

Define a minimal `CausalEvent`:

```text
session_id
event_id
node_id
local_seq
event_type
causal_refs[]
wall_time_optional
wall_time_uncertainty_optional
payload_hash
```

Then simulate:

- two independent nodes generating concurrent events;
- send/receive chains that create a definite happened-before relation;
- messages arriving at the collector in reverse order;
- missing middle events;
- node reboot with a new boot/session epoch;
- duplicate event delivery through several relays;
- stale logs arriving after a provisional timeline was already shown;
- bad wall-clock skew that would produce the wrong order if timestamps alone were used;
- optional Lamport/vector-clock summaries versus explicit causal-edge storage;
- corrupted or forged causal references.

Useful metrics include metadata bytes per event, fraction of event pairs that can be causally ordered, unresolved/missing-edge count, convergence delay and false-order rate under deliberately skewed wall clocks.

The core semantic rule is:

> If the evidence does not establish an order, the system must not invent one.

## What requires real hardware

A first experiment needs 4–6 boards and a controlled script of physical actions, for example:

1. node A records a button event;
2. A sends a message eventually reaching B;
3. B records an LED/action event caused by that message;
4. C records an unrelated event while isolated;
5. logs return to school through different student relays.

The collector should reconstruct `A -> B` while leaving C unordered relative to them unless another causal edge exists.

We should deliberately skew or disable wall-clock synchronization on some nodes. Any claim about reconstruction success must come from these known ground-truth experiment scripts, not from assumptions about clock quality.

## Messina teaching scenario

Run one session across coarse locations such as school/Messina, Villafranca, Rometta/Venetico and Spadafora. Each group performs a small scripted event sequence, while one event chain crosses locations via store-and-forward.

The teaching question becomes visible:

```text
Which events can we prove happened before others?
Which only look earlier because of their local clocks?
Which remain genuinely unknown?
```

This is a practical distributed-systems lesson using the same network we want to deploy.

## Privacy / security

- use experiment-scoped pseudonyms instead of student identities;
- do not store continuous personal activity timelines;
- keep payload content separate from causal metadata when possible;
- sign/hash event batches so relays cannot silently rewrite history;
- bind sequence numbers to a boot/session epoch so reboot does not create ambiguous counter reuse;
- accept `UNKNOWN` when log fragments are absent;
- do not infer presence at home or precise movement from event timestamps;
- restrict real deployments to controlled experiments until retention and access rules are defined.

## Difficulty

**Medium-high.** The data structures are straightforward; the hard part is preserving partial order without accidentally converting uncertainty into a total order.

## Why this is distinct from nearby use cases

- **UC-020:** provides trusted time/freshness anchors; it does not reconstruct causal order.
- **UC-022:** corroborates whether multiple witnesses support an event claim; it does not reconstruct a distributed event graph.
- **UC-062:** carries crash diagnostics; UC-093 can order diagnostics with other events afterward.
- **UC-086:** estimates where an event originated from sensor observations; UC-093 estimates causal relationships between events.

## Research / implementation signal

Vector clocks are a standard way to represent causal ordering in asynchronous distributed systems. A 2026 open-access Acta Informatica paper explicitly treats vector clocks as building blocks for causal event ordering even in crash-prone asynchronous message-passing systems. A May 2026 IETF Internet-Draft on a causal-time substrate likewise explores forward-only causal ordering where wall-clock time is auxiliary rather than the primary ordering primitive. The Internet-Draft is research/design input, not an adopted PollicinoNet protocol or IETF standard.

References:

- https://link.springer.com/article/10.1007/s00236-026-00544-z
- https://datatracker.ietf.org/doc/html/draft-vandemeent-tibet-causal-time-02
