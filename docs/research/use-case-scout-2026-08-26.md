# PollicinoNet use-case scouting — 2026-08-26

Status: research checkpoint

## Repository state checked

Before adding new cases, the existing branch was reviewed for the current use-case gate, DNA school/data-mule case, reference/content mule, DTN routing baselines, FreakWAN/LoRaMesher research, scenario-family framework and experimental evaluation methodology.

The existing cases remain:

- `UC-DNA-001` — school hub / student data mule for topic-scoped DNA information;
- `UC-CONTENT-001` — authorized reference/manifest/content data mule.

The new cases below were selected only when they introduce a materially different workload or success criterion.

## New use cases added

### UC-EMERG-001 — Resilient community bulletin

Moves small, time-sensitive, provenance-aware notices across temporarily disconnected clusters. Introduces a real need for **application usefulness deadlines** distinct from bundle TTL and for stronger authenticity/replay controls.

Difficulty: medium-high.

### UC-IOT-001 — Community sensor ferry

Students or other mobile nodes collect buffered observations from sparse fixed sensors and deliver them later. The important metric becomes freshness/age-of-information as well as bytes, and batching/aggregation become first-class.

Difficulty: medium.

### UC-MOBILITY-001 — Scheduled vehicle / commuter relay

A repeated route becomes a predictable store-carry-forward bridge. This gives a concrete reason to compare generic opportunistic routing with a deliberately simple schedule-aware strategy and later trace-driven replay.

Difficulty: medium in software, higher in field deployment.

### UC-BACKUP-001 — Opportunistic safe-copy

Uses trusted relays to evacuate encrypted references/manifests/selected chunks during a gateway outage. The objective is durability and recoverability rather than content distribution.

Difficulty: medium-high.

### UC-RAIATEA-001 — Raiatea offline document sync

Carries rights-aware document identities, manifests and wanted state between Raiatea libraries; rich bearers retrieve the payload later. The integration must remain fixture/contract driven because Raiatea is still in P0 Elaboration.

Difficulty: medium.

### UC-RURAL-001 — Offline community knowledge/service kiosk

Keeps useful public content available locally and asynchronously refreshes the cache via student/vehicle data mules. It is a modern Pollicino-style composition of short scarce contacts, physical carry and rich local synchronization.

Difficulty: medium for public content.

### UC-AI-001 — Edge AI artifact synchronization

Carries model/dataset/adapter identity, compatibility and availability metadata, then resolves large artifacts through LAN/NAS/Internet. Kept as a child of the generic content use case until AI-specific protocol state is proven necessary.

Difficulty: medium in synthetic experiments; high for secure production artifact handling.

### UC-ROBOT-001 — Field robot / drone delayed data exchange

Carries non-safety-critical status/task/reference/manifest data while bulky maps/images/logs move later over Wi-Fi/dock links. Explicitly excludes primary real-time robot control.

Difficulty: high in real deployment.

## Top three new cases

### 1. UC-IOT-001 — Community sensor ferry

Why: easiest to turn into a repeatable student experiment, naturally produces lots of tiny data where Pollicino reconciliation/batching can show measurable value, and has a direct lineage to classic Data MULE research.

Immediate software experiment: generated sensors + finite buffers + student contact schedules + freshness-aware versus raw forwarding.

### 2. UC-MOBILITY-001 — Scheduled vehicle / commuter relay

Why: strongly matches a province-scale network where human/vehicle movement creates connectivity over time. It can use the existing scenario-family framework now and later accept real privacy-safe contact traces without redesigning the object layer.

Immediate software experiment: repeated school/territorial route with jitter/missed contacts, comparing Spray-and-Wait against a minimal schedule-aware baseline.

### 3. UC-EMERG-001 — Resilient community bulletin

Why: high public value and a genuinely different optimization target: delivery-before-deadline and authenticated provenance. It also provides the concrete use case previously missing for application deadline semantics and later RAPID-like utility experiments.

Immediate software experiment: urgent/non-urgent bulletins with usefulness deadlines, priority scheduling and bounded replication.

## Literature/precedent used

- Data MULEs for sparse sensor collection: https://doi.org/10.1016/S1570-8705(03)00003-9
- DakNet asynchronous rural connectivity: https://www.media.mit.edu/publications/daknet-rethinking-connectivity-in-developing-nations/
- DTN routing/data dissemination survey: https://doi.org/10.1016/j.jnca.2016.01.002
- Vehicular DTN survey: https://doi.org/10.1016/j.comcom.2014.03.024
- Deadline-constrained DTN routing in disaster scenarios: https://doi.org/10.1016/j.comcom.2024.108038
- UAV-assisted IoT data collection survey: https://arxiv.org/abs/2211.09555

## What can be done before hardware

All new cases can start as `MODEL_SYNTHETIC` workloads using existing scenario/contact/bundle infrastructure. In particular:

- sensor generation and age-of-information;
- deadline-aware emergency workloads;
- scheduled mobile route traces with jitter;
- finite backup storage and bounded replicas;
- synthetic Raiatea rights-safe manifests;
- rural kiosk cache/wanted-list synchronization;
- AI dependency/version manifests;
- robot/drone mobility and later rich-link handover.

No new PHY is necessary for these experiments.

## Physical evidence required later

HW-006 remains the first gate before any claim about real LoRa range, NLOS behavior, contact capacity, student/vehicle route usefulness or topology superiority.

Additional later campaigns would be use-case-specific:

- IoT: sensor power, real collection time and installation behavior;
- mobility: contact windows while moving, antenna/body effects and route trace;
- emergency: measured urgent-message capacity plus stronger security/operational validation;
- robot/drone: motion/contact behavior, safe integration and independent control-channel constraints;
- rural kiosk: unattended power/enclosure and real visit/contact timing.

The frozen first LoRa campaign remains **42-byte frames / 2 dBm**. No physical result is claimed by this checkpoint.

## Repository changes

Added:

- `pollicinonet-use-case-index.md`;
- `uc-emerg-001-resilient-community-bulletin.md`;
- `uc-iot-001-community-sensor-ferry.md`;
- `uc-mobility-001-scheduled-vehicle-relay.md`;
- `uc-backup-001-opportunistic-safe-copy.md`;
- `uc-raiatea-001-offline-document-manifest-sync.md`;
- `uc-rural-001-offline-service-kiosk.md`;
- `uc-ai-001-edge-ai-artifact-sync.md`;
- `uc-robot-001-field-robot-data-exchange.md`;
- this checkpoint report.

No source code, frozen PHY or hardware configuration was changed.