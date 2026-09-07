# UC-026 — Delegated Offline Action Ticket

## Idea

Carry a **small signed permission** through the disconnected network so a device can authorize one narrowly defined, non-safety-critical action even when the central authority is offline.

Example teaching ticket:

```text
action: robot.calibrate
subject: demo-rover-3
max_uses: 1
valid_after_epoch: 41
expires_epoch: 44
parameters: bounded preset A
```

The relay carrying the ticket does not become an administrator. It transports a scoped authorization object that the target independently verifies.

## Problem solved

Many offline systems fall into one of two bad extremes:

1. require live contact with a central server for every action; or
2. give devices broad long-lived credentials so they keep working offline.

A narrow delegated ticket offers a third option: authorize exactly one class of action, for one target, for a limited period/use count, with auditable provenance.

## Actors / nodes

- teacher/operator/authority node issuing a synthetic ticket;
- student relay/store-and-forward nodes;
- target robot, sensor, gateway or demo actuator;
- optional audit/server node that later receives the result;
- optional trust/time services from UC-019 and UC-020.

## Why PollicinoNet fits

Authorization tickets are tiny, high-value objects that naturally tolerate delay:

- **DISCOVERY:** ticket availability/target hint without revealing unnecessary details;
- **EXACT:** signed ticket bytes, issuer key ID, nonce, scope, constraints and execution receipt;
- **SEMANTIC:** optional human explanation such as "calibration permitted", never the authority source itself.

LoRa can transport the ticket and a compact execution receipt. Larger logs/results can move later over richer bearers.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** signed action ticket, nonce, epoch/freshness metadata and compact receipt;
- **BLE:** local transfer to a nearby target and detailed status;
- **Wi-Fi/LAN:** richer logs/results and policy synchronization;
- **Internet:** optional issuer/audit synchronization when available;
- **physical transport:** a student/device carries the signed ticket to an isolated target.

## What we can test now in software

- define a canonical `ActionTicket` schema with issuer, target, action, parameter bounds, nonce, validity/freshness, max uses and signature;
- verify signatures offline;
- reject wrong target, wrong action, out-of-bounds parameter and altered ticket;
- reject replay after a one-use ticket has been consumed;
- combine with UC-019 trust epochs so a revoked issuer/ticket key is not silently trusted forever;
- combine with UC-020 explicit time uncertainty rather than assuming a perfect clock;
- simulate duplicate tickets arriving by multiple relays;
- generate an exact `ExecutionReceipt` referencing the ticket and result object hash;
- crash/restart the target around ticket consumption and ensure once-only semantics survive;
- test fail-closed behavior when freshness/authorization cannot be established;
- measure ticket propagation delay, replay rejection, stale-ticket rejection and duplicate overhead.

Core invariant:

> possession of a ticket grants only the ticket's explicit scope; possession of the relay device grants nothing extra.

## What requires real hardware

- 3–4 boards with one isolated target;
- a harmless demo actuator such as LED, buzzer, servo in a fixture or rover calibration routine;
- a moving relay that carries the ticket across a partition;
- deliberate duplicate/replay attempts;
- power-cycle of the target before/after execution to test durable use-count state;
- measured LoRa delivery/contact behavior.

Do not use this prototype for door locks, vehicles, safety interlocks, emergency actuators or other high-consequence control.

## Messina teaching scenario

A teacher node creates a one-use ticket allowing `demo-rover-3` in another classroom island to run a calibration pattern. No live Internet path exists. A student relay carries the ticket. The rover independently verifies issuer, target, scope, freshness and nonce, runs the harmless routine once, and later sends a signed receipt back through PollicinoNet.

A second exercise revokes the issuer key using UC-019 before the relay arrives and checks that the target rejects the stale authority state once the newer trust epoch is available.

## Privacy / security

This use case is intentionally security-heavy. Tickets need canonical signing, issuer/target binding, anti-replay, bounded parameters, durable consumption state and explicit expiry/freshness handling. The target must not execute a human-readable semantic instruction unless it corresponds to an exact valid ticket.

Do not put broad bearer credentials or reusable administrative keys into relay storage. Audit receipts should reveal only what is necessary.

## Difficulty

**High.** The payload is tiny; the difficulty is getting authorization, replay resistance, crash consistency, trust freshness and parameter bounding correct.

## Research signal

Current authorization work is moving toward cryptographically scoped, auditable delegation that can be verified without contacting the issuer at decision time. A March 2026 IETF Internet-Draft on Sovereign Policy Token Transactions describes capability-like transaction tokens with scope limits and offline verification. PollicinoNet should treat such work only as design inspiration and keep its own ticket format simple and independently testable.

Reference:

- https://datatracker.ietf.org/doc/html/draft-coetzee-oauth-spt-txn-tokens-00
