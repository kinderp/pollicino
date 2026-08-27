# HW-MSK-001 — LILYGO minisketch embedded-runtime probe

Status: **SOFTWARE READY; physical execution pending**

## Purpose

This probe answers one narrow question before any embedded PNA2-minisketch adoption:

> Can the pinned generic 16-bit `libminisketch` run repeatedly and exactly on the actual LILYGO LoRa32 V1.6.1 / ESP32-PICO-D4 with acceptable heap use and latency at the capacities relevant to the current partial-cache use case?

It is deliberately **not a LoRa test**.

The firmware:

- does not initialize SX1276;
- does not transmit RF;
- does not change H2 or the frozen PHY;
- uses USB serial only;
- tests capacities 20, 21 and 32;
- runs five trials per capacity;
- reconciles a deterministic 20-element symmetric difference;
- logs exactness, free/min heap, largest free block and phase timings.

## Software/build checkpoint

GitHub Actions `33088214482` — **PASS**.

The exact probe project was validated with:

```text
PlatformIO 6.1.19
espressif32@6.13.0
board esp32dev
Arduino-ESP32 3.20017.241212+sha.dcc1105b
Xtensa toolchain 8.4.0+2021r2-patch5
upstream minisketch commit 4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
```

Validation covered:

- Python `prepare.py` syntax: PASS;
- Python `capture.py` syntax: PASS;
- pinned upstream dependency preparation: PASS;
- full firmware compile/link: PASS;
- upstream pin file verification: PASS.

PlatformIO-reported footprint:

```text
RAM:   21,480 / 327,680 B = 6.6%
Flash: 289,977 / 1,310,720 B = 22.1%
```

ELF sections:

```text
text = 207,709 B
data =  82,524 B
bss  =   4,953 B
dec  = 295,186 B
```

Generated `firmware.bin`:

```text
290,336 B
```

These are build/static-footprint facts only. They do not prove runtime heap use or speed on the physical ESP32-PICO-D4.

## Why capacities 20 / 21 / 32

For the current discriminating use case the true difference is 20.

Pinned upstream `minisketch_compute_capacity()` previously returned:

```text
max_elements=20, fpbits=32 -> capacity 20
max_elements=20, fpbits=64 -> capacity 21
```

Capacity 32 is the conservative/incremental doubling checkpoint already validated on host.

Host allocation probes measured about 5.3 KB, 5.6 KB and 8.5 KB of temporary decode allocation at those capacities, but **those are not ESP32 measurements**.

## Upstream pin

The dependency is not vendored into the repository.

`prepare.py` fetches exactly:

```text
https://github.com/bitcoin-core/minisketch.git
4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
```

and copies only the public header, core source, headers and generic field sources into the ignored local `lib/minisketch/` directory.

Build flags enable only the 16-bit field and do not compile CLMUL implementations.

## Prepare and build

From the repository root:

```bash
python -m pip install platformio==6.1.19 pyserial
python hardware/lilygo-lora32-v1.6.1/minisketch-probe/prepare.py
pio run -d hardware/lilygo-lora32-v1.6.1/minisketch-probe
```

The PlatformIO environment deliberately matches the existing LILYGO project family:

```text
espressif32@6.13.0
board=esp32dev
Arduino
115200 serial
921600 upload
```

## Physical execution

This is the point where an actual board becomes necessary.

Only **one** LILYGO is needed. Because the radio is never initialized, an antenna is not required for this specific CPU/RAM probe; if the antenna is already attached, leave it attached.

Visually confirm the board is the expected LoRa32 V1.6.1 / ESP32-PICO-D4 before flashing.

Example on Windows:

```bash
pio run -d hardware/lilygo-lora32-v1.6.1/minisketch-probe \
  -t upload --upload-port COM3

python hardware/lilygo-lora32-v1.6.1/minisketch-probe/capture.py \
  --port COM3 \
  --output hardware/lilygo-lora32-v1.6.1/physical-validation/minisketch-runtime.json
```

Use the actual COM port shown by Windows. The existing boards have previously appeared on COM3/COM4, but do not assume the mapping without checking the current device list.

## Firmware workload

Each trial builds two deterministic sets in the same 16-bit namespace:

```text
common elements: 1..50,000
source-only:     50,001..50,010
receiver-only:   50,011..50,020
```

Expected symmetric difference:

```text
50,001..50,020 = 20 elements
```

Receiver-side behavior:

```text
create sketch
add 50,010 elements
serialize
free receiver sketch
```

Source-side behavior:

```text
create source sketch
add 50,010 elements
create/deserialise remote sketch
merge
allocate decode output
native decode
verify exact 20-element difference
free everything
```

## Serial evidence

Firmware emits machine-readable lines such as:

```text
MSP_RESULT capacity=20 trial=0 exact=1 decoded=20 serialized=40 ...
MSP_CLEANUP capacity=20 trial=0 free=... start_free=... delta=...
```

`capture.py` requires:

- 15 result lines total;
- 5 trials each for capacities 20, 21, 32;
- every trial `exact=1`;
- no `MSP_FAIL` / `MSP_FATAL`;
- cleanup free-heap deltas within 32 bytes;
- final `MSP_DONE`.

It then writes a JSON report with timing medians/min/max and heap minima.

## Success criteria

HW-MSK-001 passes only if:

1. all 15 trials decode the exact 20-element difference;
2. no reset/watchdog/fatal allocation occurs;
3. cleanup does not show a meaningful repeated heap leak;
4. minimum free heap remains comfortably above zero at capacity 32;
5. largest free block remains large enough to show no obvious fragmentation crisis;
6. timings are finite/stable enough that capacity 20/21/32 is operationally plausible.

No hard millisecond threshold is preregistered yet because we have no embedded measurement baseline. The first run is characterization, not a pass/fail performance race.

## What a PASS permits

A physical PASS would support:

- “generic 16-bit minisketch is executable on the actual Pollicino ESP32 board at capacities 20/21/32”;
- measured heap/timing evidence for those exact capacities;
- continued design of an embedded bounded minisketch availability path.

It would **not** support:

- higher capacity safety;
- real LoRa airtime/energy savings;
- radio coexistence with LoRaMesher/FreakWAN/Pollicino RF runtime;
- final production PNA2 adoption.

## Relation to HW-006

HW-MSK-001 is a CPU/RAM runtime probe and can be performed on a desk with one board and USB.

**GATE PROVE FISICHE HW-006** remains separate and is still required for LoRa distance/NLOS/contact-capacity claims. This probe neither advances nor invalidates that radio gate.
