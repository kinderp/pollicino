# UC-088 — Delay-Tolerant Web / API Fetch Courier

## Idea

Allow an offline PollicinoNet node to submit a **small, bounded read request** for a public web/API resource, let that request travel until it meets a trusted Internet gateway, and return the fetched response later through store-and-forward relays.

The first version is deliberately narrow: allow-listed `GET`-style retrieval only, not interactive browsing, login sessions, arbitrary POST actions or a transparent Internet tunnel.

## Problem solved

A node may have working LoRa contacts but no Internet path. Today it can ask nearby nodes for content they already possess, but sometimes the desired object exists only on an Internet service.

Examples:

- retrieve one public JSON weather or timetable snapshot for a classroom experiment;
- fetch the newest public release manifest for a software project;
- retrieve a public document by exact URL;
- ask a school gateway for one allow-listed API response;
- fetch a small public status page while the requester remains offline.

The requester and the Internet gateway do not need to be connected at the same time.

## Actors / nodes

- offline requester;
- student relay/store-and-forward nodes;
- one or more trusted Internet gateway nodes;
- optional response cache;
- public or school-controlled HTTP/API endpoint.

## Why PollicinoNet fits

The request is small and delay-tolerant, while the response can be returned later over the best available bearer.

- **DISCOVERY:** advertise that a node currently offers an `internet-fetch` capability and its policy class;
- **EXACT:** bind request ID, normalized URL/resource identifier, method, selected headers, response hash, fetch time and gateway identity;
- **SEMANTIC:** human labels such as `public-json`, `release-manifest` or `school-resource` may help discovery, but cannot replace the exact request.

PollicinoNet already knows how to carry requests, discover capabilities and switch to richer bearers. This use case composes those mechanisms into a familiar application.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** fetch request ID, compact normalized target, policy class, expiry, gateway advertisement, response-ready notice and response hash;
- **BLE:** nearby request/response synchronization for modest payloads;
- **Wi-Fi/LAN:** HTTP response body, headers and larger evidence;
- **Internet:** used only by the gateway that actually performs the fetch;
- **physical transport:** a student device carries pending requests to an Internet-connected island and later returns cached responses.

## What we can test now in software

Define a bounded `FetchRequest`:

```text
request_id
requester_pseudonym
target_id_or_normalized_url
method = GET
allowed_header_profile
max_response_bytes
created_epoch
expiry
policy_id
```

and a `FetchResult`:

```text
request_id
gateway_id
status_class
fetched_epoch
response_hash
content_type
response_size
cache_policy
body_ref
```

Then test:

- requester and gateway never online simultaneously;
- duplicate requests reaching two gateways;
- idempotent deduplication;
- gateway fetch failure and later retry;
- redirects inside/outside the allow-list;
- response larger than the declared limit;
- stale result arriving after request expiry;
- two gateways returning different versions at different times;
- cached result versus forced fresh fetch;
- malformed URL/headers and SSRF-style attempts;
- result metadata arriving over LoRa before the body is available over Wi-Fi;
- request cancellation overtaking an older request copy.

Useful metrics: request-to-fetch delay, fetch-to-delivery delay, duplicate gateway work, response age on delivery, cache hit ratio and bytes per bearer.

A useful invariant is:

> the returned body must remain bound to the exact normalized request, gateway identity and fetch time that produced it.

## What requires real hardware

A first physical experiment needs:

- 4–6 LoRa nodes;
- one laptop/Raspberry Pi acting as an Internet gateway;
- two disconnected requester groups;
- one or two student relays;
- a small public or school-hosted test endpoint.

The physical test should deliberately disconnect the requester from Wi-Fi/Internet while leaving the gateway connected. The request travels by PollicinoNet; the response returns later.

No claim about end-to-end latency or delivery probability should be made until measured on the real student network.

## Messina teaching scenario

Create coarse network islands such as school, Villafranca, Rometta/Venetico and Spadafora. A student node in one island requests an allow-listed public JSON resource while intentionally offline from the Internet. A relay later reaches the school gateway, which performs the fetch. The result comes back through a different relay.

This is a useful demonstration that **Internet reachability and PollicinoNet reachability are different resources**.

## Privacy / security

Web requests reveal interests and can also become an attack surface for the gateway.

- use an explicit allow-list or capability policy in the first implementation;
- allow `GET`/read-only retrieval only;
- reject local/private IP ranges and arbitrary proxying to prevent SSRF;
- cap response size and content types;
- do not forward cookies, Authorization headers or browser session state;
- encrypt request metadata if the target itself is sensitive;
- authenticate the gateway result;
- preserve HTTPS verification at the gateway;
- record fetch time because the same URL can change;
- do not treat possession of a URL as authorization to retrieve a private resource;
- do not use this as a covert Internet tunnel.

## Difficulty

**Medium-high.** The store-and-forward mechanics are straightforward. The difficult part is safe request normalization, gateway policy, result freshness, caching and avoiding accidental transformation into a general-purpose proxy.

## Why this is distinct from nearby use cases

- **UC-024:** asks the network for content that some PollicinoNet node may already hold.
- **UC-034:** moves a query toward a known/local Raiatea corpus.
- **UC-083:** carries standing subscriptions to future topic changes.
- **UC-088:** lets a disconnected requester cause a later, bounded **Internet fetch** by a trusted gateway and receive the exact response asynchronously.

## Research / implementation signal

The IETF has explored encapsulating HTTP requests/responses over Bundle Protocol for delay-tolerant networks, explicitly because ordinary end-to-end timing assumptions do not hold in DTNs. The latest published draft found during this review is `draft-blanchet-dtn-http-over-bp-04` from 28 September 2025; it expired on 1 April 2026, so it is only a work-in-progress reference, not a standard.

References:

- https://datatracker.ietf.org/doc/html/draft-blanchet-dtn-http-over-bp-04
- https://www.rfc-editor.org/rfc/rfc9171.html
