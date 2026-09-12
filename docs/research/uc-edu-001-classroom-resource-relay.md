# UC-EDU-001 — Offline classroom resource and assignment relay

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Summary

A school can use the same student-carried PollicinoNet nodes as an asynchronous educational distribution network. Small signed notices, assignment metadata, resource references and receipts travel through LoRa/store-carry-forward; larger authorized teaching materials are fetched later through school/home Wi-Fi, NAS or Internet.

The return path can carry encrypted submission receipts or compact submission references back toward school without exposing student work to relay peers.

## Problem solved

Educational workflows usually assume continuous access to a school platform. A teaching network built specifically to study intermittent connectivity should have a useful application that still works when end-to-end Internet connectivity is absent.

Examples:

- distribute a new assignment or correction to a class;
- announce that a new lab dataset/resource exists;
- carry a signed content reference toward students who missed the morning school contact;
- return an acknowledgement that a resource was received;
- carry an encrypted submission reference/receipt toward the school gateway.

The objective is not to replace the official school platform; it is a concrete, consent-based laboratory workload for DTN behavior.

## Actors / nodes

- teacher/school gateway;
- student-carried pseudonymous nodes;
- home Wi-Fi/NAS/Internet gateway;
- optional classroom fixed node;
- optional Learning-Lab/Raiatea adapter at the rich-network edge.

## Messina educational scenario

At the morning school mixing phase, many nodes receive assignment generation `A17`. A student absent that morning can still receive the compact signed assignment descriptor later from a peer encountered in a territorial cluster. At home the node resolves the authorized PDF/dataset from the school server or NAS. The following day a compact encrypted receipt can return via peers to the school gateway.

Scenario labels may use public town names such as Rometta, Saponara, Spadafora or Villafranca, but exact home addresses and student routes must never be part of the research dataset.

## Why PollicinoNet fits

The workload benefits from:

- store-carry-forward across school/home phases;
- priority and expiry;
- exact content identity and manifests;
- reference-mule behavior for larger files;
- duplicate suppression and reconciliation;
- multi-bearer handover;
- provenance/authentication of teacher-issued metadata.

It is also a very understandable demonstration for students: the network they are studying carries the metadata for an actual classroom exercise.

## Bearers

- LoRa: assignment metadata, hashes, short references, receipts;
- BLE: optional close-range classroom exchange;
- Wi-Fi/LAN: complete resources/submissions at school or home;
- Internet: official school/Learning-Lab/Raiatea endpoint when available;
- physical transport: student mobility connects otherwise separate clusters.

## What we can test now in software

Generate classes with attendance gaps and two daily phases: dense school mixing and sparse territorial contacts. Compare:

1. school-gateway-only delivery;
2. Direct Delivery;
3. Epidemic relay;
4. bounded-copy routing;
5. reference-only versus full-small-object transfer.

Metrics include percentage receiving the assignment before its educational deadline, time-to-first-receipt, scarce-link bytes, duplicate traffic, rich-path fetch success and number of relays.

A second experiment can model return receipts separately so delivery and return-path reliability are not conflated.

## Hardware required later

Real boards are needed to measure:

- actual contact opportunities during school transitions and ordinary student movement;
- useful metadata bytes per encounter;
- battery cost and usability;
- whether device handling is practical for a teaching pilot;
- real handover from LoRa state to school/home Wi-Fi.

No real student deployment should begin before privacy/consent, device management and HW-006 evidence are ready.

## Privacy and security

Educational data can be personal even when small.

Initial boundary:

- use pseudonymous node IDs in experiments;
- teacher-issued assignment metadata should be signed;
- do not broadcast grades, attendance, names or personal learning profiles;
- student submissions/receipts must be end-to-end encrypted or represented by opaque capability/reference tokens;
- relay peers must not need to decrypt payloads;
- retention must expire classroom artifacts after the relevant period;
- participation in a real student pilot requires school authorization and appropriate consent/data-protection review.

## Difficulty

**Low-medium for synthetic/public-resource experiments; medium-high for real student data.**

A safe first pilot can use public/open teaching resources and anonymous delivery receipts, avoiding personal data entirely.

## Research context

Recent research continues to explore DTN-based educational delivery for rural/intermittently connected environments, including campus prototypes, reinforcing that educational resources are a legitimate delay-tolerant application workload. This case is narrower: it is designed primarily as a measurable application for the PollicinoNet student network itself.

## Success criteria

The use case is valuable if peer relaying increases on-time resource discovery versus gateway-only delivery without excessive traffic or privacy exposure.

## Decision

**PRIMARY USE CASE / PROTOTYPE-DRIVING.**

It is one of the most direct ways to turn the Messina student network into both a networking laboratory and a useful demonstrator, while keeping full educational payloads on rich links whenever possible.
