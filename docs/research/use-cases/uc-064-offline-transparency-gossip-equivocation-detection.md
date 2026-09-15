# UC-064 — Offline Transparency Gossip and Equivocation Detection

## Idea

Let disconnected PollicinoNet nodes exchange **small signed checkpoints of append-only logs** so they can detect when an authority, repository or service presents inconsistent histories to different network islands.

A valid signature is not enough if the same authority can tell group A one signed story and group B another. UC-064 turns student relays into delayed gossip carriers: when two signed checkpoints finally meet, a contradiction or missing consistency proof becomes visible.

This complements UC-019. UC-019 distributes the latest trust/revocation state. UC-064 asks a different question: **did the authority itself equivocate or fork its history?**

## Problem solved

Consider an offline trust log, software-release log, assignment-receipt log or dataset-provenance log. Two disconnected groups may each receive a correctly signed checkpoint:

```text
Group A: log size 120, root AAA...
Group B: log size 120, root BBB...
```

Both signatures can verify, yet both views cannot represent the same append-only history at the same size. Without gossip, the groups may never discover the split view.

PollicinoNet is well suited to transporting these very small checkpoints until independent observers can compare them.

## Actors / nodes

- synthetic append-only log/authority;
- student observer nodes;
- school/server monitor;
- student relay/store-and-forward nodes;
- optional software-release, trust, evidence or Raiatea services that publish transparency checkpoints.

## Why PollicinoNet fits

The most important gossip objects are tiny and exact.

- **DISCOVERY:** `checkpoint available`, log ID, tree size/epoch and monitor hint;
- **EXACT:** signed checkpoint/root, log identity, tree size, hash algorithm and optional consistency-proof reference;
- **SEMANTIC:** labels such as `consistent`, `fork suspected`, `proof missing`, which are derived states and must not replace the exact signed evidence.

LoRa can move checkpoint digests and compact evidence. Larger proof chains or log slices can move over BLE/Wi-Fi/Internet or by physical carry.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** signed/root checkpoint, tree size/epoch, conflict alert and proof-request identifier;
- **BLE:** nearby exchange of checkpoint history and consistency proofs;
- **Wi-Fi/LAN:** complete proof chains or larger audit material;
- **Internet:** canonical log access when available;
- **physical transport:** student nodes carry checkpoint histories between disconnected groups.

## What we can test now in software

Build a tiny append-only Merkle log or equivalent deterministic checkpointed log and test:

- normal append-only growth;
- two partitions receiving different checkpoints;
- same-size/different-root equivocation;
- larger-tree checkpoints with valid consistency proofs;
- stale-but-valid checkpoints;
- duplicate, reordered and delayed gossip;
- a malicious synthetic authority serving two histories;
- observer reboot with persisted last-seen checkpoint;
- witness quorum policies without treating majority vote as cryptographic proof;
- exact preservation of conflicting signed checkpoints as evidence;
- integration with UC-019 so a trust-state publication can be both signed and transparency-audited;
- privacy test: minimize which observer requested or received which entry.

Useful metrics include time-to-conflict-detection, contacts-to-detection, checkpoint bytes per bearer, proof-fetch bytes and percentage of observers that eventually learn the conflict.

A key invariant is:

> a later-arriving valid signature must never erase contradictory earlier signed evidence.

## What requires real hardware

- 4+ boards split into at least two disconnected groups;
- one synthetic log service that intentionally serves different signed checkpoints to the two groups;
- one moving student relay that later connects the groups;
- real LoRa gossip of compact checkpoints;
- optional BLE/Wi-Fi retrieval of a larger consistency proof/history;
- measured delay from first contradictory publication to actual field detection.

This measures dissemination/detection behavior, not the security of the LoRa PHY and not the security of any production PKI.

## Messina teaching scenario

Create a classroom software-release transparency log. The `Messina/school` group receives release checkpoint A while a `Rometta/Spadafora` group receives a deliberately forked checkpoint B from the synthetic authority. Neither group has Internet and neither initially knows that the other view exists.

A student relay later moves between the groups. Only the two compact signed checkpoints need to cross the sparse link before the contradiction becomes visible. The class then retrieves the larger proof/log evidence on Wi-Fi and explains exactly why the histories cannot both be accepted.

The same exercise can later be reused for trust epochs, signed firmware releases, Raiatea evidence collections or assignment receipts.

## Privacy / security

Transparency gossip is security infrastructure and can itself leak metadata.

- use synthetic log entries and pseudonymous observers in teaching experiments;
- avoid revealing which student accessed which sensitive document or service;
- authenticate log identity and checkpoint signatures;
- preserve contradictory evidence immutably rather than resolving it silently;
- rate-limit gossip and proof requests;
- distinguish `fork proven`, `inconsistent/missing proof` and `not yet checked`;
- do not make production certificate/security claims from a classroom prototype.

## Difficulty

**Medium–High.** Merkle/checkpoint mechanics are manageable; the harder parts are durable observer state, precise evidence semantics, privacy of gossip and avoiding false confidence when a proof is merely unavailable rather than invalid.

## Research / standards signal

Certificate Transparency v2 explicitly treats consistency of the log view as an auditable property and notes that clients comparing signed tree heads can expose conflicting views. UC-064 borrows that small-checkpoint gossip idea as a generic delay-tolerant experiment; it does not attempt to reimplement the Web PKI.

References:

- https://www.rfc-editor.org/rfc/rfc9162.html
- https://www.rfc-editor.org/rfc/rfc9162.pdf
