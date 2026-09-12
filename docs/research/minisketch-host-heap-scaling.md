# Generic 16-bit minisketch heap-scaling probe

Status: native-host allocation checkpoint, 2026-08-27

## Why this probe exists

The ESP32 cross-compile proves that the pinned generic 16-bit implementation links for Xtensa and adds a manageable static firmware footprint. Static `bss`, however, does not include the dynamic vectors used by minisketch during decode.

Before asking for a physical-board runtime test, this probe measures the allocation shape of the exact pinned generic 16-bit upstream implementation on a native host.

It is not an ESP32 heap measurement. The purpose is to determine whether the remaining embedded uncertainty is small enough to justify a board micro-benchmark and to identify dangerous over-provisioning regimes in advance.

## Upstream and instrumentation

Pinned upstream:

```text
bitcoin-core/minisketch
4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
```

Build:

```text
generic implementation only
DISABLE_DEFAULT_FIELDS
ENABLE_FIELD_16
-O2
```

`tools/minisketch_heap_probe.cpp` overrides C++ `new/delete` and records retained and peak allocated bytes around:

- sketch create;
- adding set elements;
- serialization;
- receiver destruction;
- source-side remote sketch creation;
- merge;
- decode;
- final destruction.

The receiver-side sketch is destroyed before the source-side remote/decode phase so the probe does not artificially place three sketches on one logical node.

Caller-owned serialization and decode-output buffers use `malloc` and are intentionally excluded from the C++ allocation counter; their sizes are separately known from capacity.

## Validation

GitHub Actions `33087611230` — PASS.

The validation checks every capacity point and verifies all tracked allocations return to baseline after destruction.

## Measured allocation pattern

Actual symmetric difference remains 20 throughout the scaling probes.

| Capacity | Raw sketch | One sketch retained | Two source-side sketches retained | Decode temporary peak above pre-decode state |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 40 B | 104 B | 208 B | 5,326 B |
| 21 | 42 B | 106 B | 212 B | 5,592 B |
| 32 | 64 B | 128 B | 256 B | 8,518 B |
| 64 | 128 B | 192 B | 384 B | 17,030 B |
| 128 | 256 B | 320 B | 640 B | 34,054 B |
| 256 | 512 B | 576 B | 1,152 B | 68,102 B |
| 512 | 1,024 B | 1,088 B | 2,176 B | 136,198 B |
| 1,024 | 2,048 B | 2,112 B | 4,224 B | 272,390 B |

For this pinned generic host build the observed formulas are exact at all tested checkpoints:

```text
one sketch retained              = 2 * capacity + 64 B
two source-side sketches retained = 4 * capacity + 128 B
decode temporary peak             = 266 * capacity + 6 B
```

The persistent formula is consistent with a 16-bit syndrome vector plus host-side object/vector overhead. The decode factor comes from the temporary vectors used by syndrome reconstruction, Berlekamp-Massey and root/factorization work in the current upstream implementation.

These formulas are observations of this host ABI/build, not an upstream API contract and not an ESP32 guarantee.

## Current Pollicino case

The discriminating partial-cache case has true difference 20.

Upstream capacity policy previously measured:

```text
max_elements=20, fpbits=32 -> capacity 20
max_elements=20, fpbits=64 -> capacity 21
```

Corresponding host allocation checkpoints:

```text
capacity 20:
    two source-side sketches =   208 B
    decode temporary peak    = 5,326 B

capacity 21:
    two source-side sketches =   212 B
    decode temporary peak    = 5,592 B
```

This is small enough on the host model that an actual ESP32 runtime micro-benchmark is now justified rather than blocked by an obvious multi-hundred-kilobyte requirement.

## Over-provisioning warning

Wire-budget experiments showed that large capacities can remain cheaper than a 6.8 KB absolute summary for a long time. Heap tells a different story.

For example:

```text
capacity 512  -> ~136 KB temporary decode allocation
capacity 1024 -> ~272 KB temporary decode allocation
```

The generic PlatformIO target reports 320 KB total RAM before application/runtime demands. Therefore a wire-only adaptive policy is insufficient for embedded use.

This does **not** prove the exact LILYGO failure point, because host pointer/object layout and the Arduino/FreeRTOS heap differ. It does establish a strong architectural constraint:

> any embedded PNA2-minisketch selector must be bounded by an explicit memory budget as well as a wire budget.

Do not choose that memory limit from the host numbers alone.

## Gate decision

**Host dynamic-allocation gate: PASS for continuing to physical embedded measurement at capacities around 20/21/32.**

**High-capacity embedded use remains unproven and likely risky.**

The next evidence needed for embedded adoption is now genuinely physical/runtime:

- compile/upload the same generic 16-bit implementation to the actual LILYGO/ESP32-PICO-D4;
- log free heap before create, after sketch creation, before decode and at decode peak if measurable;
- run capacity 20, 21 and 32 first;
- measure create/populate/serialize/merge/decode times;
- verify exact 20-element reconciliation repeatedly;
- verify watchdog/reset stability;
- only then consider higher capacities.

This embedded micro-benchmark does not require changing the LoRa PHY or transmitting anything over RF.

## Relation to physical gates

The existing **GATE PROVE FISICHE HW-006** remains the gate for LoRa distance/NLOS/contact-capacity claims.

Minisketch now has a separate **embedded-runtime evidence gate**: actual ESP32 execution is required before saying the algorithm is suitable for the student node firmware. Cross-compilation and host allocation data are not enough for that claim.
