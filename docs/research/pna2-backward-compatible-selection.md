# PNA2 backward-compatible selection model

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-27

## Question

The simple-codec PNA2 experiments show large potential savings, but a production extension would be harmful if it required a costly new handshake or broke PNA1-only nodes.

The compatibility question is therefore part of the Use-Case Justification Gate:

> can an alternative availability representation be selected without adding a new negotiation exchange, while preserving PNA1 as a safe fallback and even as the preferred representation when it is cheaper?

## Existing PND1 capability field

The current PND1 wire header already contains a fixed-width 16-bit `capability_mask`.

Its width is present whether every bit is zero or not. The current core deliberately assigns no application meaning to the mask.

The research model therefore does **not** change PND1 and does **not** reserve a stable production bit. Instead the caller supplies a one-bit experimental mask.

The test verifies that setting that bit leaves PND1 `encoded_size` unchanged.

## Selection rules

`availability_negotiation.py` models these rules:

```text
source advertises alternative support?
receiver supports alternative?

if either answer is NO:
    send ordinary PNA1

if both are YES:
    benchmark PNA1 + all lossless alternatives
    through the same deterministic PNF1 profile

    if PNA1 is cheapest:
        send PNA1
    else:
        send the cheapest exact alternative
```

Thus “both nodes support PNA2” does not mean “PNA2 must be used”. It only permits a different representation when that representation pays for itself.

## Legacy behavior

### New receiver, old source

Old/source descriptor does not advertise the research capability bit:

```text
receiver -> PNA1
```

### New source, old receiver

Old receiver has no alternative support:

```text
receiver -> PNA1
```

### Two capable peers, sparse difference

At the maximum current PCM1 manifest with 20 isolated missing chunks, the model selects `missing_u16` rather than PNA1.

### Two capable peers, high-entropy availability

Even with both peers capable, the model selects PNA1 because the alternative representations do not reduce deterministic PNF1 wire cost.

## Validation

GitHub Actions `33082978128` — PASS:

- full project suite: PASS;
- targeted PNA2 negotiation + codec + wire tests: PASS.

## What this changes

Nothing in the stable protocol yet.

The work proves only that the existing PND1 capability field is sufficient to model backward-compatible feature discovery without inventing another handshake packet.

Before production adoption we would still need to decide:

- whether a PNA2 capability deserves a globally assigned bit;
- which alternative codecs are actually standardized;
- whether one generic `alternative availability` capability is enough or individual codecs require their own negotiation;
- decoder resource limits and denial-of-service protections;
- security/authentication relationship with the existing discovery/custody model;
- mixed-version upgrade/downgrade tests on real nodes.

These are protocol decisions and remain gated.

## Gate decision

**Backward-compatible PNA2 selection: PROTOTYPE / viable.**

No new handshake abstraction is justified. Reuse the existing fixed-width capability mechanism if and when PNA2 is promoted.

**No production capability bit is assigned in this checkpoint.**

## Evidence boundary

All codec and wire choices remain deterministic `MODEL_SYNTHETIC` PNF1 evidence. Real LoRa timing/capacity/energy remains behind **GATE PROVE FISICHE HW-006**.
