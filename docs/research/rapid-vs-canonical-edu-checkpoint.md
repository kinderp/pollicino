# RAPID vs canonical DTN baselines — UC-EDU-001 checkpoint

Status: model-synthetic research checkpoint, 2026-08-27

## Question

Does the current one-selection RAPID prototype show useful routing discrimination on the same preregistered deadline scenario already used for Direct Delivery, Epidemic, Binary Spray-and-Wait and PRoPHET?

This checkpoint does **not** ask whether RAPID is globally better or cheaper on a real LoRa network. It asks a narrower question required by the Use-Case Justification Gate:

> does the additional inference machinery change a routing decision in a useful, falsifiable way before we spend more effort integrating it?

## Shared scenario

The comparison reuses `UC-EDU-001` without changing its routing windows or application deadline:

```text
application deadline: 1030

1001  B -> D   historical/current contact
1005  A -> X   uninformed detour
1010  A -> B   useful relay opportunity
1020  B -> D   on-time delivery opportunity
1060  X -> D   late delivery opportunity
```

The object originates at A. X has no useful prior history toward D. B has prior B-D history. For RAPID only, A also has explicit slower A-D historical observations so the value of the existing source replica is not silently ignored when computing marginal replication utility.

All RAPID prior observations precede the first routing window. No future contact is revealed to the algorithm.

## Canonical outcomes already preregistered

| Strategy | Outcome | First delivery |
| --- | --- | ---: |
| Direct Delivery | undelivered | — |
| Epidemic | on time | 1025 |
| Binary Spray-and-Wait, L=2 | late | 1065 |
| PRoPHET | on time | 1025 |

The scenario already demonstrates that eventual delivery ratio alone is insufficient: Spray-and-Wait eventually succeeds but misses application usefulness.

## RAPID one-selection result

The isolated RAPID runner:

1. skips the uninformed `A -> X` contact;
2. selects `A -> B` using marginal deadline utility per transfer byte;
3. allows direct `B -> D` delivery;
4. delivers at `1025`, before the `1030` deadline.

Therefore RAPID passes the first behavioral gate: its inference chain can produce a useful decision rather than merely reproduce flooding.

## Traffic interpretation

On this scenario RAPID also performs fewer authoritative content replications than Epidemic because it does not copy the object to X. Consequently its existing Pollicino governed-transfer wire total is lower than Epidemic's governed-transfer wire total.

That is **not yet a complete network-traffic superiority result**.

RAPID additionally exchanges modeled control knowledge:

- meeting/inter-meeting metadata;
- replica-location metadata;
- final-delivery knowledge;
- candidate queue/opportunity quotes.

The prototype currently counts these as logical control entries. They do not yet have an explicit serialized wire representation, header cost or authentication cost. Claiming total-byte superiority before accounting those bytes would be invalid.

## Gate decision

**Decision: PROTOTYPE CONTINUES.**

Evidence supports continuing RAPID research because the one-selection prototype shows deadline-useful discrimination on a preregistered scenario.

It does **not** justify:

- adopting RAPID as production routing;
- adding a general strategy-controlled ranking abstraction to the common comparator;
- claiming lower total network traffic;
- claiming physical LoRa benefit.

## Next experiment: cost of intelligence

The next justified question is:

> are the content bytes avoided by RAPID worth the control-plane bytes required to make the decision?

Build an isolated deterministic control-wire accounting experiment before any common routing-API generalization.

Compare at least two encodings:

1. a simple self-contained baseline using full bundle identities and explicit pseudonymous node identifiers;
2. a compact shared-node-index encoding, counting dictionary/bootstrap cost separately rather than treating shared state as free.

Report non-overlapping bytes for:

- meeting metadata;
- replica advertisements/tombstones;
- final-delivery acknowledgements;
- queue/opportunity quotes;
- bootstrap/dictionary state;
- authentication placeholder separately until a security design is selected.

Then compute, still only as `MODEL_SYNTHETIC`:

```text
RAPID modeled total
  = governed Pollicino transfer wire bytes
  + explicitly encoded RAPID control wire bytes
```

Kill/defer criterion: if control overhead consumes the saved content traffic in the small-object/low-volume regimes relevant to PollicinoNet, defer RAPID there even if its routing choices are behaviorally smarter.

## Validation

- first attempted EDU/RAPID comparison correctly failed closed because the existing A replica lacked queue/opportunity inference; no existing replica was allowed to disappear from utility calculation;
- corrected experiment supplied explicit slower A-D prior history and retained faster B-D history;
- full project suite + targeted EDU/RAPID tests: GitHub Actions `33077652565` — PASS.

## Evidence boundary

Everything in this checkpoint is `MODEL_SYNTHETIC`.

No real LoRa capacity, airtime, range, energy, node density or geographic routing claim follows from it. Physical calibration remains behind **GATE PROVE FISICHE HW-006**.
