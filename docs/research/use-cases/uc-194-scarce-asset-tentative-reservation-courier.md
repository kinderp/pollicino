# UC-194 — Scarce Asset Tentative Reservation Courier

## Problem to solve
Two students in disconnected school islands request the same single used book or lab part. A stale catalogue can show both requests, but must not promise both an exclusive reservation.

## Actors and practical Messina scenario
Item owner, two synthetic requesters, school moderator, checkpoint, 4–6 student relay nodes; start with cardboard items and fabricated item IDs.

## Why PollicinoNet fits
Small request bundles include item hash, epoch, nonce and expiry. Only an authenticated owner may issue a final GRANTED/REFUSED result; TENTATIVE is not a grant. Physical handoff gets a distinct receipt.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: item/request/grant/receipt summaries; BLE: close-range scanning; Wi-Fi/Internet: listings and photos; physical carry: item and signed receipt.

## What can be tested immediately in software (proposed, not executed)
Simulate simultaneous requests, network partitions, late withdrawal, lost receipt, clock skew, owner reboot and duplicate proposals. Enforce at most one owner-issued active grant per item/epoch; measure settlement delay and unresolved conflicts.

## Physical hardware and required measurements
4–6 boards, two classroom islands and a teacher-owned laptop; reconcile deliberately conflicting paper-token reservations after reconnection. No payments in pilot.

## Privacy, security and implementation difficulty
MEDIUM–HIGH. Pseudonyms and designated public exchange stations, age-appropriate consent, anti-replay protection; no home addresses or payment identifiers.

## Difference from existing use cases
UC-043 lists reuse offers, UC-015 reconciles inventories and UC-042 records physical custody; UC-194 differentiates provisional holds from exclusive owner decisions.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.
