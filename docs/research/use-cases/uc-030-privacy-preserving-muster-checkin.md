# UC-030 — Privacy-Preserving Muster / Safety Check-In

## Idea

Use PollicinoNet for a **temporary safety check-in** during a controlled school excursion, campus drill or field activity: participants prove that a rotating/pseudonymous token checked in at one of several designated points, while the network avoids continuous tracking.

This must not become an attendance-surveillance system.

## Problem solved

During a field activity the organizer may need a simple question answered under intermittent connectivity:

> Which expected pseudonymous participants have checked in at a safe point during this time window?

A central Internet service may not be reachable everywhere. Student nodes and checkpoint nodes can therefore store-and-forward compact signed check-ins until the organizer's node receives them.

The design should answer **presence at a checkpoint/window**, not reconstruct where a student travelled between checkpoints.

## Actors / nodes

- participant/student nodes using rotating experiment identifiers;
- designated checkpoint/muster nodes;
- teacher/organizer node holding the mapping needed for the experiment;
- student relay/store-and-forward nodes;
- optional BLE phone companion for near-checkpoint interaction;
- optional school gateway when Internet becomes available.

## Why PollicinoNet fits

Check-ins are compact, delay-tolerant control records. They do not require a permanent end-to-end path.

- **DISCOVERY:** checkpoint epoch/challenge and availability of pending check-in receipts;
- **EXACT:** signed one-time check-in token, checkpoint ID, bounded time/epoch and receipt;
- **SEMANTIC:** `safe/check-in observed`, never a claim of exact continuous location.

A relay can carry encrypted/signed check-in records without learning the real identity behind a rotating identifier.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** checkpoint challenge/epoch, compact check-in token, receipt and missing-status summary;
- **BLE:** optional local proximity handshake at the checkpoint;
- **Wi-Fi/LAN:** bulk synchronization of the organizer's final roster/state;
- **Internet:** optional upload after the event;
- **physical transport:** participant/relay nodes carry pending check-ins between disconnected areas.

## What we can test now in software

- generate synthetic participants and rotating pseudonymous identifiers;
- define one-time checkpoint challenges bound to an epoch/window;
- simulate two disconnected checkpoint islands and delayed relay delivery;
- reject replayed, stale or wrong-checkpoint tokens;
- verify that duplicate forwarding does not create duplicate presence records;
- test a participant who checks in at checkpoint B after missing A;
- test revocation/trust changes through UC-019 without revealing more identity than necessary;
- model uncertain time using UC-020 rather than assuming perfect clocks;
- prove that the stored experiment log cannot reconstruct a continuous route because only checkpoint/window events exist;
- compare explicit participant IDs against rotating IDs to quantify metadata exposure in the simulator.

A core invariant is:

> safety check-in is an event at a designated point/window, not permission to track the participant continuously.

## What requires real hardware

- 4–6 PollicinoNet nodes;
- 2 checkpoint nodes and at least one moving relay;
- controlled campus/school-yard or lab-zone experiment;
- real duplicate/replay attempts;
- measured check-in delivery delay and missing-record reconciliation;
- optional BLE proximity handshake if that bearer is used.

No experiment should be used for real emergency accountability until independently validated.

## Messina teaching scenario

Run a synthetic field-trip drill across several controlled zones: for example school entrance, lab/courtyard and a remote safe point. Later, if permissions are appropriate, the same protocol can be tested on an educational route in the Messina/Rometta/Villafranca area using only designated checkpoints.

Each participant node receives a temporary synthetic identity. A teacher node knows the expected set. Checkpoint A is disconnected from checkpoint B; student relays carry signed check-ins between them. The final screen shows `received / pending / unknown`, not a live map of participants.

## Privacy / security

This use case has **high privacy sensitivity** because presence data can become surveillance data.

Requirements:

- opt-in experiment identities first;
- rotating/pseudonymous identifiers on the radio;
- no home addresses or continuous GPS trajectories;
- short retention after the drill;
- checkpoint/time windows coarse enough for the stated safety purpose;
- organizer-only mapping from experiment token to participant where needed;
- encryption/authentication of exact check-ins;
- relays do not gain roster access;
- no reuse for grading, discipline or attendance without a separate governance/legal analysis.

## Difficulty

**Medium.** The network record is small and testable; the real challenge is designing the identity, freshness and retention model so the demonstration teaches privacy-preserving networking rather than tracking.

## Research signal

Recent work continues to explore offline privacy-preserving nearby-device discovery using probabilistic identity filters and cryptographic set-membership techniques. That supports the direction of minimizing identity exposure, but PollicinoNet should start with a much simpler rotating-token experiment and measure its actual behavior.

Reference:

- https://www.tdcommons.org/dpubs_series/8772/
