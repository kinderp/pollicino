# UC-028 — Offline Collaborative Notebook

## Idea

Let several students edit the same small notebook, field log or lab report while their nodes are temporarily disconnected, then use PollicinoNet relays to exchange **edit operations and state summaries** until every replica converges.

This is not ordinary file synchronization. The interesting case is when two groups both edit while partitioned and neither side is the single authoritative writer.

## Problem solved

A class, field team or project group may need to keep working even when there is no shared Wi-Fi or Internet. Traditional shared-document systems often assume a reachable server. Copying whole files also creates awkward `report-final-final2.md` conflicts.

For selected data types, a local-first replicated document can instead record operations that can be merged deterministically after delayed contact.

The result should preserve both:

- exact document state and operation provenance;
- explicit unresolved **semantic conflicts** when two edits are logically contradictory even if they are mechanically mergeable.

## Actors / nodes

- student laptops/phones paired with PollicinoNet nodes;
- two or more temporarily disconnected student groups;
- student relay/store-and-forward nodes moving between groups;
- optional school node holding a durable snapshot/archive;
- teacher or human reviewer for semantic conflicts.

## Why PollicinoNet fits

Collaborative editing produces many small pieces of coordination state that tolerate delay better than they tolerate central-server dependence.

A useful split is:

- **DISCOVERY:** document ID, replica epoch, compact version/vector summary, availability of missing operation ranges;
- **EXACT:** signed/hashed edit operations, snapshots, attachment hashes and final converged document state;
- **SEMANTIC:** human meaning such as `section disputed` or `needs review`, kept separate from deterministic convergence.

LoRa can carry compact operation metadata and, where measured capacity permits, very small text operations. BLE/Wi-Fi/LAN or physical carry should move snapshots, large operation batches and attachments.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** document ID, version/vector summary, operation IDs, missing-range requests, compact acknowledgements and possibly tiny edits;
- **BLE:** nearby replica synchronization;
- **Wi-Fi/LAN:** snapshot, attachment and bulk operation exchange;
- **Internet:** optional ordinary synchronization when available;
- **physical transport:** a student node carries operation batches between disconnected groups.

## What we can test now in software

- create a tiny local-first text/notebook model using a reviewed CRDT or a deliberately narrow operation log;
- split four replicas into two network islands;
- apply concurrent edits on both sides;
- deliver operations out of order, duplicated and after long delay;
- prove deterministic convergence of the supported data type;
- verify operation IDs and persistent duplicate suppression;
- attach images/files only by exact content hash and retrieve them later over a richer bearer;
- model compact version summaries and requests for missing operation ranges;
- retain authorship/provenance without requiring a globally reachable identity service;
- deliberately create a semantic contradiction such as `meeting = Monday` versus `meeting = Tuesday` and prove that mechanical convergence does **not** pretend the contradiction is resolved;
- compare whole-file ferrying against operation-level synchronization by bytes transferred, convergence delay and conflict visibility.

A core invariant is:

> deterministic replica convergence does not imply semantic agreement.

## What requires real hardware

- 4 or more PollicinoNet nodes;
- two deliberately disconnected groups;
- one moving student relay between them;
- repeated short and long contact windows;
- measurements of delivery delay, operation backlog, duplicate overhead and convergence time;
- a real BLE/Wi-Fi handover for snapshots/attachments.

No physical-radio performance is claimed until those measurements exist.

## Messina teaching scenario

Create a shared `Rete-Messina-Lab-Notebook` with four student replicas. Put two nodes in one school/lab zone and two in another disconnected zone. Both groups edit different and overlapping sections. A student carrying a board moves between them and exchanges operation summaries/store-and-forward batches.

Later, run the same experiment on a controlled route between school/home areas such as Messina, Villafranca/Rometta or Milazzo, but log only the technical contact windows needed by UC-008 rather than student trajectories.

The visible success criterion is simple: every replica eventually reaches the same supported document state, while deliberately contradictory human claims remain marked for review.

## Privacy / security

Collaborative notes may contain names, grades, personal opinions or location details. Start with synthetic/public classroom content. Use encryption and authorization per document/replica group; do not broadcast plaintext edits as discovery metadata.

Authorship metadata should be pseudonymous where the experiment does not require real identity. A relay may transport encrypted operations without gaining edit authority.

Malicious or unauthorized operations must fail verification rather than being merged.

## Difficulty

**Medium–High.** The network transport is straightforward; the harder parts are selecting a safe replicated-data model, bounding metadata growth, handling authorization and distinguishing data-structure convergence from real semantic conflict.

## Research signal

Offline-first CRDT systems remain an active research direction. CAMS F-Edge DTN (2026) combines CRDT-based convergence with opportunistic Bluetooth/Wi-Fi-style synchronization under intermittent connectivity, while current local-first collaborative-editing literature continues to emphasize coordination-free convergence and its metadata/garbage-collection costs.

References:

- https://www.mdpi.com/1999-5903/18/4/180
- https://system-design.space/en/chapter/crdt-collaborative-editing/
