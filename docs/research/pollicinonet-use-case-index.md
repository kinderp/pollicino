# PollicinoNet use-case index

Status: living index, 2026-08-29

This index is the navigation surface for concrete PollicinoNet use cases. Detailed proposals remain governed by `use-case-justification-gate.md`: appearing here does not imply adoption of a protocol, dependency, routing algorithm, security mechanism or PHY change.

## Current primary / prototype-driving use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-DNA-001` | School hub / student data mule for topic-scoped DNA information | dense morning mixing + sparse territorial dissemination of relevant micro-information | PRIMARY / PROTOTYPE-DRIVING | `pollicinonet-use-cases.md` |
| `UC-CONTENT-001` | Reference and content data mule | carry magnet/URL/CID/manifest/wanted state now, retrieve authorized content later on rich links | PRIMARY / PROTOTYPE-DRIVING | `uc-content-001-reference-and-content-data-mule.md` |
| `UC-CONTENT-002` | Mobile reference search index | discover useful references from encountered peers without pushing lifetime catalogs | PRIMARY / PROTOTYPE-DRIVING | `uc-content-002-mobile-reference-search-index.md` |
| `UC-EMERG-001` | Resilient community bulletin | move compact time-sensitive/provenance-aware notices across disrupted clusters | PRIMARY / PROTOTYPE-DRIVING | `uc-emerg-001-resilient-community-bulletin.md` |
| `UC-IOT-001` | Community sensor ferry | collect many tiny time-series observations from sparse sensors and deliver later | PRIMARY / PROTOTYPE-DRIVING | `uc-iot-001-community-sensor-ferry.md` |
| `UC-MOBILITY-001` | Scheduled vehicle / commuter relay | exploit repeated mobile routes as predictable bridges between disconnected clusters | PRIMARY / PROTOTYPE-DRIVING | `uc-mobility-001-scheduled-vehicle-relay.md` |
| `UC-OPS-001` | Offline fleet management and configuration ferry | converge signed config/version/health state for disconnected Pollicino nodes | PRIMARY / PROTOTYPE-DRIVING | `uc-ops-001-offline-fleet-management.md` |
| `UC-EDU-001` | Offline classroom resource and assignment relay | distribute learning-resource metadata and return private receipts across intermittent student contacts | PRIMARY / PROTOTYPE-DRIVING | `uc-edu-001-classroom-resource-relay.md` |
| `UC-TRACE-001` | Privacy-preserving encounter observatory | collect bounded contact summaries and replay the real temporal graph without turning the network into student tracking | PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE | `uc-trace-001-privacy-preserving-encounter-observatory.md` |
| `UC-CITSCI-001` | Student field-observation / citizen-science ferry | move compact human observations now and resolve rich evidence later | PRIMARY / PROTOTYPE-DRIVING | `uc-citsci-001-student-field-observation-ferry.md` |
| `UC-TASK-001` | Offline task and volunteer coordination board | reconcile claims/completions/leases/deadlines for work items created under partitions | PRIMARY / PROTOTYPE-DRIVING, emergency-adjacent | `uc-task-001-offline-task-coordination-board.md` |
| `UC-EGRESS-001` | Opportunistic Internet request/reply ferry | carry an idempotent request to a trusted rich-link egress and return the asynchronous reply | PRIMARY / PROTOTYPE-DRIVING MULTI-BEARER | `uc-egress-001-opportunistic-internet-request-reply-ferry.md` |

## Integration / territorial / educational use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-BACKUP-001` | Opportunistic safe-copy | preserve important exact data during gateway outages through bounded trusted replication | PROTOTYPE | `uc-backup-001-opportunistic-safe-copy.md` |
| `UC-RAIATEA-001` | Raiatea offline document sync | carry rights-aware document identity/manifest/wanted state, retrieve authorized payload later | PROTOTYPE / integration | `uc-raiatea-001-offline-document-manifest-sync.md` |
| `UC-RURAL-001` | Offline community knowledge/service kiosk | keep a useful local cache offline and asynchronously refresh it via mobile relays | PROTOTYPE | `uc-rural-001-offline-service-kiosk.md` |
| `UC-MAP-001` | Offline geospatial and local-hazard delta exchange | move only relevant changed map/layer references instead of full geospatial datasets | PROTOTYPE / emergency-adjacent | `uc-map-001-offline-geospatial-delta-exchange.md` |
| `UC-ASSET-001` | Offline physical-asset catalog and reservation ferry | reconcile availability and bounded reservation leases for physical school/lab/library resources | PROTOTYPE / educational integration | `uc-asset-001-offline-physical-asset-catalog.md` |
| `UC-TRANSIT-001` | Offline public-transport timetable/service delta ferry | propagate authoritative route/status deltas with usefulness deadlines and later rich-feed resolution | PROTOTYPE / territorial research | `uc-transit-001-offline-public-transport-delta-ferry.md` |
| `UC-MSG-001` | Private delay-tolerant mailbox | destination-specific encrypted micro-messages plus delayed receipts across non-contemporaneous contacts | PROTOTYPE / privacy-sensitive | `uc-msg-001-private-delay-tolerant-mailbox.md` |
| `UC-EVIDENCE-001` | Integrity-first field evidence manifest ferry | bind later rich-media retrieval to compact hash/provenance/custody state | RESEARCH / PROTOTYPE, emergency-adjacent | `uc-evidence-001-integrity-first-field-evidence-ferry.md` |
| `UC-GAME-001` | Opportunistic relay challenge | generate safe, controlled store-carry-forward traffic for teaching and supervised field validation | PROTOTYPE / educational test harness | `uc-game-001-opportunistic-relay-challenge.md` |

## Domain-specific / security / future research use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-AI-001` | Edge AI artifact sync | reconcile model/adapter/dataset versions and defer large artifact retrieval to rich links | RESEARCH + PROTOTYPE, child of CONTENT | `uc-ai-001-edge-ai-artifact-sync.md` |
| `UC-FL-001` | Delay-tolerant federated evaluation / learning rendezvous | handle staleness/provenance/fairness of asynchronous computed model contributions | RESEARCH / SOFTWARE PROTOTYPE | `uc-fl-001-delay-tolerant-federated-learning-rendezvous.md` |
| `UC-ROBOT-001` | Field robot / drone delayed data exchange | move supervisory/status/reference data during intermittent field contacts; bulk data later | RESEARCH | `uc-robot-001-field-robot-data-exchange.md` |
| `UC-TRUST-001` | Offline trust, key-rotation and revocation ferry | distribute compact signed trust generations when online status services are unavailable | RESEARCH / SECURITY INFRASTRUCTURE | `uc-trust-001-offline-trust-revocation-ferry.md` |
| `UC-COMPUTE-001` | Delay-tolerant edge job and result ferry | carry asynchronous jobs toward compute-rich nodes and return result references | RESEARCH / PROTOTYPE | `uc-compute-001-delay-tolerant-job-result-ferry.md` |
| `UC-TIME-001` | Signed time-anchor and clock-drift ferry | maintain bounded time/freshness uncertainty across disconnected nodes without assuming permanent NTP/GNSS | RESEARCH / INFRASTRUCTURE PROTOTYPE | `uc-time-001-signed-time-anchor-ferry.md` |

## Practical priority for the Messina student network

The most immediately actionable workloads are not necessarily the most ambitious ones. Town names are scenario labels, never assumed RF links.

### Tier A — first real-network candidates after HW-006

1. `UC-TRACE-001`: after privacy governance/consent, collect bounded encounter evidence so routing/topology claims can use measured temporal graphs.
2. `UC-GAME-001`: synthetic signed tokens create a safe first student workload with known expected outcomes and no need for GPS or private content.
3. `UC-OPS-001`: manage harmless signed version/config fixtures for the distributed boards themselves.
4. `UC-IOT-001`: fixed sensors + student data mules create repeatable tiny-data traffic.
5. `UC-EDU-001`: public/open classroom resource descriptors make the network visibly useful to students.
6. `UC-CITSCI-001`: field observations create a real educational project while rich media stays on Wi-Fi.
7. `UC-TASK-001`: harmless lab task cards introduce real conflict/deadline semantics; emergency drills come only later.
8. `UC-EGRESS-001`: fake/allowlisted services exercise `DTN -> RICH_HOME -> DTN` request/reply behavior.
9. `UC-CONTENT-002`: reference discovery/reconciliation is naturally matched to scarce contacts and later home resolution.
10. `UC-ASSET-001`: synthetic/public physical-asset catalogs provide a safe eventual-consistency workload.
11. `UC-MOBILITY-001`: repeated routes become testable after privacy-safe contact logging exists.

### Tier B — software-first, stronger governance before field use

- `UC-EMERG-001`, `UC-MAP-001` and `UC-EVIDENCE-001`: high public value but non-operational until authenticity, authoritative sources, security and field evidence are independently validated.
- `UC-TRANSIT-001`: strong territorial relevance, but operator/vehicle experiments need separate governance.
- `UC-MSG-001`: use bot/test endpoints first; human messaging requires E2E key lifecycle, metadata minimization and school/privacy governance.
- `UC-TIME-001`: potentially foundational; physical oscillator/drift measurements are needed before real bounds.
- `UC-TRUST-001`: security-critical and unsuitable for casual production rollout.
- `UC-BACKUP-001`: useful with encrypted fixtures and bounded trusted replicas.

### Tier C — integration/research expansion

- Raiatea, rural kiosk, AI artifacts, `UC-FL-001`, robots/drones and delay-tolerant compute jobs.

## Cross-use-case architecture pressure

The catalog now contains many materially different workloads whose object state may need to survive:

```text
CONNECTED_MESH / school-local contacts
          |
          v
OPPORTUNISTIC_DTN / physical carry
          |
          v
RICH_HOME / Wi-Fi or LAN
          |
          v
INTERNET / remote service or gateway
```

New examples strengthen different parts of that path:

- MSG: private destination + asynchronous receipt;
- TASK: conflict/lease/deadline state;
- EGRESS: request identity and idempotency across a rich-link service boundary;
- FL: model generation/staleness of computed contributions;
- EVIDENCE: integrity/provenance before rich payload retrieval;
- GAME: controlled educational workload spanning mesh and carry phases.

This is evidence for continuing to **study** a shared bearer/runtime boundary. It is not permission to add a new protocol or abstraction unless the existing architecture gate and measured simplification criteria are met.

## Workloads that should remain distinct

Avoid collapsing everything into one generic “message” benchmark:

- **DNA/topic:** semantic relevance and subscriptions;
- **emergency bulletin:** usefulness deadline + authenticity/provenance;
- **sensor ferry:** freshness / many-to-one time series;
- **citizen science:** human provenance, review state, geoprivacy and deferred rich evidence;
- **content/reference index:** discovery, wanted state, catalog reconciliation and later rich retrieval;
- **fleet management:** configuration convergence, acknowledgement and rollback;
- **encounter observatory:** privacy-filtered temporal-graph recovery and replay fidelity;
- **education:** delivery-before-class/deadline plus privacy-preserving return receipts;
- **physical assets:** eventual inventory convergence, reservation leases and conflict handling;
- **public transport:** authoritative route/status generations and useful-before-departure deadlines;
- **private mailbox:** destination confidentiality, metadata minimization and delayed receipts;
- **task board:** claim/completion conflict, lease and deadline semantics;
- **Internet egress:** idempotent request/reply correlation and gateway authorization;
- **field evidence:** content integrity, provenance and custody gaps;
- **game/test harness:** known challenge completion plus safe student interaction;
- **federated learning:** model-update staleness, convergence and participation fairness;
- **time:** uncertainty growth, signed anchors and anti-rollback;
- **trust:** rollback-resistant security-state convergence;
- **geospatial:** geographic relevance, version/delta semantics and location privacy;
- **backup:** durability and bounded replication;
- **scheduled mobility:** contact predictability and route robustness;
- **compute:** job deadline/capability, idempotency and result return;
- **robot/drone:** delayed supervisory state with a strict safety boundary.

They may share transport primitives while keeping different success metrics.

## Messina educational network pattern

Use pseudonymous logical clusters rather than student addresses. Public town names such as Rometta, Spadafora, Saponara, Villafranca and other province areas may label scenarios, but no synthetic result is measured coverage.

```text
territorial cluster A -- student/vehicle mule --+
territorial cluster B -- student/vehicle mule --+--> school mixing hub
territorial cluster C -- student/vehicle mule --+       |
                                                        +--> Wi-Fi/Internet gateway
```

The morning school phase can exercise connected-mesh behavior; afternoon/evening phases exercise store-carry-forward; home/school rich links can resolve payloads or execute allowlisted egress requests. Exact object/bundle identity must survive the lifecycle transition.

## Software-first rule

All use cases can begin as `MODEL_SYNTHETIC` experiments. Useful immediate dimensions now include:

- topology/contact schedule and future TRACE replay;
- logical byte budget independent from physical duration;
- priorities, TTL and explicit application deadline;
- finite storage/gateway intermittency/multiple bearers;
- canonical DTN baselines and current stateful research strategies;
- version/generation convergence and signed fixtures;
- privacy-filtered encounter aggregation;
- simulated clock offset/drift and uncertainty;
- leases/conflict/task state transitions;
- idempotent request/reply plus asymmetric return paths;
- synthetic encrypted mailbox payloads and receipts;
- integrity hashes, staged corruption and custody receipts;
- tiny-model FL staleness/convergence experiments;
- game-token anti-replay and controlled application completion.

A model result remains a model result even if the topology uses real town names.

## Physical evidence boundary

No use case in this index changes the frozen LoRa PHY or authorizes real coverage/capacity claims.

HW-006 remains required before claims about:

- real LoRa contact availability;
- distance/NLOS behavior;
- useful bytes per encounter;
- real student/vehicle route capacity;
- real topology/routing superiority;
- physical energy/battery performance;
- real encounter/inter-contact distributions;
- real oscillator/RTC drift bounds.

The frozen first campaign remains **42-byte frames / 2 dBm**, following the existing same-room -> separation -> wall -> multi-wall/floor -> outdoor evidence sequence.

Use-case-specific hardware/security gates may add requirements after HW-006; they do not weaken it.
