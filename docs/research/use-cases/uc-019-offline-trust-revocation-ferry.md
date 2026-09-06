# UC-019 — Offline Trust Epoch and Revocation Ferry

## Idea

Keep security state usable when nodes are disconnected by distributing small **signed trust epochs**: revocations, key rotations, role changes and minimum accepted trust-version information can propagate through the same store-and-forward paths as ordinary PollicinoNet metadata.

The goal is not to invent a new PKI. It is to test a hard offline-security problem: how does an isolated node learn that a formerly trusted key should no longer be accepted?

## Problem solved

A node can verify a signature perfectly and still make the wrong decision if its trust state is stale. Suppose one student board or gateway is lost and its key is revoked while another group of nodes is offline. Those offline nodes may continue accepting messages signed by the compromised key until updated revocation information reaches them.

Permanent Internet connectivity would normally solve this by consulting a central authority. PollicinoNet should instead be able to carry authenticated trust-state updates opportunistically and make **staleness visible** rather than silently assuming that an old trust view is current.

## Actors / nodes

- network/trust authority that signs trust epochs;
- school/server node holding the canonical current trust state;
- ordinary PollicinoNet nodes that validate peers/messages;
- student relay/store-and-forward nodes carrying compact trust updates;
- one synthetic revoked node used as an adversarial test case.

## Why PollicinoNet fits

Revocation records and trust-version summaries are small, exact and security-sensitive. They are therefore a strong match for `EXACT` dissemination and store-and-forward. A node can advertise:

```text
trust_epoch = 42
trust_root = <id>
manifest_hash = ...
```

Another node with epoch 39 immediately knows that its security view is stale and can request the missing signed deltas or a newer compact snapshot.

LoRa can carry epoch/version identifiers, hashes and small deltas. Richer bearers can move larger certificate or audit material. The use case sits entirely above the frozen PHY.

## Possible bearers

- **LoRa:** trust epoch, revocation IDs, compact signed deltas, minimum accepted epoch, stale-state warning;
- **BLE/Wi-Fi/LAN:** larger signed trust snapshots, certificate chains and audit material;
- **Internet:** canonical authority update when available;
- **physical transport:** a student/data mule carries an authenticated trust-state backlog between disconnected groups.

## What we can test now in software

- build a synthetic trust authority and node certificates/keys;
- issue monotonic signed trust epochs;
- revoke one synthetic node while part of the virtual network is partitioned;
- replay, duplicate, reorder and delay trust updates;
- attempt downgrade attacks with older but correctly signed epochs;
- test key rotation and superseded credentials;
- make each node expose `current`, `stale`, `unknown` or policy-specific trust freshness instead of a single Boolean;
- compare fail-closed, bounded-grace and explicitly degraded policies for non-critical teaching scenarios;
- property-test that an accepted trust state can never move backwards to an older epoch through ordinary propagation;
- record time/contacts required for revocation state to reach all reachable nodes in simulation.

A useful invariant is:

> a node must never accept an older trust epoch as newer simply because it arrived later.

## What requires real hardware

- 4+ boards split into two temporary partitions;
- revoke one synthetic board/key while one partition cannot contact the authority;
- let a moving relay carry the new trust epoch into the isolated group;
- verify that peers change behavior only after receiving and validating the update;
- measure propagation delay/contact count and separately record how long each node remained knowingly stale.

This experiment measures **revocation-state dissemination**, not the security of the LoRa PHY itself.

## Messina teaching scenario

Use a classroom authority node and several student nodes distributed across controlled locations. One node is marked compromised during the exercise. A student relay moves between two groups that do not have end-to-end connectivity. The second group should first report that its trust view is stale, then ingest the signed epoch and reject new application-level messages from the revoked synthetic identity.

No real student identity needs to be bound to the certificates used in the experiment.

## Privacy / security

This use case is itself security infrastructure, so fail-open shortcuts must be explicit and limited to synthetic/non-critical drills. Trust updates require authentication, anti-replay and monotonic versioning. Revocation reasons may reveal sensitive operational information and should be minimized. Node identifiers exposed over LoRa should avoid stable personal identity where possible.

Do not use wall-clock expiry as the only defense unless the node also has trustworthy time; UC-020 exists specifically because secure time freshness is a separate problem.

## Difficulty

**Medium–High.** Payloads are tiny and ideal for real relay experiments. The difficulty lies in safe stale-state semantics, downgrade resistance and defining what a disconnected node is allowed to do when it cannot prove that its trust view is current.

## Research signal

Certificate-revocation freshness remains a practical problem whenever authorities or publication repositories can be offline or stale. Current IoT and mesh work continues to treat signed revocation lists, certificate lifecycle and trust propagation as active design problems. PollicinoNet can study the dissemination side at small scale without claiming to replace standardized PKI systems.