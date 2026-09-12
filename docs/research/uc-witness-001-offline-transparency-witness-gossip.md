# UC-WITNESS-001 — Offline transparency / witness gossip

Status: RESEARCH / SECURITY INFRASTRUCTURE PROTOTYPE

## Problem

A disconnected node may receive a signed security or policy state from one gateway and have no online auditor available to verify whether other users saw the same view. Ordinary signature verification proves who signed a checkpoint; it does **not** by itself prove that the signer did not present two different signed views to different partitions.

A tiny store-carry-forward network can be useful as an independent **gossip/witness channel**. Student-carried nodes exchange compact signed checkpoints (for example a Merkle-tree head or monotonic transparency generation) and later compare them at school/home. Conflicting views can then be flagged for an auditor.

Initial examples must use synthetic/test logs only:

- fleet-configuration transparency fixture;
- trust/revocation publication log;
- public software/package manifest log;
- public DNA/community-notice provenance log;
- classroom experiment deliberately serving different test checkpoints to two logical clusters.

This is not a certificate-transparency replacement and not production PKI.

## Actors / nodes

- test transparency/log service;
- school/home auditor;
- student-carried witness nodes;
- logical territorial clusters that may be partitioned;
- optional trust/config/content applications that publish checkpoints.

## Messina educational scenario

A test log at school publishes checkpoint `L:120/root=A`. During a controlled split-view experiment, cluster-A is deliberately given another validly signed checkpoint for the same logical history while cluster-B receives the expected one.

Students carry only the compact signed checkpoint/gossip evidence between Rometta-like, Saponara-like, Spadafora-like or Villafranca-like logical cohorts and the school mixing hub. On reunion, an auditor compares observed views and detects inconsistency.

No real student identity, home location or operational certificate log is required.

## Why PollicinoNet fits

Witness gossip has an unusually good scarce-link shape:

- checkpoint objects are small;
- delay is acceptable as long as inconsistency eventually reaches an auditor;
- independent mobile carriers are valuable because partitions are the threat model;
- duplicate suppression/reconciliation matter because many nodes may already know the same checkpoint;
- provenance and exact bytes are more important than throughput;
- the school mixing phase provides a natural comparison/audit rendezvous.

The application can therefore use ordinary exact Pollicino objects without changing the transport protocol.

## Possible bearers

- LoRa for signed compact checkpoints and conflict evidence;
- BLE for nearby exchange if enabled later;
- Wi-Fi/LAN/Internet for fetching proofs/full log state at the auditor;
- physical student carry between disconnected groups.

No LoRa PHY change is required.

## What can be tested now in software

1. deterministic signed test checkpoints;
2. two partitions receiving identical views;
3. deliberate split-view with two valid signatures;
4. monotonic generation rollback;
5. duplicate checkpoints from many relays;
6. missing intermediate checkpoints;
7. gossip cache limits and expiry;
8. compare full checkpoint lists versus latest-per-log plus conflict evidence;
9. reconstruct who can detect the conflict without storing student identity;
10. measure detection delay under school/home contact schedules;
11. compare direct-auditor polling with opportunistic witness gossip;
12. use reconciliation when witness caches are nearly identical;
13. keep proof retrieval on Wi-Fi after a compact conflict indicator arrives over LoRa.

Start with a toy Merkle log or signed `(log_id, generation, root_hash)` fixture. Production CT protocol compatibility is not required for the experiment.

## Minimal measurable hypotheses

- H1: independent store-carry-forward gossip detects synthetic split views that remain invisible to isolated clients.
- H2: latest-checkpoint/reconciliation schemes can keep witness traffic very small while preserving conflict detection.
- H3: pseudonymous witness transport can provide useful cross-partition evidence without recording precise student trajectories.

## Metrics

- split-view detection ratio;
- detection delay;
- witness bytes per log/generation;
- duplicate suppression;
- false conflict count;
- stale/rollback detection;
- number of independent logical clusters whose evidence reaches the auditor;
- proof-fetch bytes deferred to rich links;
- privacy metadata retained per witness event.

## What requires real hardware

Real boards are required only after the software security semantics are correct, to measure:

- actual checkpoint gossip capacity;
- energy/storage overhead of periodic witness exchange;
- real encounter-driven detection latency;
- resilience across restart/sleep;
- whether a school mixing phase provides sufficient independent witness contact.

HW-006 still comes first for RF-derived claims. The frozen first campaign remains 42-byte frames / 2 dBm.

## Privacy / security

This case exists to improve security, but can itself become a tracking channel.

Requirements:

- use test logs and test keys first;
- no stable student identity in checkpoint gossip;
- do not attach exact location to witness observations;
- minimize per-peer encounter metadata;
- distinguish `I observed checkpoint X` from `person Y observed checkpoint X`;
- signed checkpoints must be verified before comparison;
- conflict evidence must preserve exact bytes/signatures for later audit;
- denial-of-service limits for fake log IDs/checkpoints;
- do not claim production PKI safety from a classroom prototype.

## Implementation difficulty

**Medium-high.** The toy experiment is small; secure key management, anti-DoS policy and any production transparency integration are substantially harder.

## Relationship to existing use cases

- Not `UC-TRUST-001`: TRUST distributes the current trusted generation/revocations; WITNESS checks whether different partitions were shown inconsistent signed publication views.
- Not `UC-TRACE-001`: TRACE records privacy-bounded network encounters; WITNESS carries application/security checkpoints and does not require route history.
- Not `UC-OPS-001`: OPS converges device configuration; WITNESS could later audit a configuration-transparency log but does not configure devices.

## Success / kill criterion

**Continue** if a small synthetic split-view experiment demonstrates detection through carried checkpoints with bounded bytes and without requiring stable user identity.

**Defer production integration** unless a concrete Pollicino trust/config use case needs transparency rather than ordinary signed monotonic generations.

## Gate decision

**RESEARCH / PROTOTYPE.** The workload is technically well matched to DTN, but it is security infrastructure and should not become production architecture without a concrete threat model and independent review.

## Related precedent

Certificate Transparency v2 explicitly describes signed tree heads and notes that conflicting views can be detected when clients compare them; the RFC calls this technique gossip but does not standardize a gossip mechanism. Earlier CT work explored Signed Tree Head pollination between clients/servers.

- https://www.rfc-editor.org/rfc/rfc9162.html
- https://datatracker.ietf.org/doc/draft-ietf-trans-gossip/

These sources justify the security workload; they are not evidence for PollicinoNet hardware or coverage.
