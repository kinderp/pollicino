# Application usefulness deadline — use-case gate

Status: PROTOTYPE / benchmark semantics

## Why this exists

Transport TTL and application usefulness are different concepts.

`PNB1.ttl_seconds` answers:

> When must this bundle stop being retained/forwarded by the transport?

An application deadline answers:

> By when must the information arrive to still satisfy the application objective?

Two independent PollicinoNet use cases require the distinction:

- `UC-EDU-001`: an assignment/resource descriptor is useful when it reaches a student before the relevant lesson/class deadline;
- `UC-EMERG-001`: a time-sensitive bulletin can become operationally stale before its transport retention TTL expires.

This satisfies the architecture gate for studying a shared application-deadline concept.

## Simplicity decision

Do **not** add a deadline field to PNB1.

Do **not** initially add a deadline field to `ScheduledBundle` either.

The smallest falsifiable implementation is a benchmark sidecar:

```text
scenario_id
bundle_id
application_deadline_s
```

It is evaluated against the already measured `first_delivery_s`.

This keeps three concepts separate:

```text
created_at -------- application deadline -------- transport TTL expiry
     |                       |                            |
     |                       |                            +-- forwarding forbidden
     |                       +-- delivery may be too late for the use case
     +-- bundle exists
```

The deadline may be earlier than transport expiry. If it is later than transport expiry, transport expiry still prevents later delivery; the application deadline does not extend TTL.

## Initial metrics

For each strategy and deadline-scoped bundle:

- deadline opportunity count;
- delivered before/on deadline;
- delivered late;
- not delivered;
- on-time delivery rate;
- signed slack `deadline_s - first_delivery_s` for delivered items.

Positive slack means early/on-time delivery; negative slack means late delivery.

Keep ordinary delivery ratio and latency beside deadline metrics. A strategy may have high eventual delivery but poor on-time delivery.

## Evidence

Initial deadline results inherit the evidence class of the routing benchmark, currently `MODEL_SYNTHETIC`.

Synthetic contact windows and logical byte budgets cannot establish real school or emergency delivery performance.

## Use-case gate

- use cases: `UC-EDU-001`, `UC-EMERG-001`;
- baseline: ordinary eventual delivery / TTL-only evaluation;
- measurable problem: eventual delivery hides whether information arrived while still useful;
- proposed improvement: independent application-deadline evaluation;
- simplest competing solution: compare `first_delivery_s` with one sidecar timestamp;
- experiment: paired canonical DTN baselines on identical scenarios;
- success criterion: metric distinguishes strategies/scenarios that eventual delivery treats as equivalent;
- kill criterion: if no active workload needs time-bounded utility, keep the evaluator unused and do not promote it into production state;
- complexity cost: one benchmark-only objective/evaluator, no wire migration;
- evidence: `MODEL_SYNTHETIC` first.

**Decision: PROTOTYPE.**

## RAPID boundary

A RAPID-like strategy should not be implemented merely because deadline metrics now exist.

The next gate must define a concrete utility objective, for example:

```text
maximize number of EDU resource descriptors delivered before deadline
under a fixed contact/storage budget
```

Only then should the deadline sidecar become an input to a routing decision.

## Physical boundary

No hardware is required to validate deadline semantics.

Claims about real delivery-before-deadline on LoRa remain behind **GATE PROVE FISICHE HW-006**.
