# UC-137 — Privacy-Preserving Relay Budget Voucher and Admission Courier

## Idea

Give senders a bounded traffic budget that volunteer relay nodes can verify locally without requiring a stable real-world identity in every forwarding log.

The first implementation can use simple signed experiment vouchers. More advanced privacy-preserving credentials are only future research inspiration.

## Problem solved

A student DTN has scarce shared storage and contact time. If one application injects far more traffic than the rest, volunteer relay buffers and short rich-bearer windows can be consumed disproportionately.

A fully centralized account system would require continuous connectivity and create unnecessary tracking. UC-137 explores a simpler offline model: a sender proves that it still has budget for a traffic class and epoch, while relays record only pseudonymous voucher state.

## Actors / nodes

Budget issuer, sender/requester, volunteer relay nodes, destination/service, optional aggregate observer and optional UC-095 or UC-108 resource-policy components.

## Why PollicinoNet fits

Voucher proofs, epoch IDs and admission receipts are compact. Relays can decide whether to accept new work before committing storage or rich-bearer time.

Store-and-forward makes continuous central admission impractical, so locally verifiable bounded vouchers are a natural experiment.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: voucher class and epoch, compact admission proof, accept/reject and coarse remaining-budget status.
- BLE/Wi-Fi: richer voucher presentation or payload after admission.
- Internet: optional issuance or refill when available.
- Physical transport: pre-issued experiment vouchers can move with a device.

## What we can test now in software

Start with signed synthetic vouchers.

Test a sender reaching its epoch budget, the same voucher reaching multiple relays, relay reboot, stale local voucher state, per-traffic-class budgets, refill and expiry, and interaction with UC-095 fair share plus UC-108 queue pressure.

Measure admitted bundles, deferred bundles, duplicate voucher use and relay buffer occupancy in simulation.

## What requires real hardware

Use 6–10 boards. Script one high-volume synthetic sender and several normal senders, then compare a baseline with voucher-based admission using the same public test workload.

Measure accepted and deferred traffic plus buffer state. Do not claim anonymity or fairness from the first simple voucher prototype.

## Messina teaching scenario

Student nodes across Messina, Villafranca, Rometta/Venetico and Spadafora receive experiment-scoped relay budgets for public test traffic.

One scripted node produces a much larger workload than the others. Volunteer relays should preserve some capacity for ordinary course-pack or mailbox traffic while logging pseudonymous voucher epochs rather than names.

## Privacy / security

Avoid stable identity in relay telemetry; scope vouchers by short epoch and traffic class; protect issuance keys; make duplicate-use reconciliation explicit; do not use voucher logs to infer student behavior; and retain only aggregate experiment metrics where possible.

## Difficulty

High. Basic quotas are easy; disconnected reconciliation plus privacy minimization is the interesting part.

## Why this is distinct

UC-095 allocates volunteer resources fairly among admitted flows. UC-108 exposes current queue pressure. UC-137 controls how much new work a sender may inject into the relay fabric while minimizing identity leakage.

## Research / standards signal

The IETF Privacy Pass working group explored Anonymous Rate-Limited Credentials in 2026. Those March 2026 Internet-Drafts had expired by 29 September 2026, so they are useful research references rather than standards.

References:

- https://datatracker.ietf.org/doc/draft-ietf-privacypass-arc-protocol/
- https://datatracker.ietf.org/doc/draft-ietf-privacypass-arc-crypto/
