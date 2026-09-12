# Destination Recency vs Destination Interval routing gate

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-27

## Why this experiment exists

The Use-Case Justification Gate requires a concrete failure of the simpler routing policy before richer routing knowledge can be justified.

`DestinationRecencyStrategy` already solved the initial school/home data-mule workload with very little state: each node exposed only the timestamp of its most recent direct encounter with the destination/gateway.

The next question was therefore not "can RAPID work?" but:

> Is there a realistic UC-DNA-001 / UC-CONTENT-001 mobility pattern in which recency is materially wrong, and if so what is the smallest additional state needed to fix it?

## Discriminating mobility pattern

The scenario models two students encountered at school:

- `X`: recently passed close to gateway `D`, but that encounter was a one-off event;
- `B`: last saw `D` earlier, but follows a regular route/commute and has repeated direct contacts with `D`;
- `A`: source carrier with a relatively recent but much slower direct-contact history.

Synthetic chronology:

```text
past history
A-D: 50, 950        -> mean interval 900 s
B-D: 700, 800, 900  -> mean interval 100 s
X-D: 990            -> recent, but no interval estimate yet

routing experiment
1005  A -> X        school encounter
1010  A -> B        school encounter
1020  B -> D        regular commuter contact
1100  X -> D        rare next contact
```

The micro-reference is created at `1000` and has an application usefulness deadline at `1030`.

Every historical observation precedes the first routing window. No future contact is supplied to any routing strategy as oracle knowledge.

## Destination Recency result

Prior last-seen values are:

```text
A: 950
B: 900
X: 990
```

Therefore recency makes the locally consistent but application-wrong choices:

```text
A -> X : YES   990 > 950
A -> B : NO    900 < 950
```

X eventually reaches D at synthetic time `1105`, so the object is delivered but misses the deadline `1030`.

This is a material failure: eventual delivery alone would hide it.

## RAPID result

The existing RAPID prototype sees repeated direct meeting history rather than only the latest timestamp.

It:

- cannot derive a defensible interval estimate for X from a single observation and fails closed;
- sees B's repeated 100-second direct destination encounters;
- skips `A -> X`;
- selects `A -> B`;
- delivers `B -> D` at synthetic time `1025`, before deadline.

This establishes a concrete use case in which richer encounter history is useful.

## Simplest-next-baseline result

Before crediting RAPID for the win, the gate requires a simpler hypothesis.

`DestinationIntervalStrategy` stores only a running mean of each node's *direct* inter-meeting interval with one destination.

It deliberately has no:

- transitivity;
- route graph;
- replica-location gossip;
- queue model;
- deadline probability;
- marginal utility;
- future topology knowledge.

At `A -> X`, X has only one historical encounter, so its interval is `UNKNOWN` and forwarding fails closed.

At `A -> B`:

```text
A mean interval = 900 s
B mean interval = 100 s
```

so B is selected. The object arrives at D at `1025`, exactly matching the useful path selected by RAPID in this scenario.

The strategy continues to learn honestly after the decision: the real `B -> D` contact at 1020 updates B's final running mean, and the late `X -> D` contact at 1100 creates X's first interval sample. Tests do not freeze pre-decision statistics after real later observations.

## Modeled control cost

For the two non-destination decisions (`A -> X`, `A -> B`), Destination Interval needs only two target-authored interval quotes.

Research wire model:

```text
full 128-bit pseudonymous reference: 56 B total
shared u16 index + one 4-node dictionary representation: 104 B total
```

The indexed result includes the same explicit one-dictionary representation rule used by the related routing-control experiments; network-wide dissemination/authentication remains outside this model.

## Validation

GitHub Actions `33120050566`:

- full suite: `295 passed, 12 skipped`;
- targeted recency/interval gate: `3 passed`.

Earlier `33119530951` separately validated the pure Recency-vs-RAPID discrimination before Destination Interval was introduced.

## Gate decision

### Destination Recency

**KEEP as the cheapest baseline, but it is now known to be insufficient in the recent-but-rare vs older-but-regular mobility regime.**

### Destination Interval

**PROTOTYPE / mandatory next-simple baseline for regular-mobility use cases.**

It has earned its existence through a concrete failure of Recency and fixes that failure with a very small state increase.

Do not yet promote it to stable top-level API or universal production routing policy.

### RAPID

**RESEARCH / DEFER remains appropriate.**

RAPID solved the discriminating scenario, but the scenario does not justify RAPID's richer replica, queue and utility state because a one-dimensional direct-interval heuristic solves it too.

## Next justified discriminator

The next experiment must target information that Destination Interval genuinely lacks.

A realistic candidate for UC-CONTENT-001 / UC-DNA-001 is:

> two carriers have similarly good destination meeting frequency, but one has poor transfer opportunities / a congested destination queue while the other has fewer or similar meetings with substantially more useful bytes per encounter.

Destination Interval sees only meeting frequency and should be unable to distinguish them. RAPID's explicit queue/opportunity knowledge may then have a justified advantage.

This must be tested before adding any general RAPID ranking hook.

## Evidence boundary

All observations and byte counts are deterministic `MODEL_SYNTHETIC` research evidence. No physical LoRa range, capacity, airtime, energy, collision or field-network superiority is claimed.

Real calibration remains behind **GATE PROVE FISICHE HW-006**.
