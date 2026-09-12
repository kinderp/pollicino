# UC-SERVICE-001 — Offline service and capability directory

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING INFRASTRUCTURE

## Problem

In a disconnected network, knowing that a peer exists is often not enough. A node may need to know **what useful service another node can provide** and whether that advertisement is still fresh.

Examples:

- a home/school node can act as an Internet egress;
- a lab PC can execute a bounded compute job;
- a NAS can resolve a content reference;
- a fixed node can provide a sensor topic;
- a gateway can accept a configuration/firmware request;
- a local kiosk can answer a public dataset query;
- a robot/base station can expose a delayed log-upload rendezvous.

When the network is intermittent, the service provider and requester may never be online at the same time. A student-carried node can therefore ferry a compact **capability advertisement** such as `service type + opaque provider ID + generation + expiry + coarse rendezvous hints`.

The key question is not generic neighbor discovery. It is:

> can nodes discover and select currently useful services through delayed, stale-prone advertisements without requiring Internet-wide discovery or exposing sensitive topology?

## Actors / nodes

- requester node;
- service-provider node;
- student-carried relays;
- school/home gateway;
- application adapter for a specific service class;
- optional authoritative directory for signed/public services.

## Messina educational scenario

A school lab may expose several controlled services:

- `gateway/public-data-v1`;
- `resolver/class-materials-v2`;
- `compute/tiny-python-job-v1`;
- `sensor/weather-station-summary-v1`.

A node in a Rometta-like logical cluster learns at school that service `resolver/class-materials-v2` exists and carries the signed advertisement home. Another node encountered later can learn the provider coordinate even though the provider is currently unreachable. The request itself may then travel by Pollicino store-carry-forward and eventually execute when a suitable gateway is reached.

Public place names are cohort labels only; no RF reach between towns is assumed.

## Why PollicinoNet fits

PollicinoNet already separates:

- discovery/rendezvous from exact payload transfer;
- application semantics from transport;
- scarce-link objects from rich-path resolution;
- connected-school and opportunistic-territorial phases.

A compact service directory can therefore remain an application/infrastructure object above the existing transport, while EGRESS/COMPUTE/CONTENT use cases consume it.

This also gives a concrete purpose to future bearer-aware routing inputs: the best route is sometimes the route toward *a capable service*, not a fixed named destination.

## Possible bearers

- LoRa for compact service advertisements and requests;
- BLE for nearby service discovery if enabled;
- Wi-Fi/LAN for actual rich service execution;
- Internet behind an enrolled gateway only when the service policy permits it;
- physical carry of cached advertisements and requests between disconnected clusters.

No PHY change is required.

## What can be tested now in software

1. explicit service records with `service_type`, provider ID, generation and expiry;
2. provider appears/disappears;
3. stale advertisement remains in a relay cache;
4. multiple providers for the same service;
5. nearest/first-known versus freshness/cost-aware provider selection;
6. provider capability changes generation;
7. service is revoked or withdrawn;
8. advertisement loop/duplicate suppression;
9. directory reconciliation between two nearly identical caches;
10. request generated from a stale service record and safely rejected later;
11. EGRESS request chooses among two enrolled gateways;
12. COMPUTE job chooses a node that advertises the required capability;
13. reference resolver advertises only a provider class, not sensitive filesystem paths;
14. measure advertisement overhead separately from actual service traffic.

Start with simple signed explicit records. Do not invent a general service-discovery wire protocol unless repeated use cases demonstrate that a shared encoding reduces complexity.

## Minimal measurable hypotheses

- H1: ferrying compact capability records materially increases successful service rendezvous versus discovering services only during direct encounters.
- H2: generation/expiry prevents stale provider state from causing unbounded misrouting or retries.
- H3: one generic minimal record can serve at least EGRESS, COMPUTE and CONTENT resolver experiments without leaking application-specific internals.

## Metrics

- successful service rendezvous before deadline;
- stale advertisement use/rejection count;
- directory bytes exchanged;
- duplicate advertisements suppressed;
- provider-selection success/failure;
- request round-trip delay;
- number of relays before a suitable provider is found;
- advertisement convergence time;
- revoked/expired service records suppressed.

## What requires real hardware

Real boards are required before claiming:

- actual advertisement capacity over LoRa;
- real school/home service discovery latency;
- power cost of periodic advertisement/probing;
- real behavior when Wi-Fi appears/disappears;
- whether provider readiness can be represented reliably from embedded runtime state;
- real gateway/compute/NAS handoff success.

HW-006 remains required before RF/contact-capacity claims.

## Privacy / security

Service discovery can leak topology and valuable capabilities.

Requirements:

- advertise the minimum capability necessary;
- do not include student addresses, Wi-Fi credentials, filesystem paths or personal device details;
- pseudonymous/rotating provider IDs where stable identity is unnecessary;
- signed generations for authoritative school services;
- explicit expiry and revocation path;
- requester authorization remains separate from discovery;
- discovering `compute` or `egress` must not imply permission to use it;
- rate/size quotas and allowlisted service classes for first pilots;
- avoid turning the directory into a scanner for personal home devices.

## Implementation difficulty

**Medium.** A minimal service record and cache are straightforward. Correct freshness, authorization boundaries and cross-use-case abstraction require discipline.

## Relationship to existing use cases

- Not `UC-EGRESS-001`: EGRESS executes asynchronous Internet requests; SERVICE tells a node which enrolled egress may exist.
- Not `UC-COMPUTE-001`: COMPUTE carries jobs/results; SERVICE advertises available compute capability.
- Not `UC-CONTENT-001`: CONTENT carries references; SERVICE can advertise a resolver/provider class.
- Not ordinary bearer discovery: bearer discovery answers `can I communicate now?`; SERVICE answers `what application capability can this node eventually provide?`.

## Success / kill criterion

**Continue** if at least three existing use cases can reuse the same minimal service record and a synthetic experiment shows useful rendezvous benefit under intermittent contacts.

**Keep domain-specific** if EGRESS/COMPUTE/CONTENT each require incompatible semantics and a generic directory adds more bytes/state than it removes.

## Gate decision

**PROTOTYPE / CONTINUE.** Strong infrastructure candidate, but adoption of a shared wire format remains gated by measured reuse across independent use cases.

## Related precedent

DTN IP Neighbor Discovery explicitly discussed advertising services available from a discovered neighbor and the trade-off between combining service discovery with neighbor discovery versus negotiating it separately on scarce links. A current 2026 IETF DTN draft, SAND, also studies secure advertisement and neighborhood discovery across heterogeneous links.

- https://datatracker.ietf.org/doc/id/draft-irtf-dtnrg-ipnd-00.html
- https://datatracker.ietf.org/doc/draft-ietf-dtn-bp-sand/

These references motivate the problem; they do not define PollicinoNet's application model or provide LoRa field evidence.
