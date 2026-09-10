# UC-041 — Pop-Up Offline Classroom Hotspot

## Idea

Let a PollicinoNet node advertise that it can temporarily become a **local Wi-Fi classroom/library service** containing selected course material, Raiatea documents, maps or software resources even when Internet is unavailable.

LoRa is the low-bandwidth beacon/control plane. The actual browser/content session happens locally over Wi-Fi/LAN.

## Problem solved

A group of students may be together in a classroom, field activity, rural area or temporary emergency location with no usable Internet, while one nearby node already has useful content.

Instead of copying the whole library to every phone, one node can say:

```text
I can serve content pack P locally.
Join this short-lived local service if you are authorized.
```

UC-041 turns cached PollicinoNet content into a human-visible local service, not just a collection of chunks.

## Actors / nodes

- student or teacher device carrying a content cache;
- Raspberry Pi / mini-PC / laptop capable of running a local HTTP service;
- student phones/tablets/laptops as clients;
- LoRa boards advertising availability;
- school NAS/server that seeds or updates content packs when connectivity exists;
- optional Raiatea/Kiwix/Kolibri-like content service.

## Why PollicinoNet fits

- **DISCOVERY:** `offline classroom service available nearby`, supported pack/version, approximate capacity;
- **EXACT:** service identity, content-pack root/hash, short-lived handoff/session material;
- **SEMANTIC:** friendly label such as `3B Informatica`, `Wikipedia offline`, `Raiatea civil protection pack`.

The content pack itself can be distributed using UC-004/UC-006/UC-017/UC-024/UC-029/UC-040 and exposed through a local web service only when useful.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** service advertisement, content-pack root/version, rendezvous/control metadata;
- **BLE:** nearby bootstrap or fallback discovery;
- **Wi-Fi/LAN:** browser sessions and bulk content access;
- **Internet:** optional upstream synchronization when present;
- **physical transport:** preloaded SD/SSD/laptop moving the offline library between places.

## What we can test now in software

Run a local HTTP content server on one machine and simulate LoRa discovery separately.

Test:

- exact content-pack version advertisement;
- two nearby hotspots with different pack revisions;
- short-lived rendezvous credentials;
- hotspot disappears and later returns;
- clients continue reading already-fetched pages while disconnected;
- selective content update rather than full image replacement;
- one stale/corrupt content pack;
- capacity limit / too many clients;
- authorization for a private classroom pack versus a public pack;
- integration with UC-033 handoff and UC-024 `ContentNeed`;
- logging that records service health without tracking individual reading history by default.

Useful metrics include service discovery time, handoff success, local request latency, number of clients served, cache hit ratio and bytes avoided from Internet or scarce radio.

## What requires real hardware

- one or more real LoRa boards;
- a Raspberry Pi/laptop/mini-PC running a local Wi-Fi hotspot or LAN service;
- 3+ client phones/laptops;
- measured LoRa advertisement reception and rich-bearer handoff;
- measured local-service behavior under controlled concurrent clients;
- optional movement of the hotspot/cache between locations.

Do not claim LoRa range or Wi-Fi capacity from software simulation.

## Messina teaching scenario

A teacher or student node leaves school with an exact offline course pack already cached. In a controlled location in Rometta, Spadafora, Villafranca or another area without relying on Internet, the node advertises the pack over LoRa and opens a temporary Wi-Fi hotspot.

Nearby students connect from ordinary browsers and access:

- lesson notes;
- selected Raiatea documents;
- offline reference material;
- maps;
- small software/documentation packs.

Later, when the carrier returns to school Wi-Fi, UC-040/UC-024 can update only the changed content objects.

## Privacy / security

- public/offline educational content is the preferred first dataset;
- private classroom material must use authorization separate from mere LoRa discovery;
- do not broadcast reusable Wi-Fi credentials;
- do not log per-student reading behavior by default;
- bind the advertised service to an exact pack/root so clients can detect stale or substituted content;
- rate-limit abuse and isolate the local service from unrelated host resources;
- keep Internet bridging disabled by default unless explicitly intended.

## Difficulty

**Medium.** Most components already exist in ordinary Wi-Fi/HTTP software. The PollicinoNet research value is the opportunistic discovery, exact content identity, secure handoff and content-cache lifecycle around the service.

## Research / deployment signal

Offline-first education and local content hotspots are established real-world patterns. Learning Equality describes Kolibri as designed for teaching and learning without Internet. Kiwix provides local offline content servers/hotspots that expose compressed content to phones and computers over a local network. UC-041 does not replace those systems; it explores how PollicinoNet can discover, move and activate such a service opportunistically.

References:

- https://learningequality.org/
- https://get.kiwix.org/en/solutions/hotspots/
- https://get.kiwix.org/en/solutions/applications/kiwix-server/
