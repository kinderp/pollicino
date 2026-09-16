# UC-BACKUP-001 — Opportunistic safe-copy and backup evacuation

Status: USEFUL INTEGRATION USE CASE / PROTOTYPE

## Problem

A device may create information that should survive even when its normal backup destination is temporarily unreachable. Examples include field notes, experiment logs, configuration snapshots, selected photos/documents, sensor logs or other user-authorized data.

Instead of waiting for a full Internet connection, a Pollicino node can progressively move **encrypted references, manifests or selected chunks** onto other trusted nodes. Those peers physically carry the material until one reaches a trusted home/school/NAS/Internet backup target.

The goal is preservation, not general file sharing.

## Actors / nodes

- source phone/laptop/sensor/field device;
- portable Pollicino companion;
- trusted peer relays;
- school/home gateway;
- NAS/object store/backup endpoint.

## Why PollicinoNet fits

This workload stresses primitives already present but combines them differently from UC-CONTENT-001:

- exact reconstruction is mandatory;
- some chunks may be more important than others;
- multiple replicas may be desirable for durability;
- partial progress across many encounters is useful;
- storage quotas matter;
- final cryptographic verification matters;
- a rich path should take over immediately when available.

The key research question is not “how do we distribute popular content?” but “how much useful durability can be gained from scarce opportunistic contacts before the normal backup path returns?”

## Possible bearers

- LoRa only for tiny manifests, high-priority tiny objects or carefully selected chunks;
- BLE for close trusted peer exchange;
- Wi-Fi/Wi-Fi Direct for actual larger backup chunks;
- Internet for final upload;
- physical movement as store-carry-forward.

## What can be tested now in software

- generated backup objects with importance classes;
- finite relay storage and garbage collection;
- one-copy versus two-copy versus bounded-N replication;
- manifest-only/reference-only versus chunk evacuation;
- interrupted and resumed transfers;
- gateway outage duration distributions;
- recovery probability if one relay disappears;
- per-chunk exact SHA-256 verification.

The simplest baseline is “wait for the normal backup network”. Any opportunistic scheme must beat that baseline in a clearly defined outage/durability regime without excessive duplication.

## What requires real hardware

Hardware is needed before claiming practical benefit from LoRa or BLE/Wi-Fi encounters, including:

- useful bytes copied per encounter;
- real energy cost;
- storage drain speed;
- mobility/contact success;
- physical durability improvement in a field deployment.

Bulk backup over LoRa should not be assumed useful; the experiment must justify reference/manifest/chunk selection first.

## Privacy / security

**High sensitivity.** Backup data is often private.

Requirements:

- end-to-end encryption before untrusted relay storage;
- relays should not need plaintext access;
- authenticated manifests and exact hashes;
- key material must not depend on relay trust;
- explicit retention/expiry and secure deletion policy where feasible;
- avoid broadcasting stable content hashes for sensitive private objects if those hashes create correlation risk;
- relay storage quotas and abuse controls.

## Implementation difficulty

**Medium-high.** Exact chunk/custody primitives already help, but encrypted relay storage, replica policy and safe retention are additional work.

## Minimal measurable hypotheses

- H1: bounded replication provides materially better recovery probability than single-copy carry during long gateway outages for an acceptable byte/storage cost.
- H2: priority-aware chunk selection protects small critical objects before bulk objects under scarce contacts.
- H3: reference/manifest mule plus later rich-link retrieval dominates scarce-link payload transfer when the original source remains reachable later.

## Metrics

- recoverable object ratio after simulated failures;
- exact reconstruction rate;
- time to first safe remote copy;
- replicated bytes and storage occupancy;
- wire/TRC bytes by bearer;
- relay churn sensitivity;
- expired/deleted relay state;
- confidentiality/provenance invariants.

## Gate decision

**PROTOTYPE.** This use case reuses the object layer and does not justify a new protocol yet. It does justify experiments on bounded replica policy and routing-integrated storage pressure.