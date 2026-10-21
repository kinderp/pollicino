# Minisketch ESP32 cross-compile feasibility

Status: toolchain/static-footprint checkpoint, 2026-08-27

## Question

Before involving the physical LILYGO boards, can the pinned upstream minisketch generic 16-bit implementation compile and link for an ESP32 Xtensa target without x86 CLMUL support, and what static linked footprint does it add to a minimal Arduino firmware?

This is a compile-feasibility gate only. It does not measure runtime correctness, heap use, execution time or power on the actual board.

## Upstream and target

Pinned upstream:

```text
bitcoin-core/minisketch
4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
```

CI target:

```text
PlatformIO 6.1.19
platform espressif32 7.0.1
board esp32dev
Arduino-ESP32 3.20017.241212+sha.dcc1105b
Xtensa toolchain 8.4.0+2021r2-patch5
ESP32 240 MHz / 320 KB RAM / 4 MB Flash model
```

The physical Pollicino board remains the LILYGO/TTGO LoRa32 V1.6.1 with ESP32-PICO-D4; this generic `esp32dev` compile does not claim exact board-level behavior.

## Restricted upstream build

The experimental firmware copies only:

- public `minisketch.h`;
- `minisketch.cpp`;
- required upstream headers;
- generic field implementation sources;

and deliberately excludes CLMUL source files.

Build flags restrict enabled fields:

```text
-D DISABLE_DEFAULT_FIELDS
-D ENABLE_FIELD_16
```

This keeps the current PCM1 namespace mapping available while avoiding unused field widths at runtime.

A tiny setup function actually references the API so the linker cannot discard the library entirely:

```text
create 16-bit capacity-32 sketch
add element 1
add element 65535
serialize
free
```

## Validation

GitHub Actions `33086788479` — PASS.

Both builds succeeded:

1. baseline Arduino `esp32dev` firmware;
2. generic-16-bit minisketch firmware.

Therefore the pinned generic implementation is syntactically/toolchain compatible with this Xtensa ESP32 build path without x86 CLMUL.

## PlatformIO headline usage

Baseline:

```text
RAM   21,464 B / 327,680 B = 6.6%
Flash 266,993 B / 1,310,720 B = 20.4%
```

Minisketch firmware:

```text
RAM   21,480 B / 327,680 B = 6.6%
Flash 286,193 B / 1,310,720 B = 21.8%
```

Headline delta:

```text
static RAM: +16 B
Flash:      +19,200 B
```

## ELF section comparison

`xtensa-esp32-elf-size`:

| Section | Baseline | Minisketch | Delta |
| --- | ---: | ---: | ---: |
| text | 197,177 | 205,973 | +8,796 B |
| data | 70,072 | 80,476 | +10,404 B |
| bss | 4,937 | 4,953 | +16 B |
| dec | 272,186 | 291,402 | +19,216 B |

Firmware binaries:

```text
baseline firmware.bin   = 267,360 B
minisketch firmware.bin = 286,560 B
delta                   = 19,200 B
```

## Interpretation

A roughly 19 KB linked binary increase is not an obvious blocker for the modeled ESP32 partition: the test firmware remains around 21.8% of the reported 1.31 MB application space.

However, the tiny `bss` increase is **not evidence that minisketch needs only 16 bytes of RAM**.

Upstream `SketchImpl` stores its syndromes in a dynamic `std::vector`. For the 16-bit implementation, persistent syndrome payload alone scales approximately with:

```text
2 bytes * sketch capacity
```

and decode constructs additional temporary vectors for reconstructed syndromes, Berlekamp-Massey state and root finding/factorization.

Those are heap allocations and do not appear in static `bss`.

## Gate decision

**ESP32 cross-compile/static footprint: PASS / CONTINUE.**

This result is sufficient to justify measuring dynamic allocation and runtime behavior; it is not sufficient to adopt minisketch on the embedded node.

Before physical-board use, perform a host native allocation-trace benchmark to bound:

- heap remaining after create;
- peak heap during population;
- peak heap during merge/decode;
- scaling with capacities relevant to Pollicino (20/32/64/128/...);

Then the remaining embedded gate becomes small and explicit:

- actual ESP32 free heap before/after;
- peak heap during decode;
- build/merge/decode latency;
- watchdog/reset stability.

## Evidence boundary

This is real cross-compilation/link evidence for a generic ESP32 target, not runtime execution on the LILYGO board. It makes no radio, energy or hardware-performance claim.

The radio evidence gate remains **GATE PROVE FISICHE HW-006**. Embedded minisketch runtime suitability is a separate future hardware micro-benchmark gate.
