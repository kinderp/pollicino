# Recency vs interval vs RAPID discriminator

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-28

## Use-case question

UC-DNA-001 and UC-CONTENT-001 rely on human-carried nodes moving between school, home clusters and gateways. A natural cheap heuristic is to forward toward a peer that has seen the destination/gateway more recently.

This experiment asks whether **destination recency alone can be misleading** when a recent gateway encounter is occasional, while another carrier has older but much more regular gateway access.

## Scenario

One time-sensitive 64-byte object is created at node A at `t=1000`; application usefulness deadline is `1060`.

Historical state:

- A last direct destination encounter: `970`;
- B last direct destination encounter: `990` (freshest);
- C last direct destination encounter: `950` (older).

For interval-aware models the historical direct inter-meeting means are:

- A-D: `100 s`;
- B-D: `200 s`;
- C-D: `40 s`.

All explicit transfer-opportunity samples are identical (`64 B`), so the discriminator is encounter regularity, not an invented faster bearer.

Future synthetic windows:

```text
1010  A -> B
1020  A -> C
1040  C -> D   on-time opportunity
1100  B -> D   late opportunity
```

No strategy receives these future windows as oracle metadata.

## Destination Recency result

Destination Recency compares only last direct destination-contact timestamps:

```text
A score = 970
B score = 990  -> A forwards to B
C score = 950  -> A refuses C
```

C therefore has no useful bytes for its `1040` destination contact. B eventually delivers at `1105`.

Result:

- eventual delivery: PASS;
- first delivery: `1105`;
- application deadline `1060`: **MISS**.

This is a concrete failure mode of recency: **freshest historical contact is not the same thing as best future opportunity**.

## Destination Interval result

`DestinationIntervalStrategy` uses only each node's local running mean between direct destination encounters. It has no transitivity, route graph, replica gossip, queue model, deadline probability or future knowledge.

```text
A mean = 100 s
B mean = 200 s -> skip B
C mean =  40 s -> forward to C
```

C delivers at `1045`.

Result:

- eventual delivery: PASS;
- first delivery: `1045`;
- application deadline `1060`: **PASS**.

## RAPID result

RAPID uses the already implemented meeting/replica/opportunity/deadline research state. With the same historical meeting intervals and identical opportunity samples, it also places a useful copy on C and delivers at `1045`.

Result:

- eventual delivery: PASS;
- first delivery: `1045`;
- application deadline `1060`: **PASS**.

## Gate decision

This scenario **discriminates Destination Recency**, but it does **not discriminate Destination Interval from RAPID**.

Therefore:

1. Destination Recency remains useful as the cheapest baseline, but is no longer sufficient as the only simple mobility heuristic.
2. Destination Interval becomes the mandatory next simple baseline for regular human-mobility/gateway use cases.
3. RAPID remains **RESEARCH / DEFER** as an adoption candidate.
4. Do not generalize the common routing API for RAPID on the strength of this scenario.
5. A future RAPID-promoting use case must make both Recency **and Interval** materially fail while RAPID succeeds enough to justify its extra control state.

This is the intended Use-Case Justification Gate behavior: when a simpler model captures the useful distinction, prefer the simpler model.

## Next discriminators worth testing

RAPID could become justified when direct interval alone cannot represent the relevant cost, for example:

- two carriers with similar destination intervals but very different queued bytes / meetings-needed before the target object is served;
- multiple replicas where marginal value of another copy has strong diminishing returns;
- multiple competing objects with different usefulness deadlines sharing one short contact;
- transitive opportunity where the useful carrier rarely meets the final gateway directly but reliably reaches another carrier that does;
- heterogeneous transfer opportunity where equal encounter frequency hides very different useful bytes per meeting.

Each case should first receive the smallest dedicated baseline before being used to promote full RAPID.

## Validation

GitHub Actions `33163826841`: full project suite PASS and targeted discriminator tests PASS.

## Evidence boundary

All timing and byte opportunities are deterministic `MODEL_SYNTHETIC` experiment inputs. No real LoRa mobility, range, airtime, energy or geographic superiority is claimed.

Real calibration remains behind **GATE PROVE FISICHE HW-006**.
