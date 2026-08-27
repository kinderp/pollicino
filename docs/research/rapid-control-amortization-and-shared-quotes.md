# RAPID control amortization and shared opportunity quotes

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-27

## Why this experiment exists

`UC-DNA-001` and `UC-CONTENT-001` can produce many small objects during one school/mobile campaign. That creates a direct Use-Case Justification Gate question:

> If many objects reuse the same contact history, does RAPID's routing knowledge amortize, or does per-object control erase the value of avoiding unnecessary replicas?

This study keeps the network intentionally small and controlled so the answer is about control representation rather than topology.

## Fixed experiment

Four pseudonymous nodes:

```text
A -> X     one initially uninformed relay opportunity
A -> B     repeated useful relay opportunities
B -> D     repeated final-delivery opportunities
```

Each object is one 64-byte authoritative chunk. Checkpoints use:

```text
1, 2, 5, 10, 20 objects
```

Before the routing experiment, explicit historical observations establish:

- a slower A->D direct opportunity history;
- a better B->D history;
- 64-byte observed transfer opportunities.

No future encounter is supplied as prior knowledge.

For every object:

- Epidemic transfers A->X, A->B and B->D: three authoritative copies;
- RAPID skips X and transfers A->B and B->D: two authoritative copies;
- all compared objects are eventually delivered.

The shared-u16 node dictionary is counted once as 76 bytes for the four-node campaign. Network-wide dictionary dissemination, authentication, encryption and physical retransmission are not modeled.

## First result: naive amortization fails

Validation run `33080853103`:

- full project suite: 263 passed, 2 skipped;
- targeted multi-object experiment: PASS.

With the original per-bundle queue quote representation:

| Objects | Epidemic wire | RAPID governed transfer | Indexed control | RAPID delta vs Epidemic | Queue quote entries |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1890 | 1260 | 508 | -122 | 1 |
| 2 | 3780 | 2520 | 1091 | -169 | 3 |
| 5 | 9450 | 6300 | 3341 | +191 | 15 |
| 10 | 18900 | 12600 | 7811 | +1511 | 55 |
| 20 | 37800 | 25200 | 19451 | +6851 | 210 |

Negative delta means RAPID is cheaper.

The queue quote count follows the triangular sequence:

```text
N(N+1)/2
```

because the one-selection prototype asks for a separate `meetings_needed` quote for every still-eligible object on every A->B encounter.

Therefore simply sharing the node dictionary and meeting state is not enough. The current per-bundle quote representation creates super-linear control growth for many micro-objects.

## Simplest alternative before a new protocol

The current isolated-service queue model derives each bundle's `meetings_needed` from the same carrier->destination quantity:

```text
mean observed transfer-opportunity bytes per meeting
```

For a candidate object:

```text
meetings_needed = ceil(object_bytes / mean_opportunity_bytes)
```

So transmitting `meetings_needed` separately for every bundle is redundant when many objects share the same carrier/destination opportunity estimate.

The research module `rapid_shared_quote_accounting.py` therefore models one **shared opportunity quote per encounter**:

```text
carrier
+ destination
+ mean_opportunity_bytes
+ sample_count
+ last_observed_at
```

The source can derive the per-object isolated-service estimate locally.

This changes only the control representation. It does not change:

- RAPID selection decisions;
- Pollicino stores;
- custody;
- governed transfer bytes;
- meeting/replica knowledge;
- final delivery outcome.

## Shared-quote result

Validation run `33081189542`:

- full project suite: 264 passed, 2 skipped;
- targeted amortization/shared-quote tests: PASS.

For the same shared-u16 control profile:

| Objects | Epidemic wire | RAPID transfer | Original queue entries | Original delta | Shared quote entries | Shared control | Shared delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1890 | 1260 | 1 | -122 | 1 | 496 | -134 |
| 2 | 3780 | 2520 | 3 | -169 | 2 | 1031 | -229 |
| 5 | 9450 | 6300 | 15 | +191 | 5 | 2921 | -229 |
| 10 | 18900 | 12600 | 55 | +1511 | 10 | 6071 | -229 |
| 20 | 37800 | 25200 | 210 | +6851 | 20 | 12371 | -229 |

In this controlled workload the shared quote removes the triangular quote growth. After two objects, the modeled net advantage settles at 229 bytes while both transfer and the remaining control state grow with the campaign.

This is a much healthier scaling shape, but it is deliberately a narrow result.

## What this proves

It proves that the previous multi-object failure was not inherent evidence against smarter routing. It was evidence against a redundant **per-bundle control representation**.

That distinction matters for PollicinoNet:

> before adding a more sophisticated algorithm, optimize the amount of information required to express the algorithm's decision state.

This is especially aligned with the project's original purpose.

## What it does not prove

The shared opportunity quote is not yet a production wire protocol.

The experiment assumes:

- the current isolated-object queue model;
- candidate objects can derive service from one carrier/destination opportunity mean;
- explicit prior opportunity samples exist;
- one four-node dictionary representation is enough for the modeled campaign.

It does not yet account for:

- queue ordering/bytes ahead among heterogeneous objects;
- stale opportunity estimates and refresh policy;
- dictionary distribution/fanout across a large intermittent network;
- cryptographic authentication of routing/control claims;
- malicious or incorrect opportunity advertisements;
- real LoRa airtime, collisions, duty cycle or energy.

## Use-case implication

### UC-DNA-001

Many tiny topic observations should reuse contact/service knowledge. Per-message routing metadata is likely the wrong abstraction. Shared node/route/service context plus compact object references is more consistent with the use case.

### UC-CONTENT-001

Wanted references, magnet/info-hashes and manifests can likewise share the same node/service state. Routing intelligence should be paid at encounter/campaign scope where possible, not once per content reference.

## Gate decision

**RAPID remains PROTOTYPE. Shared opportunity quote: PROTOTYPE / CONTINUE.**

The experiment is strong enough to reject the original per-bundle quote representation for the many-micro-object regime, but not strong enough to define a production control protocol.

Next justified comparison:

1. keep RAPID + shared opportunity quote as the smarter candidate;
2. build a much simpler local encounter-history forwarding heuristic;
3. account the simpler heuristic's control bytes too;
4. compare both on the same DNA/content workloads.

Only if RAPID materially beats the simpler heuristic after control costs should a general ranking architecture be reconsidered.

## Evidence boundary

All values are deterministic `MODEL_SYNTHETIC` bytes. No real-radio superiority is claimed. Physical calibration remains behind **GATE PROVE FISICHE HW-006**.
