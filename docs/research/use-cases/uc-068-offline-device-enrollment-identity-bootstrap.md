# UC-068 — Offline Device Enrollment and Identity Bootstrap

## Idea

Before a student board can safely relay messages, cache content or receive updates, the network needs to know **which device it is, who is allowed to enroll it and which key belongs to it**. This use case lets a new or factory-reset PollicinoNet node join a trusted teaching deployment even when the school enrollment service is not reachable at the same moment.

The goal is not to invent a new PKI. PollicinoNet acts as the delay-tolerant transport for a small enrollment workflow: a device creates a bootstrap request, a trusted registrar later approves it, and an enrollment result eventually returns through student relay/store-and-forward nodes.

## Problem solved

A real Messina-wide teaching network may contain tens of boards distributed among students. Some boards will be new, re-flashed, replaced or reset. A hard-coded shared secret for every board scales badly and makes one leak affect the whole network.

We need a safer flow that answers:

- is this really the device we intended to enroll?
- which public key becomes its network identity?
- which role/capabilities does it receive?
- how long is the enrollment valid?
- what happens if the request or approval arrives twice or very late?
- how does a device distinguish a valid registrar from a malicious relay?

## Actors / nodes

- new or factory-reset PollicinoNet board;
- teacher/lab enrollment station or registrar;
- one or more student relay/store-and-forward nodes;
- optional school server/CA when Internet or LAN is available;
- optional close-range helper such as QR/NFC/BLE for proof that the operator is physically with the board.

## Why PollicinoNet fits

Enrollment messages are small, signed state transitions and tolerate delay much better than firmware or datasets.

- **DISCOVERY:** `unenrolled device present`, enrollment service availability, short bootstrap rendezvous token;
- **EXACT:** device key/fingerprint, enrollment request ID, registrar decision, role/capability set, trust epoch and resulting credential/certificate hash;
- **SEMANTIC:** friendly labels such as `student-board`, `sensor-node` or `lab-relay`, never a replacement for the exact cryptographic identity.

LoRa can carry compact enrollment state. Richer bearers can transport complete certificate chains or diagnostic evidence if needed. A relay never needs authority to approve the device; it only transports signed objects.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** bootstrap request digest, nonce/challenge, device key fingerprint, status, approval/result reference;
- **BLE/NFC/QR:** close-range association between a physical board and its bootstrap request;
- **Wi-Fi/LAN:** complete enrollment objects, certificates, attestation evidence and policy snapshots;
- **Internet:** optional connection to an authoritative registrar/CA;
- **physical transport:** a student carries the pending request or approved response between disconnected zones.

## What we can test now in software

Define a minimal deterministic state machine, for example:

```text
FACTORY
  -> REQUEST_CREATED
  -> REQUEST_SEEN_BY_REGISTRAR
  -> APPROVED | REJECTED
  -> CREDENTIAL_ISSUED
  -> INSTALLED
  -> ACTIVE
```

Then test:

- duplicated and reordered enrollment messages;
- stale approval after a newer request replaced the old one;
- wrong-device approval where the key fingerprint does not match;
- replay of an already-used enrollment result;
- registrar key rotation;
- explicit `unknown/stale trust state` instead of silently accepting;
- two simultaneous enrollment attempts for the same physical board;
- factory reset followed by re-enrollment with a new key;
- role-limited enrollment such as `relay-only` versus `sensor-publisher`;
- integration with UC-019 trust/revocation, UC-020 freshness, UC-048 credentials and UC-067 service naming.

A key invariant is:

> a transport relay may deliver enrollment evidence, but it can never become the authority merely because it carried the message.

## What requires real hardware

- 3–5 real boards;
- one board deliberately erased/reset;
- one registrar laptop or trusted board;
- at least one student relay that sees the requester and registrar at different times;
- optional QR/BLE close-range confirmation;
- measured time from first request to successful activation and measured radio/contact behavior.

No claim about LoRa range, enrollment latency or reliability should be made before these measurements exist.

## Messina teaching scenario

A new board is issued to a student in Rometta while the authoritative enrollment laptop is at school in Messina. The board creates a bootstrap request containing a fresh nonce and its new public-key fingerprint. A student relay later carries the compact request to school. The teacher verifies the device using a controlled QR/physical handoff and approves a narrow role. The signed result returns later through another relay and the board becomes active.

A second exercise deliberately sends an old approval after the board has generated a new request. The node must reject it rather than accepting the first signed object it sees.

## Privacy / security

Enrollment metadata is security-sensitive even when it contains no personal content.

- do not broadcast student names, home addresses or personal identifiers;
- use device pseudonyms/fingerprints and keep the mapping to people outside the radio payload;
- approval must be signed by an independently trusted registrar key;
- bind every approval to one exact request, device key, role set and freshness context;
- fail closed when trust/revocation state is too stale for the policy;
- rate-limit bootstrap requests so factory/untrusted nodes cannot fill relay queues;
- use close-range confirmation where physical possession matters;
- do not treat attestation claims as infallible proof of uncompromised hardware.

## Difficulty

**Medium–High.** The messages are small and easy to relay; the hard part is getting trust transitions, replay handling, reset/re-enrollment and role scoping correct.

## Research / standards signal

IETF BRSKI and BRSKI-AE define secure bootstrapping and certificate enrollment patterns for network devices. RFC 9733 (March 2025) extends BRSKI with alternative enrollment mechanisms based on authenticated signed objects. RFC 9711 (April 2025) defines Entity Attestation Tokens for carrying attested device claims. PollicinoNet should borrow the separation of bootstrap identity, enrollment authority and attestation evidence without assuming those protocols' transport model.

References:

- https://www.rfc-editor.org/rfc/rfc9733.html
- https://www.rfc-editor.org/rfc/rfc9711.html
