# UC-167 — One-Way / No-Return-Path Bundle Drop Courier

## Problem solved
Some useful contacts are effectively one-way: a moving transmitter may have only a brief outbound opportunity, or acknowledgements may not be available during the contact. Requiring an immediate return path can waste that opportunity.

UC-167 studies delivery that tolerates no in-band acknowledgement and lets reception evidence return later through a different route.

## Actors / nodes
One-way broadcaster, receiving boards, relay/store-and-forward nodes, later receipt collector and experiment controller.

## Why PollicinoNet fits
DTN already separates forward delivery from immediate end-to-end connectivity. Object ID, priority, repetition schedule and later reception receipt are compact. The forward and return paths can be different contacts or different bearers. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: compact signed/public test objects or one-way control where supported by the existing stack.
- BLE/Wi-Fi/LAN: one-way bulk/drop experiments.
- Internet: optional later receipt return.
- Physical transport: delayed receipt/evidence or large one-way content drop.

## Software test now
Emulate a unidirectional lossy link and compare bidirectional handshake assumptions, fixed repetition, bounded priority-aware repetition and repetition plus later out-of-band receipts. Measure simulated completion probability, repeated bytes, head-of-line blocking and later anti-entropy work.

## Real hardware
Use 6–10 boards. During the forward phase disable return traffic by experiment policy, transmit signed public TEST objects and let receivers log what they obtained. Re-enable ordinary store-and-forward later so receipts travel back through another path.

## Messina scenario
A school gateway or authorized mobile node passes a public checkpoint and has only a short outbound opportunity. It drops a signed bulletin, map subset or content manifest; confirmation can return later through ordinary relays.

## Privacy / security
Treat the forward channel as broadcast-capable. Do not expose sensitive plaintext, bound repetition to avoid amplification and do not infer individual presence merely from missing receipts.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-102 covers groupcast plus anti-entropy, UC-002 signed bulletins and UC-159 priority/preemption. UC-167 focuses specifically on a transfer phase with no usable in-band return path.

## Standards signal
The IETF DTN working group published draft-ietf-dtn-btpu-04 on 7 September 2026 for unidirectional, unreliable, frame-based transfer without a return path. UC-167 does not claim BTP-U compatibility on the frozen LoRa PHY; the draft is a design signal for the software experiment.
