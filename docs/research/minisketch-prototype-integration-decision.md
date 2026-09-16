# Minisketch prototype integration decision

Status: research integration decision, 2026-08-27

## Context

The symmetric partial-cache gate is the first current PollicinoNet use case that makes advanced set reconciliation materially different from the simple absolute PNA1/PNA2 codec family.

The next question is not whether the PinSketch mathematics can be reimplemented. It is whether Pollicino should do that at all.

## Upstream prior art

The maintained `bitcoin-core/minisketch` project provides `libminisketch`:

- standalone implementation of PinSketch/BCH-based set reconciliation;
- MIT license;
- C++11 implementation;
- public C API;
- deterministic serialized sketch format independent of internal implementation;
- CMake and Autotools build paths;
- cross-compilation examples for Windows;
- explicit APIs for create/add/serialize/deserialize/merge/decode;
- protocol-design guidance covering capacity, hashing/collisions, decode-work limits and incremental extension strategies.

No Python binding with comparable upstream status was identified in the integration survey. Similarly named Python projects found by search implement unrelated count-min sketches and must not be confused with `libminisketch`.

## Gate decision

**Do not implement BCH/PinSketch ourselves.**

That would add substantial correctness, performance and security surface without a Pollicino-specific use case for owning the mathematics.

### First actual prototype target

Build an **optional host-side adapter** around the upstream C API and pin the upstream source/version used by the experiment.

The adapter should be research-only initially and expose only the operations needed for the discriminating partial-cache test:

```text
create 16-bit sketch(capacity)
add chunk-index+1 elements
serialize
merge local/remote sketch
decode symmetric difference
classify decoded indices against local availability
produce exact missing/request indices
```

The existing simple PNA1/PNA2 codec family remains the mandatory baseline.

### Do not yet

- vendor a home-grown finite-field/BCH implementation;
- make `libminisketch` a mandatory Pollicino dependency;
- export it from stable `pollicino.net` API;
- change PNA1 wire behavior;
- reserve a production PND1 capability bit;
- assume the library is suitable for ESP32 firmware;
- claim CPU/RAM suitability on the LILYGO hardware without measurement.

## Host first, embedded later

A host-side prototype can answer the immediate research questions:

- exact encode/decode behavior;
- actual serialized sketch bytes;
- capacity-extension behavior;
- CPU and memory cost on CI/desktop;
- PNF1 fragmentation/ACK/retry cost;
- comparison with simple PNA2 codecs.

Only if that experiment remains useful should embedded portability become a separate use case/gate.

This matters because upstream optimizations and performance characteristics are architecture-dependent, while Pollicino's current physical board is resource constrained compared with a desktop.

## Security/evidence constraints

The upstream protocol guidance notes that short hashed set elements can create collision/security considerations and that decode work should be bounded against denial-of-service inputs.

For the current PCM1 universe, chunk indices are already unique under one manifest and fit a 16-bit `index+1` representation, so the first prototype does not need to hash arbitrary external identifiers into 16 bits. The manifest fingerprint remains the namespace boundary.

A future generalized object-ID reconciliation layer would require a separate collision/authentication design.

## Rateless IBLT

Rateless IBLT remains RESEARCH ONLY. It should not be implemented merely because its unknown-difference behavior is elegant. First measure whether upstream minisketch capacity extension or decode cost is actually a problem in Pollicino's use cases.

## Evidence boundary

This decision is based on literature/upstream implementation inspection plus the existing MODEL_THEORETICAL gate. No host minisketch execution or embedded benchmark is claimed yet. No physical LoRa claim is involved.
