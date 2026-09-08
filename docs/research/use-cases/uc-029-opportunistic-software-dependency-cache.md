# UC-029 — Opportunistic Software Dependency Cache

## Idea

Use PollicinoNet to discover which nearby school/home nodes already hold the **exact software dependencies** needed for a development environment, then fetch only the missing closure over Wi-Fi/LAN/BLE or by physical carry.

LoRa is the control plane: it should not be treated as the default bearer for large package archives.

## Problem solved

A classroom, student laptop or rural/offline node may need a reproducible development environment while Internet access is slow, absent or rate-limited. Re-downloading the same compilers, packages and container layers from the Internet is wasteful when another trusted node nearby already has them.

The challenge is not merely copying one file. A software environment is usually a dependency graph/closure:

```text
project
  -> compiler
  -> runtime
  -> libraries
  -> tools
```

The requester should discover exactly which objects are missing and obtain only those objects from one or more trusted caches.

## Actors / nodes

- student laptops and development machines;
- school/lab cache node;
- teacher/workstation or home server cache;
- student relay/store-and-forward nodes;
- optional Internet gateway;
- package/build system such as Nix, OCI/container registry, language package cache or a synthetic dependency DAG for the first prototype.

## Why PollicinoNet fits

This is a concrete specialization of content-addressed rendezvous with a dependency graph and strong supply-chain requirements.

- **DISCOVERY:** environment/closure ID, compact inventory hints and which node may possess missing objects;
- **EXACT:** store-path/object hashes, signed manifests, dependency edges and verified package bytes;
- **SEMANTIC:** friendly labels such as `Python classroom environment`, never a substitute for exact dependency identity.

LoRa can advertise a small environment root and cache availability. A richer bearer transfers the actual binaries. A student carrying a laptop/board can physically ferry already-cached dependencies between network islands.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** closure root, version, inventory summary, missing-object requests, provider hints and completion acknowledgements;
- **BLE:** small nearby cache exchange where practical;
- **Wi-Fi/LAN:** main binary/package transfer bearer;
- **Internet:** fallback source when available;
- **physical transport:** laptop/SSD/student node carries cached software objects between school/home islands.

## What we can test now in software

- build a synthetic dependency DAG with exact object hashes;
- create three caches that each hold only part of the closure;
- request one environment root and compute the exact missing closure;
- satisfy missing objects from multiple providers without redownloading duplicates;
- interrupt and resume transfers;
- inject corrupted objects and verify hash failure;
- inject a cache that advertises an object it does not have;
- test signature/trust rules separately from mere object availability;
- compare `download whole environment` against `retrieve only missing closure`;
- optionally repeat the experiment with a tiny real Nix closure or OCI image set after the generic protocol works;
- integrate UC-024 `ContentNeed` and UC-019 trust freshness rather than inventing a second discovery/security system.

Useful metrics include missing-object count, bytes avoided, time-to-ready, cache hit ratio and verification failures. These are software/network measurements, not LoRa range claims.

## What requires real hardware

- at least 3 laptops/cache nodes with intentionally different local inventories;
- 2–3 PollicinoNet boards for scarce-bearer discovery;
- a real LoRa discovery followed by Wi-Fi/LAN/BLE transfer;
- one experiment where the cache provider is reached only after a student/data-mule contact;
- measured handover time and actual bytes transferred per bearer.

## Messina teaching scenario

Prepare a small reproducible Python/Rust classroom environment on the school cache. Give different students incomplete caches. One student in the Rometta/Villafranca side and another in Messina/Milazzo can be modeled as disconnected islands in the simulator first; later, controlled student-node contacts can ferry cache state.

The visible exercise is: a laptop with no Internet requests `classroom-env-v1`, discovers that peers collectively have the closure, and becomes ready without every dependency coming from the school server or Internet.

A particularly useful follow-up is integration with The Blob/Nix experiments: the same content-addressed software objects that prewarm a Workspace could be opportunistically distributed by PollicinoNet when direct infrastructure is unavailable.

## Privacy / security

Software package names can reveal projects or courses, so discovery should expose only what is necessary. More importantly, cache discovery must never imply trust.

A malicious cache can poison a software supply chain. Every exact object must be verified by its content identity and, where the package model requires it, by trusted signatures/provenance. Third-party caches must not automatically become trusted substituters merely because they are nearby.

Credentials, private repository tokens and signing keys must never be ferried as ordinary cache objects.

## Difficulty

**Medium–High.** Content addressing and dependency closure make the correctness test clean, but production use requires careful trust/provenance, cache eviction and integration with real package systems.

## Research signal

Nix already models software as store objects and dependency closures and supports additional stores/binary caches as substituters. Current Nix documentation explicitly distinguishes content-addressed store objects, substituters and trusted cache configuration, which makes it a useful concrete backend for later experiments without making PollicinoNet Nix-specific.

References:

- https://releases.nixos.org/nix/nix-2.34.0/manual/package-management/binary-cache-substituter.html
- https://wiki.nixos.org/wiki/Binary_Cache
