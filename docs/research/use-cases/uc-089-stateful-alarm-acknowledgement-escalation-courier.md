# UC-089 — Stateful Alarm Acknowledgement and Escalation Courier

## Idea

Represent an alarm as a **stateful condition**, not as a one-shot notification: the condition can become active, be acknowledged by a human, clear, be confirmed as handled, or escalate if nobody acknowledges it within policy.

Those state transitions may cross disconnected PollicinoNet islands through delayed relays.

## Problem solved

A sensor alert that says “temperature high” is not enough for operational workflows. We also need to know:

- is the condition still active?
- has a responsible person actually seen this exact occurrence?
- did somebody act on it?
- did the condition clear before anyone saw it?
- did an acknowledgement arrive for an old alarm occurrence after a newer one started?
- should an unacknowledged alarm be escalated to another node/group?

This matters for harmless school/lab/rural experiments and, much later, could inform emergency-oriented designs after independent validation.

## Actors / nodes

- sensor/alarm source;
- student relay/store-and-forward nodes;
- operator/teacher acknowledgement node;
- optional escalation node/group;
- optional rich log/evidence store.

## Why PollicinoNet fits

Alarm lifecycle messages are small but semantically strict.

- **DISCOVERY:** alarm source, condition class, severity band, current-state hint;
- **EXACT:** condition ID, occurrence/event ID, transition sequence, source identity, timestamp/epoch, acknowledgement target and policy version;
- **SEMANTIC:** human labels such as `high-temperature`, `door-open` or `sensor-fault` may help a UI, but acknowledgements must bind to the exact event occurrence.

Delayed, duplicated and reordered delivery is exactly where a state machine is more useful than a simple notification feed.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact alarm transition, severity, event ID, acknowledgement, escalation and clear state;
- **BLE:** local operator acknowledgement and synchronization;
- **Wi-Fi/LAN:** detailed telemetry, charts, logs and evidence;
- **Internet:** optional authoritative dashboard or remote sink;
- **physical transport:** a student node can carry alarm/acknowledgement state between disconnected islands.

## What we can test now in software

Define an `AlarmCondition` with separate machine and human state:

```text
condition_id
occurrence_id
source_id
active_state
acked_state
confirmed_state
severity
transition_seq
created_epoch
policy_id
```

and an `AlarmAction`:

```text
action_id
condition_id
occurrence_id
action = ACK | CONFIRM | ESCALATE | COMMENT
actor_id
created_epoch
```

Then test:

- alarm becomes active, then clears before acknowledgement;
- acknowledgement arrives after clear;
- alarm reactivates with a new occurrence ID;
- stale acknowledgement for the old occurrence;
- duplicate acknowledgements;
- escalation after a bounded no-ack interval;
- escalation message overtaken by a valid acknowledgement;
- conflicting operator actions;
- source reboot and recovery of retained alarm state;
- missing transitions followed by reconciliation;
- rich evidence arriving after the alarm lifecycle is already complete.

Useful metrics include alarm-to-first-delivery, alarm-to-ack delay, stale-ack rejection count, duplicate transitions, escalation count and state-convergence time.

A critical invariant is:

> an acknowledgement for occurrence A must never acknowledge a later occurrence B of the same condition.

## What requires real hardware

A safe first experiment needs:

- 4–6 LoRa boards;
- one harmless sensor source (temperature, light, button, water-level simulator or software threshold);
- one operator node;
- one relay between isolated groups;
- optional laptop dashboard.

Create a controlled threshold crossing, isolate the operator, and observe alarm/ack/clear ordering after relays move.

Do not use safety-critical equipment in the initial experiment.

## Messina teaching scenario

Place a synthetic “lab temperature” source at school and operator nodes in two disconnected student groups. The first group receives the alarm but cannot reach the teacher directly; a student relay carries the exact occurrence ID. The teacher acknowledges it, and that acknowledgement later returns to the source through another relay.

A second experiment intentionally triggers a new occurrence before the old acknowledgement returns, demonstrating why exact event binding matters.

## Privacy / security

- authenticate alarm sources and operator actions;
- bind acknowledgements to the exact occurrence/event ID;
- do not let relays silently change severity or lifecycle state;
- keep operator identities pseudonymous or role-based where possible;
- avoid exposing detailed sensor/location metadata on broadcast LoRa frames;
- rate-limit noisy/flapping alarms;
- make escalation policy explicit and versioned;
- never interpret missing acknowledgement as proof that nobody saw the event;
- keep real emergency/safety use out of scope until independently validated.

## Difficulty

**Medium.** The packets are small; the interesting complexity is the condition state machine, stale acknowledgement handling, escalation races and reboot recovery.

## Why this is distinct from nearby use cases

- **UC-002:** distributes signed bulletins/messages.
- **UC-007:** emits compact edge-AI event scouts.
- **UC-022:** corroborates observations from several witnesses.
- **UC-089:** manages the **full lifecycle of one stateful alarm**, including exact acknowledgement and escalation under delay/reordering.

## Research / implementation signal

OPC UA Part 9 models alarms as stateful Conditions and separates process state from human acknowledgement/confirmation. In particular, the acknowledgement is tied to the EventId of a particular event notification, which is a strong conceptual match for avoiding stale acknowledgements in a DTN.

References:

- https://reference.opcfoundation.org/specs/OPC-10000-9/5
- https://reference.opcfoundation.org/specs/OPC-10000-9/5.7.2
