# UC-138 — Dead-Letter and Non-Delivery Resolution Courier

## Idea

Make non-delivery a first-class, explainable outcome instead of allowing a bundle or application job to retry indefinitely.

When an exact object cannot be delivered because its lifetime expires, the destination disappeared, no compliant route exists, storage is exhausted, policy blocks every path, or the object is superseded, PollicinoNet records a compact terminal or recoverable failure state. A later relay can carry that state back to the origin, which may retry with a new policy, choose a new destination, salvage the payload to a designated dead-letter cache, or deliberately abandon it.

## Problem solved

In a long-partition store-and-forward network, "not delivered yet" can mean no useful contact yet, destination unavailable, no policy-compliant path, expiry, storage pressure, supersession, or application rejection. Without explicit failure resolution, stale work can circulate, occupy volunteer buffers and produce confusing retransmissions.

## Actors / nodes

Sender/origin application, student relay/store-and-forward nodes, final endpoint/service, optional dead-letter or salvage cache, optional UC-098 receipt collector, and UC-108/UC-134 policy components.

## Why PollicinoNet fits

Failure metadata is tiny compared with most payloads and can propagate asynchronously even after the payload itself has been dropped. Useful states include PENDING, DEFERRED, DELIVERED, EXPIRED, NO_ROUTE, ENDPOINT_UNAVAILABLE, POLICY_BLOCKED, STORAGE_DROPPED, SUPERSEDED, APPLICATION_REJECTED, SALVAGE_AVAILABLE and UNKNOWN.

The frozen LoRa PHY remains unchanged.

## Possible bearers

- LoRa: object/job ID, compact failure reason, state epoch, retry/salvage hint and acknowledgement.
- BLE: local reconciliation of dead-letter state.
- Wi-Fi/LAN: payload salvage, full receipts and diagnostic logs.
- Internet: optional alternate endpoint or authoritative retry policy.
- Physical transport: laptop/phone/SD can carry an undelivered object to a designated salvage point.

## What we can test now in software

Simulate expiry, endpoint removal, temporary/permanent no-route, UC-134 policy eliminating all candidate paths, UC-108 storage rejection, supersession while an old copy is in flight, duplicate/reordered failure reports, stale NO_ROUTE after successful delivery, conflicting reasons and sender unreachability.

Compare retry-forever, retry-until-expiry, terminal failure, bounded salvage and application-specific retry. Measure stale queue occupancy, unnecessary retransmissions, explainable-failure rate, salvage success and time spent in UNKNOWN.

## What requires real hardware

Use 5–8 boards with one sender, one destination and several relays. Withdraw the destination, constrain one relay buffer, create a synthetic no-compliant-path case and let one harmless bundle expire. Then restore a destination or salvage cache.

Measure actual control messages, queue occupancy, observed lifecycle transitions and recovered payloads. Do not generalize physical reliability from one trial.

## Messina teaching scenario

A public course-pack fragment starts in Messina and is intended for a temporary service in Rometta/Venetico. One experiment disables that service before the relay arrives. A second route exists only through a relay class that the object is not allowed to use. Instead of circulating indefinitely, the object becomes ENDPOINT_UNAVAILABLE or POLICY_BLOCKED and the reason returns through Villafranca. A teacher-controlled salvage cache can then accept the exact object, or the sender can create a new delivery intent for Spadafora.

## Privacy / security

Failure reasons can leak topology, destination existence or policy state. Use opaque endpoint/object identifiers where needed, return coarse reason classes, authenticate terminal-state reports, bind reports to the exact object/job and lifecycle epoch, never let a stale failure overwrite later DELIVERED, rate-limit retries and keep dead-letter retention bounded.

## Difficulty

**Medium.**

## Why this is distinct

UC-098 records selected forwarding/delivery events; UC-138 decides what the application should do when delivery cannot complete. UC-108 controls admission under queue pressure. UC-077 handles lifecycle deletion/expiry of replicated content. UC-112 resumes interrupted transfers.

## Standards signal

Bundle Protocol v7 defines delivery failure behavior, expiration and status-report reason codes such as depleted storage, destination endpoint unavailable and no known route, while warning that status reporting itself must remain bounded.

References:

- https://www.rfc-editor.org/rfc/rfc9171.html
- https://www.rfc-editor.org/info/rfc4838/
