# UC-OPS-001 — Offline fleet management and configuration ferry

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Summary

A distributed PollicinoNet student network needs to remain operable even when many nodes are away from school and have no Internet access. This use case treats the network itself as a DTN-managed fleet: signed configuration state, policy/version metadata, update references and maintenance commands can travel outward through student-carried nodes, while health summaries, logs and acknowledgements travel back toward school/home gateways.

This is not remote interactive administration. It is asynchronous, bounded and auditable fleet management for challenged connectivity.

## Problem solved

A real deployment across the Messina hinterland may contain nodes that only intermittently reach Wi-Fi or a central administrator. Requiring every node to connect directly to a cloud service would defeat the purpose of the off-grid network.

The network therefore needs a way to answer:

- which configuration/policy version should this node use?
- which signed firmware/package reference is current?
- which nodes have acknowledged or rejected an update?
- which nodes report low storage, repeated failures or stale software?
- can a configuration rollback/revocation reach disconnected clusters?

## Actors / nodes

- school or administrator gateway;
- student-carried Pollicino nodes;
- optional fixed relay/sensor nodes;
- home Wi-Fi/NAS gateways;
- maintenance workstation that signs releases/policies.

Student identities are not required by the protocol experiment. Nodes should use pseudonymous IDs.

## Messina educational scenario

A school gateway publishes configuration generation `G42`. Students leave school carrying the signed generation metadata. During afternoon contacts in pseudonymous clusters labelled, for example, Rometta, Spadafora, Saponara or Villafranca, nodes that still run `G41` learn that a newer authorized generation exists. If the update body is too large for LoRa, they carry only its manifest/hash/reference and fetch it later over home Wi-Fi. Acknowledgements and health summaries return opportunistically the next day.

No town-to-town LoRa reachability is assumed by this scenario; human mobility creates the bridge.

## Why PollicinoNet fits

Existing primitives already address much of the workload:

- content-addressed identity and exact verification;
- PND1 discovery / rendezvous state;
- PCM1 manifests and chunk reconciliation;
- PNB1 TTL/hop governance;
- custody/store-carry-forward;
- priorities and fairness;
- multi-bearer handover;
- durable restart and finite relay storage.

The important new workload is **management state convergence under disconnection**, not a new PHY.

## Bearers

- LoRa: compact signed config/version/health summaries and selected small deltas;
- BLE: nearby technician/student maintenance session where appropriate;
- Wi-Fi/LAN: complete package/firmware payloads, detailed logs and checkpoints;
- Internet: upstream package/release repository when available;
- physical carry: the student/vehicle moves management state between clusters.

## What we can test now in software

A synthetic fleet can model 20–100 nodes with different current generations and intermittent contacts. Compare:

1. push complete configuration every time;
2. advertise only generation/hash, pull detail on mismatch;
3. version manifest + reconciliation;
4. signed update reference, body fetched only on rich bearer.

Inject missed contacts, stale nodes, rollback attempts, limited storage and a deliberately bad configuration generation. Measure convergence time, control bytes, duplicate suppression, rollback recovery and how many nodes remain stale.

A second experiment can route small health summaries back toward the school gateway and compare freshness under Direct Delivery, Epidemic, Spray-and-Wait and later PRoPHET.

## Hardware required later

Real boards become necessary to measure:

- actual time/bytes needed to exchange management metadata;
- battery impact of periodic discovery and maintenance traffic;
- restart/upgrade behavior on the target board;
- robustness when nodes move between real school/home encounters;
- safe firmware installation and rollback on real hardware.

Do not auto-flash firmware in the first field campaign. Start with signed version metadata and harmless configuration fixtures.

Real LoRa contact capacity/range claims remain blocked by HW-006.

## Privacy and security

Management traffic has a high trust requirement.

Minimum design constraints:

- signed configuration generations;
- anti-replay / monotonic generation or equivalent rollback protection;
- explicit authorization for destructive or privileged actions;
- no secrets in broadcast configuration;
- pseudonymous node health where individual identity is unnecessary;
- rate/size quotas so forged maintenance traffic cannot consume the DTN;
- fail-closed behavior when authenticity is unknown.

A compromise of the signing authority would be severe, so key rotation/revocation is deliberately separated into `UC-TRUST-001`.

## Difficulty

**Medium in simulation; medium-high on real boards.**

The data model is small and aligns with existing Pollicino primitives. Production-safe update installation, rollback and key management are the difficult parts.

## Research context

RFC 9675 (DTN Management Architecture) explicitly treats network management in challenged networks where timely end-to-end exchange, continuous power and external infrastructure cannot be assumed. PollicinoNet does not need to implement DTNMA to learn from that workload model.

## Success criteria

Continue if a version/manifest/pull strategy materially reduces scarce-link management traffic while converging reliably after partitions and preserving signed provenance.

## Decision

**PRIMARY USE CASE / PROTOTYPE-DRIVING.**

It directly supports operating the future student network itself. It justifies a management workload and signed-version experiments, but not a new management wire protocol until simple opaque Pollicino objects prove insufficient.
