# PollicinoNet use-case catalog

This catalog turns PollicinoNet research primitives into concrete scenarios that can be simulated first and validated later on real nodes.

Core rules for every use case:

- do not modify the frozen LoRa PHY as part of use-case work;
- `DISCOVERY`, `EXACT` and `SEMANTIC` remain information contracts, not radio technologies;
- prefer LoRa for compact discovery/control and a richer bearer for bulk bytes whenever one is available;
- do not claim physical range, reliability, airtime or energy results without real measurements;
- safety-critical/emergency scenarios remain experiments until independently validated;
- protect identity, location, content metadata and authorization at the application layer.

## Catalog

| ID | Use case | Main problem | Best first experiment | HW need | Difficulty |
|---|---|---|---|---|---|
| [UC-001](uc-001-student-knowledge-ferry.md) | Student Knowledge Ferry | disconnected school/home/town islands | synthetic student mobility + store-and-forward | later | Medium |
| [UC-002](uc-002-signed-community-bulletin.md) | Signed Community Bulletin / civil-protection drill | resilient small authoritative messages | signatures + expiry + network partitions | later | Medium |
| [UC-003](uc-003-rural-sensor-courier.md) | Rural Sensor Courier | collect data without permanent backhaul | synthetic sensor backlog + moving relay | useful early | Low–Medium |
| [UC-004](uc-004-offline-ai-artifact-distribution.md) | Offline AI Artifact Distribution | models/datasets across intermittent links | chunk inventory + cache reconciliation | later | Medium–High |
| [UC-005](uc-005-mobile-gateway-uav-vehicle.md) | Mobile Gateway / UAV / vehicle | fixed nodes without end-to-end paths | contact-window and queue simulator | required for claims | High |
| [UC-006](uc-006-raiatea-document-capsules.md) | Raiatea Document Capsules | exact document/version distribution | versioned corpus + missing-chunk retrieval | optional first | Medium |
| [UC-007](uc-007-edge-ai-event-scout.md) | Edge AI Event Scout | send interesting events, not raw streams | semantic event + exact evidence simulator | later | High |

## Most promising for the Messina student network

### 1. UC-001 — Student Knowledge Ferry

Best match for a real distributed class network. It makes normal student mobility useful without requiring permanent coverage and exercises exactly the PollicinoNet ideas that are hardest to learn from a static two-board link: delay tolerance, store-and-forward, cache hits, handover and content addressing.

### 2. UC-003 — Rural Sensor Courier

The cleanest path from simulator to real hardware. Sensor payloads are small, measurable and easy to generate synthetically first. A field node plus a walking/bicycle collector gives a concrete experiment without requiring a full mesh or an Internet gateway.

### 3. UC-004 — Offline AI Artifact Distribution

Strategically strong because it joins PollicinoNet P2P/content-addressing with the AI track. LoRa does not carry giant models; it carries just enough information to find the right version and missing chunks, while Wi-Fi/Internet/physical carry does the bulk work.

## Immediate software-only test plan

The following can be implemented without any radio hardware:

1. create a deterministic contact/mobility simulator with nodes, time windows and link availability;
2. model per-node `PollicinoStore` inventories and exact content-addressed chunks;
3. add store-and-forward queues with TTL, hop limit, priority and duplicate suppression;
4. simulate LoRa as a scarce control bearer and Wi-Fi/Internet/physical carry as richer bearers;
5. run UC-001, UC-003 and UC-004 over the same simulator;
6. record TRC, delivery delay, cache hit ratio, duplicate overhead, completed-object rate and exact hash verification.

This reuses the current architecture instead of creating a special PHY or a separate networking stack per scenario.

## Physical experiments that become necessary

After the simulator contracts are stable:

- repeatable 2-node and 3+ node relay measurements;
- walking/bicycle data-mule passes;
- sensor-node backlog collection;
- real LoRa discovery followed by BLE/Wi-Fi/LAN handover;
- only later, vehicle/UAV tests with the relevant safety/legal controls.

Measured packet loss, RSSI/SNR, airtime, latency and reconstruction success must be recorded explicitly. Simulator outcomes must not be promoted to field claims.

## Related prior art worth watching

The use cases are consistent with several existing research directions without copying their assumptions into the PollicinoNet core:

- delay-tolerant/opportunistic content retrieval and mobile data mules;
- UAV-assisted LoRa collection, where recent field research shows scheduling and antenna directivity matter;
- bandwidth/energy-aware edge-AI model updates over LPWAN;
- federated/adapter-based AI updates that reduce the amount of model state exchanged.

These are design references, not evidence that PollicinoNet has achieved the same physical results.
