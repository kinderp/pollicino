# UC-104 — Exact Version-Delta Artifact Ferry

## Idea

When a node already has version `V1` of a large object, do not automatically move the whole `V2`. Carry a compact manifest saying **which exact base is required**, then transfer a verified delta over BLE/Wi-Fi/LAN or physical media and reconstruct `V2` locally.

The key invariant is:

```text
apply(delta, exact_base_hash) -> exact_target_hash
```

If the base is missing or wrong, the node must refuse the delta and request a different delta chain or the full object.

## Problem solved

PollicinoNet may repeatedly distribute large, versioned artifacts:

- AI models or adapters;
- datasets and indexes;
- map bundles;
- course packs;
- Raiatea document stores;
- firmware images;
- container/root filesystem artifacts.

If versions are similar, sending each complete object wastes short rich-bearer contacts and cache capacity. UC-104 makes **version difference** a first-class transport choice while preserving exact content identity.

This is deliberately broader than Git patches: many useful artifacts are binary or generated and do not live naturally in Git.

## Actors / nodes

- publisher/source holding the target version;
- cache nodes holding one or more base versions;
- student relay/store-and-forward nodes;
- requester device;
- optional delta-builder service;
- verifier that checks target hashes/signatures.

## Why PollicinoNet fits

PollicinoNet already separates compact control from bulk bytes and already uses content identity/versioning in many use cases.

- **DISCOVERY:** `target available`, supported base versions, approximate delta/full size class;
- **EXACT:** base hash, target hash, delta hash, delta algorithm/version, signature/provenance and reconstruction recipe;
- **SEMANTIC:** labels such as `model-small-v7` or `map-messina-september`, never a substitute for hashes.

LoRa does not carry the delta itself except for tiny test fixtures. It helps two nodes decide whether a useful delta path exists before opening a richer bearer.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** target/base hashes or compact IDs, availability, delta-chain choice, completion/failure status;
- **BLE:** small/medium delta transfer during nearby contacts;
- **Wi-Fi/LAN:** normal delta or full-object transfer;
- **Internet:** seed full objects or deltas at connected gateways;
- **physical transport:** USB/SSD/student-carried cache for large bases, deltas or fallback full copies.

## What we can test now in software

Use several artifact families with controlled changes:

- a PDF/course archive with a few changed files;
- a map bundle with a small updated subset;
- a generated index;
- a model file where only a small adapter/metadata component changes;
- deliberately bad cases where binary changes make the delta almost as large as the target.

Implement a simple planner that compares:

```text
full target
single delta V1->V2
delta chain V0->V1->V2
content-chunk reuse
```

Test:

- exact-base mismatch;
- corrupted delta;
- interrupted transfer and resume;
- stale delta manifest;
- target signature failure;
- delta larger than full target;
- a cache that claims a base but has corrupted bytes;
- multiple possible bases with different transfer costs;
- deletion/tombstone interaction with UC-077;
- cache-demand interaction with UC-100.

Useful metrics include delta bytes, control bytes, reconstruction CPU time, completed reconstruction rate, fallback rate, and rich-bearer contact time consumed. Do not infer radio/energy savings until measured on real devices.

## What requires real hardware

A first physical test can use:

- 3–5 LoRa nodes;
- two laptops or a laptop plus Raspberry Pi;
- one cache with `V1`;
- one publisher with `V2`;
- a short controlled Wi-Fi/BLE contact;
- the same experiment repeated with full-object transfer and delta transfer.

Measure actual transferred bytes, wall-clock reconstruction time, transfer completion and device resource use. Any energy conclusion requires explicit instrumentation.

## Messina teaching scenario

A school cache in Messina has a new 1–2 GB offline AI/course bundle. Student caches in Villafranca and Rometta already have the previous exact version.

LoRa advertisements reveal that a particular cache has the required base hash. During a later Wi-Fi contact the relay carries only the selected delta. The receiver reconstructs the target and verifies the **target hash**, not merely the delta signature.

Another student intentionally starts from a similar-looking but wrong base. The correct behavior is a safe refusal and fallback request, showing why human filenames such as `model-v2.bin` are insufficient.

## Privacy / security

- hashes identify exact artifacts but can still leak which content a node probably has; expose only what the scenario requires;
- authenticate manifests and target provenance;
- verify both delta integrity and final target hash;
- never apply a delta merely because the filename/base label matches;
- enforce artifact usage policy from UC-076 after reconstruction;
- preserve deletion/retention semantics from UC-077;
- cap CPU/storage work to prevent malicious decompression or reconstruction abuse;
- treat executable/firmware targets with the same signature/authorization gates as full artifacts.

## Difficulty

**Medium.** The mechanics are established; the interesting PollicinoNet work is safe base negotiation, fallback, chain selection and measuring whether deltas actually help under intermittent contacts.

## Why this is distinct

- **UC-004:** distributes complete AI artifacts.
- **UC-009:** distributes signed firmware/configuration.
- **UC-044:** moves Git history/patches.
- **UC-104:** provides a generic exact-base/target delta mechanism for arbitrary versioned artifacts.

## Research / implementation signal

The rsync algorithm was explicitly designed to update similar files over low-bandwidth, high-latency links by sending unmatched data rather than whole files. OSTree also supports self-contained static deltas that can be applied offline and binds deltas to specific source/target revisions. These are useful design references; PollicinoNet still has to measure whether a delta is beneficial for each artifact family and real contact window.

References:

- https://rsync.samba.org/tech_report/
- https://ostreedev.github.io/ostree/copying-deltas/
- https://ostreedev.github.io/ostree/formats/
