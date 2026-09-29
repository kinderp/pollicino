# UC-134 — Policy-Constrained Relay Eligibility and Sensitive-Path Courier

## Idea

Let an exact object declare which classes of relay are allowed to carry it, so PollicinoNet can choose a longer or slower path rather than violate a transport policy.

The goal is not DRM. It is policy-aware forwarding by cooperating nodes.

## Problem solved

A DTN may discover many possible paths, but not every relay should necessarily carry every object.

Examples: a synthetic sensitive document may be allowed on school-managed relays but not volunteer caches; ciphertext may be relayable everywhere while a decryption-share object is restricted; a dataset may be allowed to leave one island only through a designated gateway.

Without path constraints, routing optimizes reachability while silently ignoring the handling policy attached to the data.

## Actors / nodes

Publisher/policy issuer, requester, student relay nodes with different trust/ownership classes, opportunistic caches, gateway nodes and optional UC-076 policy evaluator.

## Why PollicinoNet fits

Relay eligibility is compact control metadata. LoRa can advertise an opaque policy/profile ID and route capability, while payloads stay encrypted and use richer bearers.

Store-carry-forward makes this especially interesting because a node may intentionally wait for a later eligible relay instead of taking the first contact.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: policy/profile ID, relay-class capability, route refusal reason and compact next-hop hint.
- BLE/Wi-Fi: payload transfer only after policy evaluation.
- Internet: optional authoritative policy refresh.
- Physical transport: an eligible managed device or sealed storage carrier.
- Encrypted ciphertext may use a broader carrier set than key material when policy explicitly allows it.

## What we can test now in software

Create a contact graph with relay classes such as managed, volunteer, gateway and sealed-only.

Compare reachability-only routing, policy-constrained routing, policy plus UC-095 volunteer budgets, and policy plus UC-108 queue pressure.

Inject policy changes, stale policy state, an ineligible shortest path, no compliant path, encrypted-vs-key objects, and a relay lying about its class.

Measure logical delivery success, policy violations, added delay in the simulated trace and number of NO_COMPLIANT_PATH outcomes. These are software metrics, not radio claims.

## What requires real hardware

Use 6–10 boards assigned synthetic relay classes. Give one object a path policy that deliberately excludes the most convenient relay and verify that it waits for a later compliant route.

Measure only observed contacts, completed transfers and policy decisions. Do not infer privacy or confidentiality from path choice alone.

## Messina teaching scenario

Create coarse islands for Messina, Villafranca, Rometta/Venetico and Spadafora. Some experiment boards are marked school-managed, others volunteer.

A public course pack can use every relay. A synthetic sealed case file may transit only managed nodes. Students can compare how the same physical contact trace produces different admissible paths without recording home addresses or personal routes.

## Privacy / security

Relay class itself can reveal ownership or affiliation, so use coarse, experiment-scoped labels. Authenticate policy issuers and relay attestations where required. Return POLICY_UNKNOWN or NO_COMPLIANT_PATH instead of silently relaxing constraints.

Path policy does not protect plaintext by itself; combine it with encryption, UC-021, UC-019 and appropriate application authorization.

## Difficulty

Medium-high. Basic filtering is simple; stale policy, route discovery, privacy of labels and lying/misconfigured relays make the real problem interesting.

## Why this is distinct

UC-076 decides whether an actor may use an artifact. UC-021 protects sensitive plaintext from carriers. UC-134 decides which relay classes may transport which exact objects and makes non-compliant routes unavailable even if they are topologically attractive.

## Standards signal

Bundle Protocol Security separates cryptographic protection from network-specific security policy and explicitly notes that policy depends on each network's operational context. UC-134 explores that policy layer experimentally.

References:

- https://www.rfc-editor.org/info/rfc9172
- https://www.rfc-editor.org/info/rfc9171
