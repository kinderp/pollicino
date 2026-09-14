# UC-058 — Floating Local Service and State Handoff

## Idea

Let a useful local service **move with the network instead of being tied to one permanently reachable server**. A student-carried laptop/Raspberry Pi can host a small offline service for a while, then hand the service manifest and bounded state to another node that is more likely to meet the next users.

Examples include a local documentation/search service, a tiny classroom web app, a safe inference endpoint, a queue/status dashboard, or a read-mostly community information service.

This is not ordinary file replication. The experiment asks whether PollicinoNet can coordinate **service placement, handoff and continuity** across long disconnections.

## Problem solved

UC-041 can expose a pop-up hotspot and UC-040 can pre-position content, but a mobile community may need a service to remain available even when the original host leaves.

A central cloud endpoint fails this requirement when Internet is absent. Copying the service everywhere may also waste storage, compute and energy.

PollicinoNet can carry compact placement/control state over LoRa while containers, static assets or checkpoints move over richer bearers when contacts permit.

## Actors / nodes

- student-carried laptop/Raspberry Pi/mini-PC capable of hosting the service;
- LoRa companion nodes advertising service availability and handoff intent;
- nearby clients;
- student relay/store-and-forward nodes;
- optional school server that seeds an authoritative service image/state;
- optional UC-008 contact-history input for choosing the next host.

## Why PollicinoNet fits

Service placement is naturally delay-tolerant when the service is non-safety-critical and can tolerate temporary unavailability.

- **DISCOVERY:** `service S available`, `handoff candidate`, coarse capacity/load and expected availability window;
- **EXACT:** service image/root hash, configuration hash, state-checkpoint hash, epoch and handoff transaction ID;
- **SEMANTIC:** friendly label such as `classroom-search` or `local-docs`, never a substitute for exact service identity.

LoRa only coordinates who should host what. Service bytes and checkpoints move over BLE/Wi-Fi/LAN/Internet or physical carry.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** service advertisements, placement/handoff intent, version IDs, short state summaries, leases and acknowledgements;
- **BLE:** nearby bootstrap and small state transfer;
- **Wi-Fi/LAN:** service image, container, model, static assets and checkpoint transfer;
- **Internet:** optional fast path or authoritative seed/update source;
- **physical transport:** a student carries a preloaded SSD/SD/laptop containing the service and its state.

## What we can test now in software

Build a tiny local HTTP service with a small state object and simulate 4–8 intermittently connected hosts.

Test:

- service placement on one node, then explicit handoff to another;
- exact image/config/state binding;
- handoff interruption after metadata but before state transfer;
- old host and new host both temporarily believing they are active;
- lease/epoch rules that prevent silent split-brain;
- stateless service versus bounded-state service;
- client requests arriving while the service is unavailable;
- restart from the latest verified checkpoint;
- stale checkpoint rejection;
- mobility-aware host selection using synthetic or UC-008 contact traces;
- comparison of `fixed host`, `replicate everywhere`, `content-only prefetch` and `floating service` baselines;
- metrics: service availability, handoff delay, bytes moved, duplicate-active time, lost/queued requests and energy/storage proxy costs.

A useful invariant is:

> service continuity may degrade during a partition, but no node may silently invent or accept a newer service state than the exact verified state it possesses.

## What requires real hardware

- 3–4 LoRa nodes paired with at least two laptops/Raspberry Pis;
- one small local service that can be stopped/restarted safely;
- a real LoRa service/handoff control exchange;
- one real Wi-Fi/LAN state/image handoff;
- deliberate movement of the current or next service host;
- measured handoff duration, service downtime, actual bytes and real contact windows.

Do not infer service availability or energy cost from simulation alone.

## Messina teaching scenario

Prepare three student-carried service hosts representing coarse zones such as `Messina`, `Villafranca/Rometta` and `Spadafora/Venetico`. A small offline classroom search service starts on the school node.

Before the original host leaves a group, PollicinoNet observes a suitable future carrier from privacy-safe UC-008 traces or a simple configured route. LoRa negotiates the handoff and Wi-Fi transfers the exact service state. Later the second node becomes the local host in another disconnected group.

Students can intentionally miss a planned encounter or interrupt the transfer and verify that the service either restarts from a verified older checkpoint or becomes explicitly unavailable rather than fabricating state.

## Privacy / security

- migrate only allow-listed services;
- sign service manifests and verify exact image/config hashes;
- keep user secrets and unrelated host files outside transferable state;
- minimize per-user logs and avoid migrating browsing histories by default;
- use short-lived leases/epochs to make split-brain explicit;
- encrypt private service checkpoints;
- apply resource quotas so an advertised service cannot consume arbitrary CPU/storage;
- do not use this prototype for safety-critical control or emergency command functions.

## Difficulty

**High.** The radio metadata are small, but correctness around state checkpoints, split-brain, leases, service restart and mobility-aware placement is subtle.

## Research signal

Recent edge-computing work continues to study distributed/asynchronous service placement and service migration for mobile users. In 2026, work on energy-aware floating services and cooperative caching explicitly explored services that move among mobile IoT nodes, while distributed asynchronous edge-cloud placement work studied migration without global coordination. PollicinoNet can reproduce the systems question on a much smaller delay-tolerant student network without importing any external performance claims.

References:

- https://doi.org/10.1109/JIOT.2026.3650790
- https://doi.org/10.1109/TMC.2025.3593592
