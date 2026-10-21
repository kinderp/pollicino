# UC-TRUST-001 — Offline trust, key-rotation and revocation ferry

Status: RESEARCH / SECURITY-INFRASTRUCTURE PROTOTYPE

## Summary

In a disconnected network, security state can become stale even when application data is delivered correctly. This use case studies how compact, signed trust updates — revoked node/key identifiers, new trust-anchor generations, key-rotation metadata and security-policy generations — can propagate through the same store-carry-forward network without requiring every node to contact an online certificate/status service.

This is security infrastructure, not an application feature. It should be implemented conservatively and only after simple signed fixtures are benchmarked.

## Problem solved

A node may remain disconnected for hours or days. During that period:

- a credential may be revoked;
- an administrative signing key may rotate;
- a compromised node may need to be de-authorized;
- policy may change so certain traffic must no longer be accepted.

If trust state only updates via Internet, a disconnected DTN can continue accepting stale credentials long after the authority has changed its decision.

## Actors / nodes

- trust/security authority;
- school/admin gateway;
- student-carried relay nodes;
- fixed Pollicino/sensor nodes;
- optional home rich-network gateways.

The trust object should identify cryptographic principals, not real student names.

## Messina educational scenario

Suppose one experimental node key is deliberately marked revoked in a controlled exercise. The school gateway issues signed trust generation `T12`. Nodes leaving school carry the compact update into territorial clusters. A node still on `T11` must learn and verify `T12` before accepting newly received content attributed to the revoked key.

This can be tested entirely with synthetic keys and pseudonymous nodes. It must not be used to make claims about real incident response speed until field contact traces exist.

## Why PollicinoNet fits

Trust state is small, high-priority, versioned and valuable even when no end-to-end path exists. Existing Pollicino properties are a natural substrate:

- exact object identity;
- provenance/authenticator fields;
- priority scheduling;
- TTL/hop governance;
- durable custody;
- store-carry-forward;
- multi-bearer handover;
- duplicate suppression.

The core research question is not how to invent a new PKI, but how quickly trustworthy security state converges under intermittent contacts and finite resources.

## Bearers

- LoRa: compact signed revocation/key-generation summaries;
- BLE: local technician recovery or bootstrap where policy permits;
- Wi-Fi/LAN/Internet: full trust bundles, certificates and audit logs;
- physical carry: mobile nodes ferry signed security state between disconnected clusters.

## What we can test now in software

Use synthetic credentials and controlled compromise events. Compare:

1. Internet-only trust refresh;
2. gateway/direct delivery of trust update;
3. high-priority DTN flooding;
4. bounded-copy trust propagation;
5. periodic generation-summary reconciliation.

Measure:

- time until each node learns the newest trust generation;
- percentage of nodes accepting stale credentials over time;
- trust-control wire bytes;
- duplicates;
- effect of missed contacts;
- behavior after restart;
- conflict handling for reordered generations;
- fail-closed behavior on forged or malformed updates.

A crucial test is that replaying `T11` after verified `T12` must not silently roll a node back.

## Hardware required later

Real boards are required for:

- measured trust-update propagation through actual student mobility;
- persistence across power loss/restart;
- cryptographic verification cost and battery impact;
- operational key storage on the target device;
- recovery procedures for a node that misses multiple generations.

HW-006 still gates any claim about LoRa propagation time/capacity.

## Privacy and security

This is a security-critical use case. Requirements include:

- authenticity and integrity of trust updates;
- monotonic generation/anti-rollback semantics;
- bounded validity and replay protection;
- least-privilege signing keys;
- secure key storage where hardware permits;
- no private keys or personal identity data in propagated revocation objects;
- denial-of-service limits on bogus trust updates;
- explicit recovery/override procedure rather than ad-hoc bypasses.

A production trust design requires independent security review. The first prototype should use disposable test keys only.

## Difficulty

**High.**

The payload is tiny, but failure modes are severe. A simple, auditable design is more important than minimizing a few extra bytes.

## Research context

DTN architecture literature has long identified credential revocation and security-state distribution as difficult when centralized online services are unavailable. RFC 4838 explicitly notes that revocation state may need to be maintained in DTNs, and later research has proposed offline-validatable revocation mechanisms for disruption-tolerant networks. PollicinoNet should use this as a workload and threat model, not automatically adopt a specific PKI scheme.

## Success criteria

The experiment should demonstrate deterministic, rollback-resistant convergence of signed trust generations under partitions, with explicit accounting of the scarce-link cost.

## Decision

**RESEARCH / SECURITY-INFRASTRUCTURE PROTOTYPE.**

Strongly justified as a future real-network requirement, but not suitable for production adoption without dedicated threat modeling, implementation review and hardware key-management evidence.
