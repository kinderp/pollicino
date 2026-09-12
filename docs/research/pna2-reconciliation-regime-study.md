# PNA2 reconciliation — regime study under the use-case gate

Status: literature/design checkpoint, 2026-08-25

This document corrects and refines the earlier set-reconciliation discussion using the actual current PCM1/PNA1 wire limits.

## 1. Current protocol reality

Current `PCM1` limits the chunk count to `MAX_CHUNKS = 0xFFFF = 65,535`.

Therefore a one-million-chunk manifest is **not currently representable** and must not be used as a present-tense PNA2 justification without first justifying a future manifest-version change.

Current PNA1 encodes:

- magic: 4 bytes;
- version: 1 byte;
- manifest fingerprint: 32 bytes;
- chunk count: 2 bytes;
- availability bitmap: `ceil(N/8)` bytes.

So:

`PNA1_bytes = 39 + ceil(N / 8)`

At the current maximum `N = 65,535`:

`PNA1 = 39 + 8,192 = 8,231 bytes`.

That is already a meaningful scarce-link control cost and is sufficient to justify a PNA2 experiment without inventing a larger future manifest.

## 2. Concrete use cases

PNA2 passes the feature gate for at least two concrete cases.

### UC-PNA2-A — complete source, almost-complete receiver

A complete source and receiver share the same PCM1 manifest. The receiver is missing only a small number `d` of chunk indices.

Goal: tell the source exactly what is missing with substantially fewer bytes than a full bitmap.

### UC-PNA2-B — partial relay meets another partial relay

Both peers have different partial subsets of the same manifest. Neither is a complete source and the direction of the difference is not known by one side in advance.

Goal: learn useful symmetric difference information without first exchanging a full 8-KB bitmap in the maximum PCM1 regime.

These are materially different regimes and should not be forced through one codec.

## 3. Simplest baseline: sparse index list

Because PCM1 currently has at most 65,535 chunks, every chunk index fits in 16 bits.

If a PNA2 sparse format reused a PNA1-like 39-byte fixed header, a list of `d` missing indices would cost approximately:

`39 + 2d` bytes.

Ignoring small mode-specific fields, sparse-list payload beats raw bitmap when:

`2d < ceil(N/8)`

or approximately:

`d < N / 16`.

So the sparse list wins below roughly **6.25% missing chunks**.

Examples at `N = 65,535`:

| Missing chunks d | Raw PNA1 | Sparse index approximation |
| ---: | ---: | ---: |
| 1 | 8,231 B | 41 B |
| 5 | 8,231 B | 49 B |
| 20 | 8,231 B | 79 B |
| 100 | 8,231 B | 239 B |
| 1,000 | 8,231 B | 2,039 B |
| 4,000 | 8,231 B | 8,039 B |
| 4,096 | 8,231 B | 8,231 B |

This means a simple sparse list is an extremely strong baseline for `complete source -> receiver missing a few chunks`.

## 4. Range / run-length representation

When missing chunks occur in contiguous runs, encode `(start, length)` using two 16-bit values per range.

Approximate size:

`39 + 4r` bytes

where `r` is the number of missing ranges.

Range encoding beats the sparse list when:

`4r < 2d`, i.e. `r < d/2`.

In simple terms: average missing-run length greater than about two chunks makes ranges attractive.

Concrete use case:

- interrupted sequential transfer leaves one or a few contiguous suffix/ranges missing.

This is likely common in bounded contact windows and should be benchmarked before any sketch algorithm.

## 5. Compressed bitmap

A compressed bitmap can win when missing/available bits have structure but are not sparse enough for a short index list.

Possible prototype choices should initially remain dependency-light, for example:

- simple byte-level RLE;
- range encoding;
- a standard general compressor only if its CPU/RAM and framing cost are justified.

Do not introduce a compression dependency until the simpler range codec loses on a target workload.

## 6. Minisketch / PinSketch regime

`minisketch` implements a BCH/PinSketch-style set reconciliation primitive.

Important property:

- for `b`-bit elements and difference capacity `c`, the sketch stores approximately `b*c` bits;
- two sketches XOR to a sketch of the symmetric difference;
- decode succeeds when actual difference does not exceed configured capacity.

For current PCM1 chunk indices, `b = 16` is sufficient.

Therefore a capacity-`d` minisketch has payload around:

`16d bits = 2d bytes`.

That is **not smaller than directly sending `d` uint16 indices** when one peer already knows exactly which indices the other side needs.

This is a crucial regime result:

> minisketch is not justified for UC-PNA2-A merely as a byte-saving replacement for a missing-index list.

Its value appears in UC-PNA2-B:

- both sides are partial;
- neither side knows the symmetric difference;
- one compact sketch can reveal both directions of difference;
- set size can be huge relative to difference without sketch size growing with `N`.

### Gate decision

**PROTOTYPE only for symmetric/partial-relay reconciliation.**

Do not use minisketch by default for complete-source transfers unless CPU/round-trip behavior gives a measured advantage in some specific regime.

## 7. IBLT regime

IBLTs support insertion/deletion and probabilistic listing of a set difference. Literature and minisketch's own comparison notes show that IBLT communication often carries an overhead factor relative to near-optimal `b*c` sketches, but decoding can be linear-time and operationally attractive.

Potential Pollicino use case:

- partial/partial reconciliation;
- differences not arranged as simple contiguous ranges;
- larger difference cardinalities where quadratic-ish sketch decoding becomes undesirable;
- CPU is more valuable than minimum possible wire size.

Risks:

- probabilistic decode failure;
- parameter sizing;
- more complex failure/retry semantics;
- adversarial hash/collision considerations.

### Gate decision

**RESEARCH/PROTOTYPE after sparse/range/minisketch baselines.**

It does not pass adoption merely because it is asymptotically elegant.

## 8. Rateless IBLT / rate-compatible reconciliation

Recent rateless/rate-compatible reconciliation work attacks a real weakness of fixed-capacity sketches/IBLTs: the sender may not know the difference cardinality in advance.

Rateless IBLT incrementally emits coded symbols until the receiver has enough information to decode.

Concrete Pollicino use case:

> Two partial relays meet for an uncertain contact duration; neither knows the symmetric-difference size, and every extra round-trip is expensive. The sender should progressively transmit reconciliation information without choosing an oversized fixed structure up front.

This aligns strongly with intermittent contacts.

But current PCM1's structured 16-bit shared universe makes simpler adaptive schemes strong competitors, e.g.:

- send a small-capacity sketch first and extend only on failure;
- sparse/range mode when one direction becomes known;
- raw bitmap when difference is dense.

### Gate decision

**DEFER until simpler adaptive PNA2 codecs are measured.**

Reopen when unknown symmetric difference + short/one-way contacts is demonstrated as a material target regime.

## 9. PNA2 should be a codec-selection experiment, not one algorithm

The prototype should expose codecs behind one experimental interface without changing frozen PNA1 semantics initially.

Suggested candidates:

1. `bitmap` — exact PNA1 baseline;
2. `missing_u16` — sparse missing indices;
3. `missing_ranges_u16` — contiguous ranges;
4. `simple_compressed_bitmap` — only if justified by traces;
5. `minisketch16` — symmetric partial/partial baseline;
6. `iblt16` — optional after previous measurements;
7. `rateless` — only after an unknown-difference use case demonstrates need.

## 10. Regime map

| Regime | First codec to beat |
| --- | --- |
| complete source, receiver missing very few chunks | `missing_u16` |
| complete source, contiguous missing suffix/ranges | `missing_ranges_u16` |
| complete source, dense/irregular missing state | raw/compressed bitmap |
| partial peer vs partial peer, known small difference bound | minisketch |
| partial/partial, larger difference where CPU dominates | IBLT candidate |
| partial/partial, unknown difference, expensive feedback | rateless candidate |

No codec should be declared universally superior.

## 11. Minimal falsifiable benchmark

Use current-valid chunk counts only first:

`N = 64, 256, 1,024, 4,096, 16,384, 65,535`.

Difference regimes:

- `d = 0, 1, 5, 20, 100, 1,000`;
- 1%, 5%, 10%, 25%, 50%, 90% where valid.

Patterns:

- random sparse;
- contiguous suffix;
- several ranges;
- alternating/dense;
- two partial peers with symmetric difference.

Metrics:

- encoded bytes;
- number of contact round trips;
- encode/decode CPU;
- peak RAM;
- deterministic vs probabilistic success;
- bytes spent on failed decode/retry;
- implementation/dependency complexity.

Final SHA-256 reconstruction remains authoritative regardless of reconciliation codec.

## 12. Success / kill rules

### Sparse/range PNA2

Adopt if it materially reduces control bytes in target scenarios with trivial complexity and no weakening of exactness.

### minisketch

Adopt only in a symmetric partial/partial regime where it beats simple alternatives after accounting for CPU/dependency cost.

### IBLT / rateless

Adopt only if they win a demonstrated unknown/symmetric-difference regime that simpler codecs cannot cover efficiently.

## References

- Y. Minsky, A. Trachtenberg, R. Zippel, *Set Reconciliation with Nearly Optimal Communication Complexity*, IEEE Transactions on Information Theory 49(9), 2003, DOI 10.1109/TIT.2003.815784.
- D. Eppstein, M. T. Goodrich, F. Uyeda, G. Varghese, *What's the Difference? Efficient Set Reconciliation without Prior Context*, SIGCOMM 2011.
- M. T. Goodrich, M. Mitzenmacher, *Invertible Bloom Lookup Tables*, Allerton 2011.
- Bitcoin Core, `minisketch`, BCH/PinSketch set-reconciliation implementation.
- L. Yang, Y. Gilad, M. Alizadeh, *Practical Rateless Set Reconciliation*, 2024, arXiv:2402.02668.
