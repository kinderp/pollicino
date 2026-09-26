# Symmetric partial-cache reconciliation — minisketch gate

Status: MODEL_THEORETICAL + MODEL_SYNTHETIC gate checkpoint, 2026-08-27

## Why revisit advanced set reconciliation?

The first PNA2 experiments deliberately deferred minisketch/IBLT because simple exact representations already solve important asymmetric regimes:

- few isolated missing chunks -> sparse uint16 list;
- contiguous gaps -> ranges;
- highly structured state -> compressed bitmap;
- high-entropy state -> keep PNA1.

A richer algorithm is justified only if there is a concrete state pattern those absolute representations handle badly.

`UC-CONTENT-001` supplies such a pattern: two mobile peers may both carry large **partial** caches of the same object after different opportunistic histories. They can share most present chunks and most absent chunks while differing in only a handful of chunks.

In that regime, describing absolute availability repeats a large amount of information both peers effectively agree on.

## Discriminating synthetic cache state

Current manifest limit:

```text
65,535 chunks
```

Deterministic test state:

```text
common available chunks: 50,000
LEFT-only chunks:            10
RIGHT-only chunks:           10

LEFT available total:    50,010
RIGHT available total:   50,010
symmetric difference:        20
```

The common 50,000-chunk set is pseudo-randomly distributed over the manifest to avoid making the absolute bitmap artificially easy for a range codec.

## Best simple absolute representations

Validation run `33083370213` reports:

```text
LEFT best absolute:  bitmap_zlib  6,789 B
RIGHT best absolute: bitmap_zlib  6,790 B
```

So even after the simple PNA2 codec work, either peer still needs roughly 6.8 KB to describe its absolute state in this constructed regime.

Two absolute descriptions total 13,579 B.

## Why minisketch is relevant here

The minisketch/PinSketch property used for this gate is documented by the upstream project:

- a sketch over `b`-bit set elements with capacity `c` occupies `b*c` bits;
- sketches can be XOR-combined to obtain a sketch of the symmetric difference;
- decoding succeeds when the actual difference does not exceed the chosen capacity.

Current chunk indices fit a 16-bit set-element model after an `index + 1` mapping, avoiding the zero field element.

This checkpoint does **not** implement or vendor minisketch. It uses only that documented size law to determine whether an implementation prototype is justified.

## Conservative theoretical checkpoint

Actual symmetric difference:

```text
20 elements
```

Modeled sketch capacity:

```text
32 elements
```

This deliberately provides headroom rather than giving the sketch an exact-difference oracle.

With the same 40-byte research envelope used by the simple PNA2 experiments:

```text
sketch = 40 + (16 * 32 / 8)
       = 104 B
```

For one-way LEFT -> RIGHT synchronization, RIGHT can classify the decoded symmetric-difference indices using its local set and request the ten chunks that exist only on LEFT.

Conservative request representation:

```text
40-byte envelope + 10 * uint16
= 60 B
```

Total modeled one-way reconciliation control:

```text
104 + 60 = 164 B
```

versus the current best RIGHT absolute summary:

```text
6,790 B
```

This is more than a 40x source-byte difference in this deliberately discriminating state pattern, before PNF1 fragmentation/ACK effects are considered.

The gate test also fails closed when sketch capacity is set to 19 for an actual difference of 20. No over-capacity decode success is assumed.

## Validation

GitHub Actions `33083370213`:

- full project suite: 282 passed, 2 skipped;
- symmetric partial-cache gate tests: 3 passed.

Printed checkpoint:

```text
left_absolute  = bitmap_zlib 6789
right_absolute = bitmap_zlib 6790
two_absolute   = 13579
symmetric_difference = 20
modeled_sketch = 104
modeled_request = 60
modeled_one_way_control = 164
```

## Gate decision

### minisketch / PinSketch

**Decision: PROTOTYPE CANDIDATE for symmetric partial-cache reconciliation.**

This is the first current PollicinoNet use case that justifies an actual advanced set-reconciliation prototype rather than a literature-only note.

Before adoption, an implementation must still be compared against:

- the simple absolute PNA1/PNA2 family;
- CPU/RAM/decode cost on target hardware;
- capacity underestimation/extension behavior;
- collision/security mapping of chunk indices or hashes;
- actual PNF1 wire cost including sketch/request framing;
- malicious-input / decode-work limits;
- backward-compatible capability negotiation.

### Rateless IBLT

**Decision: RESEARCH ONLY for now.**

Rateless IBLT is attractive when the difference size is unknown and incremental symbols should be sent until reconciliation succeeds. But minisketch documentation itself describes incremental sketch extension strategies, so a rateless implementation is not yet justified solely by uncertainty in this use case.

Rateless IBLT should get its own prototype gate only if measured/software experiments show that minisketch capacity estimation/extension or decode cost is a material problem for PollicinoNet.

## Architectural implication

PNA2 should not be one codec. The research is converging toward a regime selector:

```text
known manifest / absolute state
    -> PNA1 | sparse | range | compressed bitmap

near-identical large partial caches
    -> set-reconciliation candidate (minisketch prototype)
```

The selector itself remains research until the advanced path is implemented and benchmarked.

## References

- Bitcoin Core minisketch documentation, `doc/math.md` and `doc/protocoltips.md`.
- BIP 330 / Erlay reconciliation protocol as a deployed-design reference for negotiated sketch-based set reconciliation.
- Yang, Gilad, Alizadeh, *Practical Rateless Set Reconciliation* (Rateless IBLT), 2024.

## Evidence boundary

The minisketch values here are theoretical encoded-size modeling, not an implementation result. All Pollicino codec values are deterministic software measurements. No real LoRa airtime, energy, capacity or field claim is made.

Physical evidence remains behind **GATE PROVE FISICHE HW-006**.
