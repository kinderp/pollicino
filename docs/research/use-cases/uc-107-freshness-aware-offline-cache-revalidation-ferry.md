# UC-107 — Freshness-Aware Offline Cache Revalidation Ferry

## Idea

Make cached content explicitly answer three separate questions:

1. **Do I have the exact object?**
2. **Is it still fresh according to the publisher/policy?**
3. **If it is stale, am I allowed to serve it while a revalidation request travels through the DTN?**

PollicinoNet already moves and caches content. UC-107 adds a generic freshness/revalidation contract for long-disconnected caches so that "available" is not mistaken for "current".

## Problem solved

Offline systems face an uncomfortable trade-off:

- refusing every stale object makes the service useless when the origin is unreachable;
- serving old content without warning can be dangerous;
- different content classes need different policies.

Examples:

- an old course PDF may be acceptable with a visible stale label;
- a map tile may be useful for a limited time;
- an emergency bulletin cancellation must not be hidden by a stale copy;
- an AI model card or policy document may require exact revalidation before use;
- a public API result fetched by UC-088 may be usable stale only under an explicit policy.

## Actors / nodes

- authoritative publisher/origin;
- school/Raiatea cache;
- student relay/store-and-forward nodes;
- offline requester;
- optional Internet gateway or authoritative revalidator;
- trusted-time/freshness support from UC-020 where needed.

## Why PollicinoNet fits

Revalidation requests and freshness metadata are compact even when the cached object is large.

- **DISCOVERY:** object available, freshness class, stale/revalidation-needed status;
- **EXACT:** object hash/version, publisher policy version, expiry/freshness evidence, validator token/ETag-like value, revalidation receipt;
- **SEMANTIC:** labels such as `fresh`, `stale-but-usable`, `must-revalidate`, `unknown-time`, shown to users but backed by exact metadata.

LoRa can carry the compact revalidation request/result. The object remains on the cache or moves over richer bearers only if a new version is actually needed.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** revalidation request, validator/hash, freshness state, compact `UNCHANGED / NEW_VERSION / REVOKED / UNKNOWN` result;
- **BLE:** nearby metadata/object refresh;
- **Wi-Fi/LAN:** full refreshed object when changed;
- **Internet:** authoritative conditional fetch/revalidation at a gateway;
- **physical transport:** refreshed cache snapshot or signed validity checkpoint carried by a student/device.

## What we can test now in software

Build a cache simulator with several policy classes:

```text
A. must-be-fresh
B. stale-while-revalidate for bounded time
C. stale-if-origin-unreachable for bounded time
D. immutable content-addressed object
E. revoked/cancelled object
```

Test:

- requester disconnected before expiry;
- stale object served with an explicit warning under policy;
- revalidation request duplicated or reordered;
- origin says `UNCHANGED`;
- origin publishes a new exact version;
- origin revokes/cancels the object;
- node clock is uncertain or wrong;
- trusted-time checkpoint from UC-020 arrives late;
- two caches have different freshness evidence for the same object;
- revalidation result arrives after the requester has already used a stale copy;
- privacy-sensitive objects whose metadata must not be publicly advertised.

Useful metrics include stale-serving duration, number of unnecessary full-object refreshes avoided, time-to-revalidation, stale exposure window, revalidation-control bytes and number of requests that correctly become `UNKNOWN` when time evidence is insufficient.

## What requires real hardware

A first physical experiment needs:

- 4–6 boards;
- one offline cache/RPi or laptop;
- one origin/gateway;
- one versioned public document or course pack;
- a deliberately disconnected interval that crosses the freshness deadline;
- a delayed LoRa revalidation path;
- a Wi-Fi refresh only when the object actually changes.

Repeat the same scenario with `UNCHANGED`, `NEW_VERSION` and `REVOKED/CANCELLED` origin outcomes. Measure actual revalidation latency, control traffic and rich-bearer bytes. Do not claim energy or radio savings without instrumentation.

## Messina teaching scenario

A cached Raiatea/course package is available at nodes around Rometta/Venetico while the authoritative school origin in Messina is temporarily unreachable.

The cache can still answer requests, but its UI must distinguish:

```text
FRESH
STALE — policy permits temporary use
STALE — MUST REVALIDATE
TIME UNKNOWN — freshness cannot be established
REVOKED/CANCELLED
```

A student relay later carries the compact revalidation request toward a connected gateway. If the origin says the object is unchanged, only a tiny receipt returns. If it changed, the new exact object is scheduled for Wi-Fi/BLE transfer.

This makes "offline-first" behavior visible and testable instead of silently serving whatever happens to be cached.

## Privacy / security

- object freshness metadata can reveal what a user or cache possesses; minimize public advertisements;
- authenticate publisher policies and revalidation receipts;
- bind freshness evidence to the exact object/version;
- never treat local clock time as trustworthy when the scenario requires UC-020-style trusted time;
- `UNKNOWN` must remain distinct from `FRESH`;
- revocation/cancellation must override stale-serving permission when authenticated and applicable;
- do not use stale policy to bypass UC-076 usage restrictions or UC-077 deletion/retention state;
- avoid silent stale serving for safety-critical or emergency data.

## Difficulty

**Medium.** The protocol objects are small; the subtle part is expressing policy, time uncertainty and user-visible stale state correctly across partitions.

## Why this is distinct

- **UC-020:** carries trusted time/freshness evidence.
- **UC-077:** propagates deletion/retention expiry.
- **UC-083:** distributes topic updates.
- **UC-088:** fetches a bounded Internet resource through a later gateway.
- **UC-107:** defines what an offline cache may do **between updates**, and how it revalidates a cached exact object without automatically transferring it again.

## Standards signal

HTTP caching already separates freshness, stale serving and validation. RFC 9111 states that a stale response normally must not be generated unless the cache is disconnected or stale use is otherwise permitted; RFC 5861 defines bounded `stale-while-revalidate` and `stale-if-error` behavior. UC-107 generalizes those ideas to content-addressed, delay-tolerant PollicinoNet objects with explicit time uncertainty and non-HTTP bearers.

References:

- https://www.rfc-editor.org/rfc/rfc9111.html
- https://datatracker.ietf.org/doc/rfc5861/
