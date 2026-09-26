# One-way minisketch: receiver sketch -> source decision

Status: optional native host research, 2026-08-27

## Correction to the first native checkpoint

The first host-side minisketch experiment used a conservative two-message flow:

```text
LEFT sends sketch -> RIGHT
RIGHT decodes difference
RIGHT sends explicit request indices -> LEFT
```

That flow is valid but is not minimal for Pollicino's ordinary one-way chunk forwarding.

Current PNA semantics already answer a simpler question:

> receiver, tell the source what you already have so the source can avoid sending it again.

The same direction works better with minisketch.

## Minimal one-way flow

For SOURCE -> RECEIVER synchronization:

```text
RECEIVER builds sketch(receiver availability)
        |
        v
SOURCE receives sketch
SOURCE combines it with source availability
        |
        v
symmetric difference
        |
        +-- element SOURCE has     -> source-only -> useful chunk to send
        +-- element SOURCE lacks   -> receiver-only -> ignore in this direction
```

The source therefore learns the exact useful source-only chunk indices directly.

No second request message is required merely to classify the symmetric difference.

## Native implementation

`minisketch_one_way_host.py` is a thin research wrapper over the already validated pinned upstream adapter.

It calls the underlying reconciliation with:

```text
LEFT  = receiver set
RIGHT = source set
```

so the underlying `RIGHT-only` result is exactly the source-only set that can advance the receiver.

## Validation

GitHub Actions `33086210863` — PASS.

- ordinary project suite without native dependency: `288 passed, 12 skipped`;
- pinned upstream build: PASS;
- one-way native tests: `2 passed`.

Discriminating state:

```text
SOURCE-only chunks   = 10
RECEIVER-only chunks = 10
symmetric difference = 20
capacity              = 32
```

Decoded source-only and receiver-only sets match ground truth exactly.

## Wire result

Actual upstream raw sketch:

```text
64 B
```

Conservative research envelope:

```text
40 + 64 = 104 source bytes
```

Existing deterministic PNF1 model:

```text
104 B -> 3 frames -> 182 B modeled wire
```

Best simple absolute receiver availability:

```text
bitmap_zlib
6,790 source bytes
10,638 modeled PNF1 wire bytes
```

Ratio in this deliberately discriminating state:

```text
10,638 / 182 ~= 58.45x
```

The former explicit ten-index request alone cost another 112 modeled PNF1 bytes, making the older two-message result 294 B. That request is no longer part of the preferred one-way research flow.

## Architectural implication

This aligns the advanced reconciliation candidate with existing PNA semantics rather than inventing a new request/response pattern.

A future availability family can conceptually remain:

```text
receiver availability description
        -> source chooses useful chunks
```

where the description may be:

- PNA1 bitmap;
- sparse indices/ranges;
- compressed bitmap;
- minisketch for near-identical large partial caches.

This is preferable to introducing a separate symmetric-sync protocol unless a genuinely bidirectional synchronization use case later requires one.

## Gate decision

**Receiver-sketch one-way minisketch: preferred research shape / CONTINUE.**

The previous two-message sketch+request model remains useful as a conservative comparison, but should not guide a future one-way PNA2 design.

Still no production PNA2 format or capability bit is assigned.

## Evidence boundary

Set-difference correctness and 64-byte serialization are actual host execution of pinned upstream libminisketch. The 182/10,638-byte comparison is deterministic PNF1 `MODEL_SYNTHETIC` accounting.

Real LoRa/embedded evidence remains behind **GATE PROVE FISICHE HW-006**.
