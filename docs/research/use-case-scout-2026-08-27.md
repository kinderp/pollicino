# PollicinoNet use-case scouting — 2026-08-27

Status: research checkpoint

## Repository state checked

The branch was reviewed before adding new cases. Existing use cases already cover:

- DNA school/data-mule dissemination;
- reference/content mule and mobile reference search;
- emergency community bulletins;
- IoT sensor ferry;
- scheduled vehicle/commuter relays;
- opportunistic backup;
- Raiatea document manifests;
- rural offline kiosks;
- AI artifact synchronization;
- robot/drone delayed exchange.

The second scouting round therefore avoids adding another generic “data mule” or “content distribution” case. New entries below introduce a distinct success criterion or operational requirement.

## New use cases added

### UC-OPS-001 — Offline fleet management and configuration ferry

The PollicinoNet fleet uses its own DTN to converge signed configuration generations, version/update references, health summaries and acknowledgements while nodes are away from Internet access.

Why it matters: a province-scale student network is not maintainable if every node requires continuous cloud connectivity. This is a direct operational use case for the network itself.

Difficulty: medium in simulation; medium-high for safe firmware/configuration deployment.

### UC-EDU-001 — Offline classroom resource and assignment relay

Signed assignment/resource descriptors travel through student relays; rich payloads are fetched later on Wi-Fi/NAS/Internet. Private return receipts/submission references remain encrypted end-to-end.

Why it matters: it is an understandable, consent-based application for the student network and gives a concrete delivery-before-class/deadline metric.

Difficulty: low-medium for public resources; medium-high when personal educational data is introduced.

### UC-TRUST-001 — Offline trust, key-rotation and revocation ferry

Compact signed trust generations propagate through disconnected clusters so nodes can learn revocations/key rotations without requiring a continuously reachable status service.

Why it matters: a mature DTN cannot assume security state is always fresh. The payload is tiny, but correctness and rollback resistance are critical.

Difficulty: high; synthetic disposable keys only for the first prototype.

### UC-MAP-001 — Offline geospatial and local-hazard delta exchange

Nodes exchange only changed map/layer references relevant to a coarse area, then fetch full geospatial payloads over richer bearers. This remains non-operational and emergency-adjacent, not a certified warning/navigation system.

Why it matters: it combines reference reconciliation, geographic relevance, provenance and rich-link handover in a workload with strong territorial relevance.

Difficulty: medium for synthetic/public data; higher for authoritative operational integration.

### UC-COMPUTE-001 — Delay-tolerant edge job and result ferry

Compact authenticated jobs move toward compute-rich school/home/edge nodes; result references return later. Large input/model/result data stays on Wi-Fi/LAN/Internet when possible.

Why it matters: it extends Pollicino from moving information/artifacts to moving asynchronous units of work, without pretending LoRa is an interactive remote-compute link.

Difficulty: high due to authorization, idempotency, quotas and sandboxing.

## Top three from this round

### 1. UC-OPS-001

Most practical. If boards are physically distributed among students, configuration/version/health convergence becomes a real operational requirement immediately. It can first be tested with harmless signed version fixtures and no firmware flashing.

Immediate software experiment: 20–100 nodes with mixed configuration generations; compare full push, generation/hash advertisement, manifest/pull and rich-link package resolution.

### 2. UC-EDU-001

Best demonstrator. The network can carry metadata for an actual classroom exercise while keeping large resources and personal data off LoRa. It produces easy-to-understand metrics: who learned about the resource before the educational deadline, how many relay hops were needed and how many scarce-link bytes were spent.

Immediate software experiment: dense morning school mixing + absent students + sparse afternoon clusters + next-day return receipts.

### 3. UC-TRUST-001

Most strategically important infrastructure case. It forces the project to think about stale credentials, revocation, anti-rollback and security-state convergence before a real network grows large.

Immediate software experiment: synthetic revocation generation `T12`, partitions and missed contacts; verify that nodes never accept replayed `T11` after `T12` is verified.

`UC-MAP-001` is close behind because it has strong territorial/protection-civil relevance, but authoritative source integration and location privacy make it less suitable than OPS/EDU for the first student field pilot.

## Literature / standards context used

- RFC 9675 — Delay-Tolerant Networking Management Architecture: https://www.rfc-editor.org/rfc/rfc9675.html
- RFC 4838 — Delay-Tolerant Networking Architecture, including asynchronous application structuring and security/revocation constraints: https://www.rfc-editor.org/rfc/rfc4838.html
- Bhutta, Cruickshank, Sun — PKI validation and revocation suitable for DTNs: https://doi.org/10.1049/iet-ifs.2015.0438
- Abdeljabar, Alouini — DTN approach for equitable digital learning in rural areas (2025): https://arxiv.org/abs/2511.20334
- Trono et al. — DTN MapEx, disaster mapping over DTN: https://doi.org/10.1007/978-3-319-11569-6_5
- Geo-DMP — DTN-based mobile geospatial data retrieval: https://doi.org/10.3390/ijgi9010008
- ITU Disaster Connectivity Map / connectivity maps: https://www.itu.int/en/ITU-D/Emergency-Telecommunications/Pages/Disaster-Connectivity-Map.aspx

These references motivate workload classes. They do not provide physical evidence for PollicinoNet or the province of Messina.

## What can be tested before hardware

No PHY change is required. The existing synthetic scenario/contact framework can already model:

- configuration/version generation convergence and acknowledgements;
- classroom resource delivery deadlines and return receipts;
- signed trust-generation propagation and anti-rollback;
- map-region interest filtering plus version/delta reconciliation;
- compute job queues, capability matching, deadlines and idempotency.

All experiments should use paired seeds and the existing `MODEL_SYNTHETIC` evidence class.

## Physical evidence required later

HW-006 remains the first physical gate. Only measured campaigns may establish real contact availability, distance/NLOS behavior, useful bytes per encounter or battery cost.

Use-case-specific later evidence:

- OPS: real signed-metadata exchange, restart persistence, safe rollback/upgrade workflow;
- EDU: practical device handling and privacy-safe school/home contact logging;
- TRUST: cryptographic verification cost, secure key storage and recovery across missed generations;
- MAP: measured delta/reference capacity and safe local-client handover; authoritative integration requires separate domain review;
- COMPUTE: queue/restart behavior and actual worker energy/execution cost.

The frozen first LoRa campaign remains **42-byte frames / 2 dBm**, same-room → separation → wall → multi-wall/floor → outdoor.

## Repository changes

Added:

- `uc-ops-001-offline-fleet-management.md`;
- `uc-edu-001-classroom-resource-relay.md`;
- `uc-trust-001-offline-trust-revocation-ferry.md`;
- `uc-map-001-offline-geospatial-delta-exchange.md`;
- `uc-compute-001-delay-tolerant-job-result-ferry.md`;
- this checkpoint.

Updated:

- `pollicinonet-use-case-index.md` — now includes `UC-CONTENT-002`, the five new use cases and a practical priority tier for the Messina student network.

No source code, LoRa PHY value or hardware configuration was changed.
