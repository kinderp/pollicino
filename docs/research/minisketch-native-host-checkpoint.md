# Native host-side minisketch checkpoint

Status: optional native host prototype, 2026-08-27

## Goal

The previous symmetric partial-cache gate justified minisketch only from the documented `b*c` size law. This checkpoint asks whether the actual upstream implementation can reproduce the exact Pollicino cache difference, remain optional, and retain the predicted wire advantage when its real serialized bytes pass through PNF1.

## Upstream pin

The experiment uses:

```text
bitcoin-core/minisketch
commit 4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
2026-08-14
```

The upstream repository is cloned only inside the temporary validation workflow. Pollicino does not vendor the implementation and does not add it as a mandatory package dependency.

CMake build configuration:

```text
BUILD_SHARED_LIBS=ON
MINISKETCH_FIELDS=16
MINISKETCH_BUILD_TESTS=OFF
MINISKETCH_BUILD_BENCHMARK=OFF
```

The resulting shared library is loaded by the research-only `minisketch_host.py` adapter through Python `ctypes`.

The ordinary project test suite executes before the native library is built and skips the optional native tests, proving that Pollicino still works without libminisketch.

## Namespace mapping

Current PCM1 chunk indices are:

```text
0 .. 65,534
```

libminisketch field elements for a 16-bit sketch are:

```text
1 .. 65,535
```

The adapter therefore maps:

```text
chunk index i -> field element i + 1
```

This is exact and collision-free for the current PCM1 manifest namespace. No hash truncation is used in the first prototype.

## Discriminating cache state

Same deterministic state as the theoretical gate:

```text
manifest chunks:       65,535
LEFT available:        50,010
RIGHT available:       50,010
LEFT-only:                 10
RIGHT-only:                10
symmetric difference:      20
sketch capacity:            32
field bits:                 16
```

## Native correctness result

GitHub Actions `33084423197` — PASS.

- ordinary full suite without native dependency: `282 passed, 5 skipped`;
- pinned upstream shared library build: PASS;
- optional native adapter tests: `3 passed`.

libminisketch decoded exactly:

```text
decoded symmetric difference = 20
LEFT-only = 10
RIGHT-only = 10
```

The receiver classifies decoded elements using only its local availability set, matching the standard symmetric-difference reconciliation protocol.

## Actual serialized size

Upstream serialization for 16-bit elements, capacity 32:

```text
raw sketch = 64 bytes
```

This exactly matches the documented `16 * 32 / 8` size law.

The experimental Pollicino framing remains deliberately conservative:

```text
40-byte research envelope + 64-byte raw sketch = 104 bytes
40-byte request envelope + 10 * uint16 indices = 60 bytes
```

## PNF1 wire result

Using the same deterministic synthetic PNF1 profile as the availability research:

```text
max_frame_bytes = 64
ack_bytes = 8
```

Actual native reconciliation messages require:

```text
sketch:  104 source bytes -> 3 PNF1 frames
request:  60 source bytes -> 2 PNF1 frames
combined modeled wire = 294 bytes
```

On the same LEFT cache, the best simple absolute representation is:

```text
bitmap_zlib
source bytes = 6,789
modeled PNF1 wire = 10,637 bytes
```

Therefore in this deliberately discriminating partial-cache state:

```text
10,637 / 294 ~= 36.2x
```

The native minisketch path uses roughly 36x less modeled PNF1 wire than the best current absolute availability representation.

This is not a global compression ratio; it applies to this specific near-identical partial-cache regime.

## Host timing observation

One CI-run observation:

```text
build LEFT sketch:  ~97.4 ms
build RIGHT sketch: ~97.0 ms
serialize LEFT:      ~0.008 ms
merge + decode:      ~0.734 ms
```

The two build timings must **not** be treated as native libminisketch performance. Each 50,010-element sketch is populated through about fifty thousand Python-to-C `ctypes` calls, so FFI overhead dominates that measurement.

`merge + decode` is a much cleaner one-call native observation, but even it is only a hosted CI-run data point, not a hardware guarantee.

A native C/C++ benchmark would be needed for useful CPU conclusions, and embedded CPU/RAM measurements remain a separate gate.

## Gate decision

**Host-side libminisketch prototype: PASS / CONTINUE.**

The theoretical gate was confirmed by the actual pinned upstream implementation.

Still do not:

- make libminisketch mandatory;
- expose the adapter as stable top-level API;
- assign a production PND1 capability bit;
- replace PNA1/simple PNA2 codecs;
- claim ESP32 suitability;
- claim real LoRa airtime/energy gains.

The next useful question is capacity uncertainty. Upstream protocol guidance explicitly supports incremental sketch extension and warns against complex estimators that can cost more bandwidth than they save. Before considering Rateless IBLT, test whether a bounded incremental minisketch strategy is sufficient for Pollicino's unknown-difference case.

## Evidence boundary

Correctness and serialization are actual host execution of the pinned upstream library. PNF1 wire numbers remain deterministic `MODEL_SYNTHETIC`. Physical LoRa evidence remains behind **GATE PROVE FISICHE HW-006**.
