# UC-033 — Secure Rich-Bearer Handoff Bootstrap

## Idea

Use LoRa only to **discover that a useful peer exists and negotiate a short-lived handoff**, then move the real payload over BLE, Wi-Fi/LAN or another richer bearer.

The core experiment is simple: two nodes discover each other through PollicinoNet, agree on *which exact object or session* they want to exchange, create a short-lived authenticated rendezvous, and then switch to the richer bearer without exposing reusable credentials.

## Problem solved

Many PollicinoNet use cases already assume a sentence like:

```text
LoRa discovers the peer -> Wi-Fi/BLE transfers the bytes
```

but the handoff itself is an important distributed/security problem.

A naive implementation might broadcast a Wi-Fi password, connect to the wrong nearby device, reuse stale bearer credentials, or transfer an object different from the one discovered over LoRa.

UC-033 makes the transition explicit and testable.

## Actors / nodes

- student PollicinoNet board with LoRa plus BLE/Wi-Fi-capable companion device;
- laptop/phone/ESP32 or similar rich-bearer endpoint;
- optional school cache/NAS/server;
- student relay/store-and-forward node that carries the rendezvous metadata;
- optional offline node that has no Internet at all.

## Why PollicinoNet fits

PollicinoNet is well suited to a **scarce control plane + rich data plane** split.

- **DISCOVERY:** `peer X may hold object Y and supports bearer Z`;
- **EXACT:** object root/hash, peer/session identity, one short-lived handoff token and the negotiated transfer intent;
- **SEMANTIC:** friendly labels such as `map pack`, `Raiatea document` or `classroom environment`, never a substitute for exact object identity.

The handoff can be reused by UC-004, UC-006, UC-012, UC-017, UC-023, UC-024, UC-029 and later use cases instead of inventing a different LoRa→Wi-Fi bridge each time.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** peer/bearer discovery, compact offer/request, short-lived rendezvous material, object/session binding and failure acknowledgement;
- **BLE:** nearby bootstrap or direct small transfer;
- **Wi-Fi Direct / local Wi-Fi / LAN:** primary rich payload transfer;
- **Internet:** optional rich bearer when policy permits;
- **physical transport:** the relay may carry the short-lived request/offer until the target is encountered later.

## What we can test now in software

Build a deterministic `HandoffSession` state machine with states such as:

```text
DISCOVERED
OFFERED
BOUND
RICH_LINK_READY
TRANSFERRING
VERIFIED
COMPLETED
```

Then test:

- exact binding between discovered peer, requested object and rich-link session;
- short TTL and one-use rendezvous tokens;
- replay of an old handoff offer;
- two nearby peers advertising the same object;
- wrong-peer connection attempt;
- object substitution after successful discovery;
- rich bearer failure and safe retry;
- downgrade attempt from an authenticated rich bearer to an insecure one;
- duplicate LoRa offers and out-of-order state messages;
- node reboot between discovery and rich-link establishment;
- cancellation when UC-024 `ContentNeed` has already been satisfied by another provider.

Useful software metrics include handoff attempts, successful bindings, stale/replay rejection, time from logical discovery to `RICH_LINK_READY`, and bytes kept off the scarce bearer.

## What requires real hardware

- at least two LoRa boards plus two BLE/Wi-Fi-capable endpoints;
- real LoRa discovery followed by a real BLE or Wi-Fi link;
- repeated peer encounters where multiple rich-bearer devices are visible at once;
- measured discovery-to-rich-link setup time;
- measured success/failure rate under controlled distance/orientation/interference conditions;
- measured payload bytes per bearer.

No physical performance value should be inferred from the simulator.

## Messina teaching scenario

Use three student nodes and one school cache.

One student requests a small map/document/environment object while disconnected from the school network. Another student's node advertises that it has the exact object root. LoRa performs discovery and negotiates a short-lived handoff. When the two students are close enough, the actual object moves over BLE/Wi-Fi and is verified by hash.

A second test deliberately places two possible providers nearby and proves that the rich-link session binds to the intended provider/object rather than to whichever SSID/device happens to answer first.

This can be repeated along controlled school/home routes without collecting continuous student location.

## Privacy / security

Do not broadcast reusable Wi-Fi passwords, long-lived bearer credentials or broad device identifiers.

Prefer:

- rotating/discovery identifiers where practical;
- short-lived session material;
- exact binding to peer + object + requested operation;
- mutual authentication appropriate to the bearer;
- minimal metadata in LoRa advertisements;
- fail-closed behavior when identity/freshness cannot be verified.

A nearby peer being discoverable does not make it trusted or authorized to receive content.

## Difficulty

**Medium–High.** The data transfer itself is ordinary BLE/Wi-Fi, but the challenge is making cross-bearer identity, authorization, freshness and object binding precise enough that every later use case can safely reuse it.

## Research signal

Recent work continues to combine LoRa with richer local radios rather than forcing all traffic through one bearer. A 2026 dual-radio BLE/LoRa emergency-mesh prototype explicitly exploits complementary radios, and a 2026 Computer Communications paper studies self-organizing IoT service continuity across LoRa and Wi-Fi. These are useful architectural signals, not PollicinoNet performance evidence.

References:

- https://www.max-robotics.com/en/research/publications/cmptvmcrz08ggbjb2htdtd5tx
- https://eprints.whiterose.ac.uk/id/eprint/236382/
