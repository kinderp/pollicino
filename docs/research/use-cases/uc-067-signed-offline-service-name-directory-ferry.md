# UC-067 — Signed Offline Service Name Directory Ferry

## Idea

Give disconnected PollicinoNet nodes a small, signed way to answer questions such as:

```text
What exact identity/key currently represents `raiatea-school`?
Which service record names the local package cache?
Which key owns `lab-printer-1`?
Which alias replaced an old service name?
```

The aim is not to recreate DNS. The experiment is about **stable human/service names mapped to exact cryptographic/service identities while directory updates themselves may be delayed**.

This complements UC-014. UC-014 advertises dynamic capabilities such as `I can run this job now`. UC-067 provides a more stable naming/bootstrap layer: `this signed name currently denotes this service/key/version`.

## Problem solved

Once a PollicinoNet deployment grows beyond a few boards, hard-coded IDs become difficult to manage. A user may remember `raiatea-school`, but the underlying key, host, service instance or endpoint can rotate. Two disconnected groups may also hold different directory versions.

A normal online directory assumes a reachable resolver. In a sparse network we instead need:

- signed name records;
- explicit version/freshness;
- key/service rotation;
- conflict detection;
- graceful stale/unknown state;
- store-and-forward propagation.

## Actors / nodes

- school/network directory authority for the experiment;
- named services such as Raiatea, cache, classroom hotspot or lab device;
- ordinary student nodes resolving names;
- student relay/store-and-forward nodes;
- optional Internet/DNS bridge when connected;
- optional UC-019 trust/revocation authority.

## Why PollicinoNet fits

Directory records are small, exact and change less frequently than bulk content.

- **DISCOVERY:** name hash/prefix, directory epoch, record-available hint and service class;
- **EXACT:** canonical name, service/key identity, record version, authority signature, expiry/freshness information and optional replacement/tombstone record;
- **SEMANTIC:** human aliases and service descriptions, useful for UI but never a substitute for the exact signed binding.

LoRa can distribute record IDs, version summaries and small signed mappings. Richer bearers can synchronize a larger directory snapshot if needed.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** directory epoch, compact signed name record, record hash, stale-state/request metadata;
- **BLE:** nearby directory synchronization/bootstrap;
- **Wi-Fi/LAN:** larger signed directory snapshot and service metadata;
- **Internet:** optional bridge to conventional DNS/service-discovery infrastructure;
- **physical transport:** student nodes carry updated signed records between disconnected zones.

## What we can test now in software

Build a tiny synthetic directory with names such as:

```text
raiatea-school
course-cache
lab-printer-1
pollicino-relay-demo
```

Then test:

- exact signed name-to-key/service mappings;
- monotonic directory epochs;
- service key rotation;
- rename/alias records;
- tombstone/revocation of an old name;
- duplicate and out-of-order updates;
- stale-but-valid records;
- two conflicting records for the same name/version;
- explicit `unknown` when no sufficiently fresh record is available;
- negative-cache expiry so `not found` does not become permanent;
- interaction with UC-019 trust epochs;
- interaction with UC-033 after a service name resolves to an exact peer/service identity;
- spoofing/name-squatting negative tests;
- comparison of stable-name resolution versus copying raw node IDs into every application configuration.

Useful metrics include record-propagation delay, stale-resolution rate, directory bytes per bearer, successful rotation convergence and time-to-resolve after a node starts with an empty cache.

A key invariant is:

> a friendly name may be convenient, but authorization decisions must bind to the exact authenticated identity produced by a sufficiently fresh signed record.

## What requires real hardware

- 3–5 boards with at least two real named services or service simulators;
- one disconnected group with an intentionally stale directory;
- rotate one service key/name at the authority;
- use a moving student relay to carry the signed update;
- perform real LoRa record propagation;
- optionally use UC-033 to connect to the resolved service over BLE/Wi-Fi/LAN;
- measure how long nodes remain stale and whether old mappings are rejected after update.

The experiment validates application-layer naming propagation, not Internet DNS availability or LoRa PHY performance.

## Messina teaching scenario

Create named services distributed across the teaching network, for example:

- `raiatea-school` at the institute;
- `course-cache-rometta` on a portable cache;
- `lab-printer-1` on a supervised school LAN;
- `messina-demo-gateway` on an optional gateway node.

A student node in a disconnected group knows only the friendly name and an older signed directory epoch. During the exercise, the key behind `raiatea-school` is rotated. A relay later brings the new directory record. The node should expose that its view was stale, validate the new binding and only then use UC-033 or another application protocol to contact the exact service.

This is a useful classroom demonstration because students can see the difference between **finding a name**, **authenticating an identity** and **actually reaching the service**.

## Privacy / security

A service directory can reveal network structure.

- advertise only services intended to be discoverable;
- avoid embedding student names or home locations in service names;
- authenticate directory authority and records;
- protect against replay/downgrade and name squatting;
- treat stale status explicitly;
- separate naming from authorization: resolving a name does not grant permission to use the service;
- minimize detailed endpoint metadata on broadcast LoRa;
- use UC-019 for trust/revocation state rather than inventing a second unrelated trust model.

## Difficulty

**Medium–High.** The signed record format is small. The main design work is conflict/version semantics, rotation, stale-state behavior and keeping naming separate from trust and capability advertisement.

## Standards signal

DNS-Based Service Discovery provides a mature model for named service instances, while the IETF Service Registration Protocol (RFC 9665) uses public keys and signatures to defend service registrations and is designed to work without relying on multicast-only discovery. UC-067 does not import DNS-SD/SRP as its wire protocol; these standards are useful references for the distinction between service naming, registration, identity and discovery.

References:

- https://www.rfc-editor.org/info/rfc6763
- https://www.rfc-editor.org/info/rfc9665
- https://datatracker.ietf.org/doc/html/rfc9665
