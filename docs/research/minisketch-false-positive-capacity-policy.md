# Minisketch false-positive capacity policy checkpoint

Status: optional native host research, 2026-08-27

## Question

An overfull minisketch can have a non-zero false-decode probability. Before a Pollicino protocol can rely on incremental sketches, the capacity must include an explicit false-positive target rather than merely equal an expected difference count.

The upstream C API provides exactly this policy primitive:

```text
minisketch_compute_capacity(bits, max_elements, fpbits)
minisketch_compute_max_elements(bits, capacity, fpbits)
```

This checkpoint asks how expensive that safety margin is for Pollicino's current 16-bit chunk-index namespace.

## Upstream pin and validation

Pinned upstream:

```text
bitcoin-core/minisketch
4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
```

GitHub Actions `33085273271` — PASS:

- ordinary suite without native dependency: `282 passed, 10 skipped`;
- pinned upstream shared-library build: PASS;
- native capacity-policy tests: `3 passed`.

## Actual upstream capacity table

For 16-bit sketches, raw serialized size is exactly `2 * capacity` bytes.

| Decodable elements requested | fpbits | Upstream capacity | Raw bytes | Inverse supported max |
| ---: | ---: | ---: | ---: | ---: |
| 8 | 0 | 8 | 16 | 8 |
| 8 | 16 | 9 | 18 | 9 |
| 8 | 32 | 10 | 20 | 9 |
| 8 | 64 | 12 | 24 | 9 |
| 16 | 0 | 16 | 32 | 16 |
| 16 | 16 | 16 | 32 | 16 |
| 16 | 32 | 16 | 32 | 16 |
| 16 | 64 | 18 | 36 | 17 |
| 20 | 0 | 20 | 40 | 20 |
| 20 | 16 | 20 | 40 | 20 |
| 20 | 32 | 20 | 40 | 20 |
| 20 | 64 | 21 | 42 | 21 |
| 32 | 0 | 32 | 64 | 32 |
| 32 | 16 | 32 | 64 | 32 |
| 32 | 32 | 32 | 64 | 32 |
| 32 | 64 | 32 | 64 | 32 |

## Main result for the discriminating cache case

The actual symmetric difference is 20.

For an upstream false-positive target of roughly:

```text
2^-32
```

the required capacity remains exactly:

```text
20
```

and the raw sketch remains:

```text
40 bytes
```

No bandwidth penalty is needed at this point.

Even a roughly `2^-64` target increases the capacity only from 20 to 21:

```text
40 -> 42 raw bytes
```

The native test confirms that the capacity returned for `max_elements=20, fpbits=32` still decodes the real 20-element difference exactly.

## Interpretation

This table is an upstream algorithm result, not a Pollicino security recommendation.

It nevertheless removes one possible justification for adding a more complicated estimator or Rateless IBLT now:

> in the currently relevant small-difference regime, an explicit strong false-positive margin can cost almost nothing in serialized sketch bytes.

A future protocol still needs to choose its own acceptable false-positive target based on the consequences of a false decode and the exact verification/fallback flow.

## Verification remains mandatory

Even with a bounded false-positive probability, decoded indices must not be treated as authoritative content facts by themselves.

Pollicino should continue to rely on the existing manifest/hash verification path for any retrieved chunk. Reconciliation only identifies candidate differences; it does not replace exact object verification.

## Gate decision

**False-positive-aware minisketch capacity: viable / continue.**

Do not standardize `fpbits=32` or `64` yet. First design the complete acceptance/fallback flow and measure its wire behavior.

**Rateless IBLT remains RESEARCH ONLY / DEFER.**

Current evidence now shows all three of the reasons we initially considered Rateless IBLT can already be addressed cheaply by upstream minisketch:

1. sparse symmetric difference -> native compact sketch;
2. unknown difference -> incremental serialization extension;
3. overfull false-decode risk -> explicit upstream capacity/fpbits policy with small overhead in the tested regime.

A Rateless IBLT implementation now requires a new discriminating use case, not merely architectural curiosity.

## Next gate

The next minimal protocol experiment should combine:

```text
PNA1/simple absolute alternatives
        vs
incremental minisketch
```

with a bounded rule:

- extend the sketch only while its cumulative wire cost remains justified;
- if it becomes more expensive than the best absolute response, fall back;
- decoded differences remain subject to exact manifest/chunk verification.

No production capability bit or PNA2 wire format is assigned by this checkpoint.

## Evidence boundary

Capacity values and decode behavior are actual host calls to the pinned upstream library. Any PNF1 transfer comparison remains MODEL_SYNTHETIC. Embedded/LoRa claims remain behind **GATE PROVE FISICHE HW-006**.
