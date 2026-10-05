# UC-165 — Prepositioned Sealed-Release Package Courier

## Problem solved
A large object may need to be present before it is allowed to be opened. In an intermittent network it is safer to preposition the encrypted bulk object early and later ferry only a compact authenticated release authorization.

## Actors / nodes
Publisher, release authority, sealed-package cache, relay/store-and-forward nodes, authorized recipient and audit collector.

## Why PollicinoNet fits
The encrypted object can move earlier over Wi-Fi, Internet or physical storage. At release time only package hash, release epoch, authorization ID, expiry and optional key-envelope state need to propagate. LoRa remains a control bearer and the frozen PHY is unchanged.

## Bearers
- LoRa: release authorization, exact package ID/hash, epoch and supersession state.
- BLE/Wi-Fi/LAN: sealed package and catch-up metadata.
- Internet: optional publisher/release authority.
- Physical transport: large sealed packages.

## Software test now
Use only public or synthetic material. Test early-open attempts, superseded package versions, replayed release state, offline recipients, wrong package hashes and release state arriving before the package. Use established cryptographic libraries rather than a custom cipher.

## Real hardware
Use 4–6 boards plus 2–3 cache devices. Preload an encrypted public file, isolate the caches, then propagate a compact release authorization through the store-and-forward path and verify that only the intended exact package becomes usable.

## Messina scenario
A large classroom package can be staged across several school/public checkpoints before a scheduled exercise; the later release message is tiny and can propagate even when rich connectivity is unavailable.

## Privacy / security
Authenticate release and cancellation state, bind authorization to the exact package hash and prevent downgrade to older versions. Initial trials should use non-sensitive content.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-021 protects sealed sensitive content in transit, UC-020 carries trusted-time state and UC-026 delegates a bounded action. UC-165 specifically separates early bulk prepositioning from later compact authorization to unlock one exact object.

## Research / standards signal
Sealed-envelope designs and standard authenticated-encryption libraries provide the right building blocks. Draft mechanisms are design references only, not a reason to invent new cryptography.
