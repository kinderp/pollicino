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

## Current top 3 next experiments for the Messina student network

### 1. UC-008 — Privacy-Preserving Network Observatory

This should come first because it produces the **real contact traces** needed to make every later simulation less hypothetical. Controlled routes with 3+ boards can reveal contact windows, useful relays and queue opportunities without requiring continuous coverage. The privacy rule is strict: measure encounters, not student lives.

### 2. UC-013 — Field Report and Evidence Capsules

A very concrete store-and-forward exercise with small LoRa payloads: one team creates a signed synthetic observation, other students relay it, and the command node later resolves an exact evidence object over Wi-Fi/BLE. It combines emergency-drill logic, provenance and richer-link handover without pretending to be an operational civil-protection system.

### 3. UC-010 — Robot Mission Mailbox

A strong classroom demo because the result is visible: a rover receives an idempotent queued mission across an intermittent path, executes it locally and returns status before uploading richer logs later. It tests TTL, acknowledgements, duplicate suppression and authorization. Safety functions such as emergency stop must remain local and independent of PollicinoNet.

### Strong follow-up: UC-012 — Opportunistic Backup and Restore

This is strategically important for the P2P/content-addressed track. It becomes especially valuable once the contact graph from UC-008 is available: we can test which replicas should move where, then deliberately remove a node and prove an exact restore from surviving peers.

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
9. record TRC, delivery delay, cache hit ratio, duplicate overhead, age-of-information, completed-object rate and exact hash verification.

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
- firmware/configuration experiments only on spare non-critical hardware with rollback tests;
- only later, vehicle/UAV tests with the relevant safety/legal controls.

Measured packet loss, RSSI/SNR, airtime, latency, contact duration, energy where relevant and reconstruction success must be recorded explicitly. Simulator outcomes must not be promoted to field claims.

## Related prior art worth watching

The use cases are consistent with existing research directions without copying their assumptions into the PollicinoNet core:

- delay-tolerant/opportunistic networking and public-transport data mules, including recent 2025 work modeling buses/minibuses as DTN carriers;
- multi-hop LoRa relay-placement research, useful as a reminder that relay position strongly affects delay, throughput and coverage;
- incremental firmware-update work over LoRa/LoRaWAN, including compact binary deltas and bounded-update architectures published in 2025–2026;
- blackout/disaster-resilient hybrid mesh work combining LoRa with richer local bearers;
- bandwidth-aware federated/LoRA adapter exchange for heterogeneous edge devices;
- UAV-assisted LoRa collection, where scheduling, geometry and antenna effects must be measured rather than assumed.

These are design references, not evidence that PollicinoNet has achieved the same physical results.
