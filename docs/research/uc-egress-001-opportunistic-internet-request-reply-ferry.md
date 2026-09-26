# UC-EGRESS-001 — Opportunistic Internet request/reply ferry

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING MULTI-BEARER INTEGRATION

## Problem

A node may have no Internet now but still need to submit a small non-real-time request to an online service. Another node later reaches a trusted Wi-Fi/Internet gateway, forwards the request, stores the response and physically carries it back toward the requester.

The important application semantics are not generic content caching. They are **asynchronous request/reply correlation, idempotency, egress trust and response return**.

Examples suitable for an initial lab are:

- upload a small sensor batch to a school-owned service;
- ask a school API for the current public dataset/config generation;
- submit a content/reference wanted-list and receive a compact availability answer;
- query a controlled public-data mirror with a bounded, cacheable request.

An arbitrary web proxy or open relay is explicitly out of scope.

## Actors / nodes

- disconnected requester: sensor, student node, kiosk or robot;
- student-carried relay nodes;
- trusted egress node that eventually enters `RICH_HOME` or school Wi-Fi;
- allowlisted service adapter / lab server;
- return relay path, which may differ from the outbound path.

## Messina educational scenario

A fixed node in a pseudonymous inland/coastal cluster creates request `Q41` in the afternoon. A student's Pollicino node encounters it and carries the request home. When the node reaches trusted Wi-Fi, an egress adapter sends `Q41` to a school-controlled server. The small response `R41` is stored locally and can return through the school mixing phase the next morning, then through another student relay to the originating cluster.

```text
isolated node --LoRa--> student relay
                        [physical carry]
                              |
                         home/school Wi-Fi
                              |
                           Internet
                              |
                           response
                              |
                        [physical carry]
                              v
                         isolated node
```

Public town names may label simulation cohorts, but no geographic LoRa reach is assumed.

## Why PollicinoNet fits

This use case exercises the current bearer-runtime idea directly:

```text
OPPORTUNISTIC_DTN -> RICH_HOME -> OPPORTUNISTIC_DTN
```

The request must keep stable identity, expiry, retry/idempotency and provenance while the bearer changes. It also benefits from scheduled/student mobility and destination-aware routing without turning LoRa into an IP tunnel.

## Possible bearers

- LoRa for small request/response envelopes or references;
- BLE for local pickup/drop if separately enabled;
- Wi-Fi/LAN for egress at school/home;
- Internet only at a trusted gateway;
- physical carry between disconnected clusters and the gateway.

The system should prefer the rich bearer for actual Internet interaction. No PHY change is required.

## What can be tested now in software

1. request ID + idempotency key + reply correlation;
2. requests created while no gateway exists;
3. multiple competing egress relays;
4. egress relay disappears before sending;
5. duplicate request arrives at the service twice;
6. response returns by a different relay path;
7. usefulness deadline shorter than transport TTL;
8. cacheable versus non-cacheable requests;
9. tiny direct response versus rich response represented by a content reference;
10. queue scheduling when sensor uploads, DNA micro-information and egress requests share storage/contact budget;
11. compare first-available gateway, scheduled-mobility and destination-recency routing under identical synthetic contacts.

Start with a local fake HTTP/service endpoint so the networking semantics are testable without external credentials or uncontrolled Internet content.

## What requires real hardware

Real devices are required before claiming:

- actual transition reliability from LoRa/opportunistic state to home/school Wi-Fi;
- useful request/reply capacity per real encounter;
- real gateway encounter frequency;
- energy cost of Wi-Fi wake/connect plus LoRa carry;
- end-to-end wall-clock turnaround on student movement;
- behavior with real captive portals/NAT/router conditions.

HW-006 remains required before RF-derived byte/contact claims.

## Privacy / security

The egress node is a major trust boundary.

Requirements:

- no transparent/open proxy;
- allowlisted service adapters and bounded request types first;
- explicit authorization/capability for who may use an egress;
- no plaintext long-lived service credentials in relay bundles;
- preserve end-to-end application encryption where feasible;
- TLS/authentication at the Internet service boundary;
- strict idempotency for state-changing requests;
- rate/size quotas so a relay cannot be abused;
- no assumption that a student's personal mobile data plan is available or authorized;
- default first pilot to school/home Wi-Fi deliberately enrolled for the experiment;
- log request identifiers/status, not sensitive payloads, unless separately approved.

## Implementation difficulty

**Medium-high.** Request correlation is simple; safe egress authorization, idempotency and cross-bearer lifecycle are the real engineering work.

## Minimal measurable hypotheses

- H1: stable request identity survives `DTN -> rich egress -> DTN` without duplicate side effects.
- H2: scheduled/student mobility can return useful non-real-time replies even when requester and Internet are never concurrently connected.
- H3: a narrow service-adapter model gives most experimental value without the security surface of a generic IP/web proxy.

## Metrics

- request success before deadline;
- round-trip delay;
- duplicate service invocation count;
- responses delivered / orphaned;
- bytes carried on LoRa versus Wi-Fi/Internet;
- egress queue occupancy;
- number of gateway handoffs;
- retry/duplicate suppression;
- authorization failures.

## Success / kill criterion

**Continue** if a fake-service prototype demonstrates exact idempotent request/reply behavior across bearer transitions and produces a workload not reducible to ordinary content reference sync.

**Reject** a generic proxy design if allowlisted adapters satisfy the concrete use cases with less security surface.

## Gate decision

**PROTOTYPE / CONTINUE.** This is a strong practical use case for a student-carried network and directly exercises the existing bearer-runtime boundary without changing the LoRa PHY.

## Related precedent

KioskNet used ferries such as buses/cars to move data between rural kiosks and Internet gateways, with an Internet-side proxy: https://uwspace.uwaterloo.ca/items/658cdf6d-8d56-4ea5-b832-b94a1606979b .

Work on metropolitan DTN service access similarly studied public-transport carriers collecting user requests that require Internet access: https://doi.org/10.1155/2016/8434109 .

These precedents motivate asynchronous Internet service access; they do not provide performance evidence for PollicinoNet or Messina.
