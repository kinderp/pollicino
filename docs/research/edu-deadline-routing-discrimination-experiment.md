# EDU deadline routing discrimination experiment

Status: preregistered deterministic MODEL_SYNTHETIC experiment

## Question

Can application usefulness deadline distinguish routing strategies that look equivalent under eventual delivery ratio?

This experiment is motivated by `UC-EDU-001` and is also relevant to `UC-EMERG-001`.

## Object

One small exact resource descriptor is created at node `A` at synthetic time `1000`.

- final destination: `D`;
- transport TTL: long enough that all candidate relay paths remain technically valid;
- application usefulness deadline: `1030`;
- all strategies see the exact same contacts, byte budgets and initial state.

## Contact sequence

```text
1001  B -> D    history only; B does not yet have the object
1005  A -> X    tempting early relay
1010  A -> B    useful relay
1020  B -> D    on-time delivery opportunity
1060  X -> D    late delivery opportunity
```

Every contact is synthetic. Duration and logical source-byte budget remain independent explicit inputs.

## Strategies

### Direct Delivery

Expected: no delivery, because `A` never meets `D`.

### Epidemic

Expected:

```text
A -> X
A -> B
B -> D at ~1025
```

Result: eventual delivery **and** on-time delivery.

### Binary Spray-and-Wait, L=2

Expected:

```text
A has 2 tokens
A -> X: give X one token, A keeps one
A -> B: A is now in wait phase, so no replication
X -> D at ~1065
```

Result: eventual delivery succeeds, but application deadline is missed.

### PRoPHET

`B -> D` occurs before `A -> B`, so the model learns that `B` has useful encounter history toward `D`.

Expected:

```text
A -> X: no useful destination predictability, hold
A -> B: B has greater P(*,D), replicate
B -> D at ~1025
```

Result: eventual delivery **and** on-time delivery.

PRoPHET routing-control/RIB bytes remain unmodeled, so this experiment may compare routing behavior and deadline outcome but must not claim complete traffic superiority for PRoPHET.

## Preregistered expected classification

| Strategy | Eventual | Before deadline 1030 | Late | Undelivered |
|---|---:|---:|---:|---:|
| Direct Delivery | 0 | 0 | 0 | 1 |
| Epidemic | 1 | 1 | 0 | 0 |
| Binary Spray-and-Wait L=2 | 1 | 0 | 1 | 0 |
| PRoPHET | 1 | 1 | 0 | 0 |

The key result is not which strategy is globally best. It is:

> eventual delivery treats Epidemic, Spray-and-Wait and PRoPHET as equal, while application deadline reveals a meaningful difference.

## Falsification

The experiment fails its purpose if:

- Spray-and-Wait also delivers before 1030;
- Epidemic or PRoPHET cannot deliver before 1030 for reasons unrelated to the intended routing decision;
- different strategies receive different contact inputs;
- deadline evaluation changes the routing behavior itself.

If the deterministic implementation does not match the preregistered behavior, fix the model or the experiment; do not move the deadline after seeing results.

## What this would justify

A successful discrimination result justifies keeping application deadline as an evaluation objective.

It does **not** by itself justify RAPID.

RAPID-like work requires a separate utility gate. A plausible first objective would be:

> maximize the count of EDU resource descriptors delivered before their application deadlines under fixed contact-byte and storage budgets.

## Evidence boundary

All results are `MODEL_SYNTHETIC`.

No claim about real school routes, LoRa contact times or real on-time delivery is permitted before **GATE PROVE FISICHE HW-006** and later privacy-safe field evidence.
