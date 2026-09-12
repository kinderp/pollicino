# Incremental minisketch capacity checkpoint

Status: optional native host experiment, 2026-08-27

## Question

Rateless IBLT was kept as RESEARCH ONLY because upstream minisketch guidance already describes incremental sketch extension when the symmetric-difference size is not known in advance.

This checkpoint tests that property with the actual pinned `libminisketch`, rather than relying only on documentation.

## State

Same discriminating partial-cache case:

```text
65,535 manifest chunks
LEFT available  = 50,010
RIGHT available = 50,010
actual symmetric difference = 20
```

Upstream pin:

```text
bitcoin-core/minisketch
4a179c61e3cbe3ac2b3c027764ce8eb5183155e1
```

## Serialization prefix property

A 16-bit capacity-32 sketch serializes to 64 bytes.

The experiment separately builds capacity 8, 16 and 20 sketches from the same set and verifies byte-for-byte:

```text
capacity 8  serialization == first 16 bytes of capacity 32
capacity 16 serialization == first 32 bytes of capacity 32
capacity 20 serialization == first 40 bytes of capacity 32
```

Therefore a sender can compute a sufficiently large sketch once and reveal additional serialization bytes without retransmitting the prefix already sent.

## Native decode result

GitHub Actions `33084930028` — PASS.

Ordinary suite without native dependency:

```text
282 passed, 7 skipped
```

Native adapter + incremental tests:

```text
5 passed
```

Actual prefix decode checkpoint:

| Capacity | Raw bytes received | Native decode success | Exact 20-element difference |
| ---: | ---: | --- | --- |
| 8 | 16 | no | no |
| 16 | 32 | no | no |
| 20 | 40 | yes | yes |
| 32 | 64 | yes | yes |

This particular under-capacity state returned explicit decode failure for 8 and 16. A production protocol must not assume all under-capacity cases fail cleanly: upstream documents a false-decode probability when a sketch is overfull. False-positive bounds remain part of the protocol/security design.

## Simple doubling experiment

Unknown-difference policy modeled:

```text
send capacity 8 prefix
if not exact/accepted -> extend to 16
if not exact/accepted -> extend to 32
```

Raw sketch bytes sent across all rounds:

```text
16 + 16 + 32 = 64 bytes
```

So no raw sketch byte is retransmitted.

For conservative experimental messages, each round still pays a 40-byte envelope and PNF1 framing/ACK overhead.

Modeled PNF1 result:

```text
one-shot capacity 32 sketch + final request =   294 B
incremental 8 -> 16 -> 32 + final request =    452 B
best absolute availability representation = 10,637 B
```

Incremental negotiation therefore costs 158 modeled wire bytes more than knowing capacity 32 in advance, but remains more than 20x smaller than the best absolute summary in this discriminating state.

The important point is not that 8/16/32 is the optimal sequence. It is that uncertainty can already be handled with bounded incremental minisketch extension without introducing another reconciliation family.

## Gate decision

### Incremental minisketch

**PROTOTYPE / CONTINUE.**

Next protocol work should focus on:

- false-positive target / `minisketch_compute_capacity` policy;
- bounded extension steps;
- exact acceptance/verification rules;
- fallback to the best absolute PNA1/PNA2 representation before extension becomes wasteful;
- protection against decode-work denial of service.

### Rateless IBLT

**Remain RESEARCH ONLY / DEFER.**

The current use case does not yet demonstrate a material problem that requires Rateless IBLT. Minisketch already supports an incremental path that reuses previously transmitted raw sketch bytes and remains dramatically below the absolute-state cost in the tested regime.

Rateless IBLT should get an implementation gate only if later evidence shows that minisketch extension, false-positive overhead or quadratic decode cost becomes the actual bottleneck.

## Evidence boundary

Prefix identity and decode behavior are actual host execution of the pinned upstream library. The 294/452/10,637-byte values use deterministic PNF1 MODEL_SYNTHETIC accounting. No real LoRa or embedded-performance claim is made.

**GATE PROVE FISICHE HW-006** remains unchanged.
