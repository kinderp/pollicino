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
| [UC-008](uc-008-network-observatory-contact-graph.md) | Privacy-Preserving Network Observatory | learn real contact opportunities and relay value | synthetic contact graph + relay planning | useful early | Medium |
| [UC-009](uc-009-signed-firmware-config-ferry.md) | Signed Firmware and Configuration Ferry | maintain isolated sensors/robots safely | signed manifest + interrupted-update simulator | required before claims | High |
| [UC-010](uc-010-robot-mission-mailbox.md) | Robot Mission Mailbox | asynchronous jobs for intermittently connected robots | idempotent mission queue + simulated outages | useful early | Medium–High |
| [UC-011](uc-011-dnatrace-encounter-capsules.md) | DNATrace Encounter Capsules | pseudonymous offline discovery with later consent | synthetic traces + consent/rendezvous state machine | later | Medium |
| [UC-012](uc-012-opportunistic-backup-restore.md) | Opportunistic Backup and Restore | exact P2P recovery across intermittent nodes | node-loss + content-addressed restore | useful early | Medium–High |
| [UC-013](uc-013-field-report-evidence-capsules.md) | Field Report and Evidence Capsules | bring signed observations back from disconnected field teams | synthetic incident/report simulator | useful early | Medium |
| [UC-014](uc-014-opportunistic-capability-compute-exchange.md) | Opportunistic Capability and Compute Exchange | discover and use compute/storage/connectivity across partitions | capability scheduler + idempotent job manifests | useful early | High |
| [UC-015](uc-015-partition-tolerant-resource-ledger.md) | Partition-Tolerant Resource Ledger | reconcile inventory/requests while disconnected | CRDT/log convergence under partition and reorder | useful early | Medium |
| [UC-016](uc-016-federated-adapter-round-courier.md) | Federated Adapter Round Courier | coordinate AI updates across intermittent clients | synthetic clients + exact adapter manifests | later | High |
| [UC-017](uc-017-offline-map-tile-ferry.md) | Offline Map and Route Tile Ferry | keep useful map subsets available without Internet | versioned tile cache + area-of-interest reconciliation | useful early | Medium |

## Current top 3 next experiments for the Messina student network

### 1. UC-008 — Privacy-Preserving Network Observatory

This should still come first because it produces the **real contact traces** needed to make every later simulation less hypothetical. Controlled routes with 3+ boards can reveal contact windows, useful relays and queue opportunities without requiring continuous coverage. The privacy rule is strict: measure encounters, not student lives.

### 2. UC-015 — Partition-Tolerant Resource Ledger

This is an unusually good match for a real teaching mesh because the payloads are tiny but the distributed-systems problem is real. Two disconnected groups can independently update a synthetic school/emergency inventory, a student relay can carry the missing operations, and all nodes must eventually converge to the same auditable state. It exercises duplicate suppression, ordering, store-and-forward, signatures and reconciliation without needing bulk transfer over LoRa.

### 3. UC-017 — Offline Map and Route Tile Ferry

This makes content-addressed distribution visible and concrete. Nodes can cache different prepared map areas for the Messina hinterland, use LoRa only to advertise a coarse area/version need, and hand over exact missing tiles through Wi-Fi/BLE or physical carry. The first field test can remain completely non-operational: open map data, synthetic route overlays and measured bearer handover only.

### Strong follow-ups

- **UC-014 — Opportunistic Capability and Compute Exchange:** strategically important because it turns nodes into discoverable compute/storage/service providers, not only content holders.
- **UC-012 — Opportunistic Backup and Restore:** important for the P2P/content-addressed track; once UC-008 contact traces exist, replica placement can be tested against real mobility.
- **UC-010 — Robot Mission Mailbox:** still one of the strongest visible classroom demonstrations of queued, delay-tolerant control that explicitly excludes safety-critical functions.
- **UC-016 — Federated Adapter Round Courier:** a high-value AI research direction after the network simulator and artifact model are stable.

## Immediate software-only test plan

The following can be implemented without any radio hardware:

1. create a deterministic contact/mobility simulator with nodes, time windows and link availability;
2. model per-node `PollicinoStore` inventories and exact content-addressed chunks;
3. add store-and-forward queues with TTL, hop limit, priority and duplicate suppression;
4. simulate LoRa as a scarce control bearer and Wi-Fi/Internet/physical carry as richer bearers;
5. produce privacy-safe synthetic contact graphs for UC-008 and feed them into UC-001/UC-003/UC-013;
6. implement signed/idempotent state machines for UC-009, UC-010 and UC-013;
7. implement synthetic DNATrace rendezvous/consent for UC-011;
8. inject node loss and perform exact content-addressed restore for UC-012;
9. build a capability-aware job scheduler for UC-014 with exact input/output manifests, stale advertisements and retry without duplicate execution;
10. build the UC-015 synthetic resource ledger and property-test convergence under partition, reordering and duplication;
11. run UC-016 with a tiny public/synthetic model and dataset, treating LoRa only as coordination/discovery unless measurements justify more;
12. package a small open map area into deterministic content-addressed tiles for UC-017, create a second version and prove that only missing/changed tiles move;
13. record TRC, delivery delay, cache hit ratio, duplicate overhead, age-of-information, completed-object rate, convergence delay, stale-work rate and exact hash verification as applicable.

This reuses the current architecture instead of creating a special PHY or a separate networking stack per scenario.

## Physical experiments that become necessary

After the simulator contracts are stable:

- repeatable 2-node and 3+ node relay measurements;
- controlled walking/bicycle data-mule passes;
- privacy-safe contact-window collection for UC-008;
- sensor-node backlog collection;
- real LoRa discovery followed by BLE/Wi-Fi/LAN handover;
- one synthetic field-report relay chain with exact evidence retrieval;
- one safe rover mission-mailbox demo, explicitly excluding safety-critical control;
- 3+ storage nodes with a deliberate node-loss/restore test;
- a UC-015 split-network experiment where two groups update a synthetic ledger and a moving relay causes measured convergence;
- a UC-014 three-node capability/job experiment with an allow-listed task and one real rich-link artifact handover;
- a UC-017 three-node map-cache experiment with LoRa area/version discovery and measured Wi-Fi/BLE tile retrieval;
- firmware/configuration experiments only on spare non-critical hardware with rollback tests;
- federated-adapter experiments only after the software protocol is stable, with public/synthetic data first;
- only later, vehicle/UAV tests with the relevant safety/legal controls.

Measured packet loss, RSSI/SNR, airtime, latency, contact duration, energy where relevant and reconstruction/convergence success must be recorded explicitly. Simulator outcomes must not be promoted to field claims.

## Related prior art worth watching

The use cases are consistent with existing research directions without copying their assumptions into the PollicinoNet core:

- delay-tolerant/opportunistic networking and public-transport data mules;
- multi-hop LoRa relay-placement research, useful as a reminder that relay position strongly affects delay, throughput and coverage;
- incremental firmware-update work over LoRa/LoRaWAN, including compact binary deltas and bounded-update architectures;
- blackout/disaster-resilient hybrid mesh work combining scarce and richer local bearers;
- offline replication and CRDT-based emergency-management work under mobile/weak connectivity;
- mobile-edge task offloading research that considers compute placement, cache state, bandwidth and device constraints together;
- bandwidth-aware federated/LoRA adapter exchange for heterogeneous edge devices;
- self-hosted/offline map stacks used where field connectivity cannot be assumed;
- UAV-assisted LoRa collection, where scheduling, geometry and antenna effects must be measured rather than assumed.

These are design references, not evidence that PollicinoNet has achieved the same physical results.
