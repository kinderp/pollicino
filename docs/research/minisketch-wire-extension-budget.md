# Minisketch wire and incremental extension budget

Status: MODEL_SYNTHETIC policy-bound checkpoint, 2026-08-27

## Question

Incremental minisketch can handle an unknown difference, but a protocol still needs a stopping rule:

> how far can the sketch be over-provisioned or incrementally extended before its modeled wire cost is no longer justified relative to the best absolute availability representation?

This checkpoint defines the budget without yet defining a production fallback protocol.

## Fixed discriminating state

Same pseudo-random partial cache used by the native minisketch experiments.

Best absolute representation for the LEFT cache:

```text
bitmap_zlib
source bytes = 6,789
modeled PNF1 wire = 10,637 B
```

The successful minisketch path is modeled with:

```text
40-byte sketch envelope
2 bytes per 16-bit sketch capacity
40-byte request envelope in the conservative two-message budget model
```

The newer preferred one-way receiver-sketch flow removes the request message entirely, so the thresholds below are conservative for that improved shape.

## One-shot capacity break-even

Validation: GitHub Actions `33085987772` — PASS.

With ten request indices reserved in the conservative model:

```text
largest capacity still cheaper than absolute = 3,338
raw sketch bytes                            = 6,676
modeled sketch+request wire                 = 10,624 B

first capacity no longer cheaper            = 3,339
raw sketch bytes                            = 6,678
modeled sketch+request wire                 = 10,652 B
```

The absolute baseline is 10,637 B.

So for a true difference of 20 elements there is enormous headroom before capacity over-provisioning alone destroys the wire advantage.

## Cumulative doubling budget

Tested extension sequence:

```text
8 -> 16 -> 32 -> 64 -> 128 -> 256 -> 512 -> 1024 -> 2048 -> 4096
```

Each step sends only the newly exposed raw sketch suffix. Raw prefix bytes are never retransmitted, but every extension pays another research envelope and PNF1 framing/ACK cost.

### Known test request count

If the final request is known to contain ten indices, the longest tested prefix still cheaper than the absolute baseline ends at:

```text
capacity 2048
cumulative modeled wire = 7,220 B
```

The next step to capacity 4096 is already more expensive than the absolute fallback.

### Unknown LEFT/RIGHT split — pessimistic reserve

Before decode, a protocol may not know how the symmetric difference divides between source-only and receiver-only elements.

A deliberately conservative budget reserves a final request containing as many indices as the current capacity.

Under that worst-case reserve, the longest tested safe prefix ends at:

```text
capacity 1024
reserved request indices = 1024
cumulative modeled wire  = 7,108 B
```

Extending to 2048 with a 2048-index request reserve is no longer cheaper than the 10,637 B absolute response.

Again, the preferred receiver-sketch one-way flow removes this request entirely, so these are intentionally conservative limits.

## Actual 20-element case

The real native incremental experiment succeeds by capacity 32:

```text
8 -> 16 -> 32
```

and costs 452 B in the older two-message model.

Thus the actual case succeeds far before any measured stop point:

```text
32 << 1024 << 2048 << 3338
```

depending on how conservative the budget is.

## Gate decision

**A bounded incremental minisketch policy is justified and has measurable stop conditions.**

Do not yet implement a complex fallback encoding. The first protocol rule can remain simple:

1. know the best absolute response cost locally;
2. extend only while a predeclared conservative sketch budget stays below that cost;
3. stop and choose an absolute path before crossing the budget;
4. exact chunk hashes remain authoritative after reconciliation.

The exact production fallback after partial sketch work remains a separate protocol-design question because already-spent sketch bytes cannot be recovered. Upstream guidance about combining partial sketches with fallback set transfer should be evaluated only if this becomes material in real workloads.

## Rateless IBLT decision

**Remain RESEARCH ONLY / DEFER.**

The current evidence now gives minisketch:

- compact native reconciliation;
- incremental prefix reuse;
- low-cost false-positive capacity margins;
- large measured over-provisioning headroom;
- bounded cumulative extension limits.

Rateless IBLT still lacks a discriminating Pollicino use case that these mechanisms fail to handle adequately.

## Evidence boundary

All break-even and incremental budget values use deterministic PNF1 `MODEL_SYNTHETIC` accounting. The capacity serialization law is validated against upstream native execution, but these stop points are not physical LoRa contact limits.

**GATE PROVE FISICHE HW-006** remains unchanged.
