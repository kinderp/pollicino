# RAPID control-wire break-even checkpoint

Status: model-synthetic research checkpoint, 2026-08-27

## Why this experiment exists

The one-selection RAPID prototype already showed useful routing discrimination on the preregistered EDU scenario: it skipped an uninformed relay, selected the historically useful relay and delivered before the application deadline.

That was not enough to claim traffic efficiency because RAPID's routing knowledge was counted only as logical control entries.

This experiment asks the next Use-Case-Gate question:

> are the governed content-transfer bytes saved by smarter routing greater than the bytes required to communicate the routing knowledge?

No production wire format is introduced. The experiment lives outside PNB1/PNC1/H2 and remains `MODEL_SYNTHETIC`.

## Experimental accounting model

`rapid_control_wire.py` converts the control work already exposed by RAPID encounter reports into deterministic byte counts.

It counts separately:

- meeting/inter-meeting entries;
- complete-replica advertisements/tombstones;
- final-delivery acknowledgement entries;
- queue/opportunity quotes;
- stream headers;
- optional shared-node-index dictionary/bootstrap representation.

It does **not** invent:

- LoRa airtime;
- retransmission probability for control frames;
- authentication/encryption tags;
- dictionary dissemination fanout;
- physical energy.

Those omissions prevent this result from becoming a physical or production-network claim.

## Two deliberately simple node-reference baselines

### A. Self-contained 128-bit pseudonym

Every control record carries a 16-byte pseudonymous node reference.

Advantages:

- self-contained;
- no shared dictionary assumption;
- no bootstrap table required.

Disadvantage:

- larger repeated routing metadata.

### B. Shared u16 node index

Control records use a 2-byte node index. A canonical dictionary representation is counted separately:

```text
4-byte dictionary header
+ N * (2-byte index + 16-byte full pseudonym)
```

For the four-node checkpoint this is 76 bytes.

Important: 76 bytes is the representation of one dictionary, **not** a claim that distributing that dictionary to all peers costs only 76 bytes. Network-wide dissemination/fanout remains unmodeled and must not be hidden.

## Checkpoint scenario

The scenario is the same small RAPID-vs-Epidemic schedule already validated:

```text
A -> X   uninformed relay opportunity
A -> B   useful relay opportunity
B -> D   final delivery
```

RAPID skips X. Epidemic copies to X and B.

Both deliver at the same synthetic time.

## Measured model output

Validation run: GitHub Actions `33078118396`.

### Governed transfer only

```text
RAPID governed transfer wire: 1260 B
Epidemic wire:                1890 B
```

So RAPID avoids 630 bytes of governed transfer traffic by avoiding the unnecessary A->X replication.

### RAPID with self-contained 128-bit pseudonyms

Control work:

```text
meeting metadata: 384 B
replica metadata: 260 B
delivery metadata: 0 B
queue quote:       54 B
bootstrap:          0 B
-----------------------
RAPID control:     698 B
```

Modeled total:

```text
1260 + 698 = 1958 B
```

Compared with Epidemic:

```text
RAPID:    1958 B
Epidemic: 1890 B
Delta:     +68 B
```

**Result:** in this small-object/small-network regime, the simple self-contained RAPID control representation consumes more than the content traffic it saves.

### RAPID with shared u16 node indices

Control work:

```text
meeting metadata: 188 B
replica metadata: 204 B
delivery metadata: 0 B
queue quote:       40 B
bootstrap:         76 B
-----------------------
RAPID control:     508 B
```

Modeled total:

```text
1260 + 508 = 1768 B
```

Compared with Epidemic:

```text
RAPID:    1768 B
Epidemic: 1890 B
Delta:    -122 B
```

**Result:** under the explicit but optimistic assumption that one shared node-index dictionary representation is sufficient for this campaign, compact control state makes RAPID cheaper in this scenario.

## Control-entry audit

The schedule exposed 12 modeled RAPID control entries:

```text
meeting entries:  7
replica entries:  4
delivery entries: 0
queue quotes:      1
```

The byte-accounting layer fails closed unless these categories exactly recompose the pre-existing `control_entry_count_lower_bound`.

## Main scientific conclusion

There is no context-free answer to “is RAPID more efficient than Epidemic?”.

For this scenario:

- RAPID makes the smarter forwarding decision;
- it saves 630 governed-transfer bytes;
- a naive self-contained control format spends 698 bytes and loses overall;
- a compact indexed format spends 508 bytes including one dictionary representation and wins by 122 bytes;
- the result could change again once dictionary dissemination and security overhead are counted.

Therefore **routing intelligence itself has a scarce-link budget**.

This is directly aligned with PollicinoNet's central research objective: do not introduce knowledge/control information unless the information it saves is worth more than the information needed to communicate it.

## Use-Case Gate decision

**Decision: CONTINUE AS PROTOTYPE, DO NOT ADOPT.**

RAPID has now passed two gates:

1. behavioral usefulness: it can make a deadline-useful routing decision;
2. possible byte usefulness: at least one explicit compact-control regime can outperform Epidemic in the synthetic checkpoint.

It has *not* passed a production/adoption gate because:

- the self-contained baseline loses;
- dictionary dissemination is not yet counted end-to-end;
- authentication/security overhead is not encoded;
- only a tiny scenario has been measured;
- control retransmissions/airtime are not modeled physically;
- no real student-network evidence exists.

## Next justified experiment

Do not generalize the common routing API yet.

The next experiment should be a **break-even regime sweep** varying at least:

- object/source bytes;
- number of avoided Epidemic replications;
- node count;
- control-entry count;
- full-ID vs shared-index mode;
- amortization of shared dictionary/bootstrap across multiple bundles.

The key output should be a regime map:

```text
when control_cost < avoided_transfer_cost -> RAPID worth studying
when control_cost >= avoided_transfer_cost -> simpler routing preferred
```

This directly serves `UC-DNA-001` and `UC-CONTENT-001`, where many small topic objects or content references may amortize shared routing state very differently from one isolated object.

## Evidence boundary

All values above are deterministic model bytes, not physical radio bytes/airtime measurements. Real range, loss, contact capacity, energy and field superiority remain behind **GATE PROVE FISICHE HW-006**.
