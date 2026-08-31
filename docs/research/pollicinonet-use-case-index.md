# PollicinoNet use-case index

Status: living index, 2026-08-31 — 38 distinct use-case families

This index is the navigation surface for concrete PollicinoNet use cases. Detailed proposals remain governed by `use-case-justification-gate.md`: appearing here does not imply adoption of a protocol, dependency, routing algorithm, security mechanism or PHY change.

Cross-application abstractions are also governed by `substrate-generality-gate.md`: application semantics remain outside Pollicino core unless genuine reusable behavior is established.

## Current primary / prototype-driving use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-DNA-001` | School hub / student data mule for topic-scoped DNA information | dense morning mixing + sparse territorial dissemination of relevant micro-information | PRIMARY / PROTOTYPE-DRIVING | `pollicinonet-use-cases.md` |
| `UC-CONTENT-001` | Reference and content data mule | carry magnet/URL/CID/manifest/wanted state now, retrieve authorized content later on rich links | PRIMARY / PROTOTYPE-DRIVING | `uc-content-001-reference-and-content-data-mule.md` |
| `UC-CONTENT-002` | Mobile reference search index | discover useful references from encountered peers without pushing lifetime catalogs | PRIMARY / PROTOTYPE-DRIVING | `uc-content-002-mobile-reference-search-index.md` |
| `UC-FARO-001` | Distributed scientific knowledge package exchange | preserve/find/replicate exact signed FAROPackage bytes without moving scientific trust/evidence semantics into Pollicino | PRIMARY / CROSS-PROJECT CONFORMANCE / SOFTWARE-FIRST | `uc-faro-001-distributed-scientific-knowledge-package-exchange.md` |
| `UC-EMERG-001` | Resilient community bulletin | move compact time-sensitive/provenance-aware notices across disrupted clusters | PRIMARY / PROTOTYPE-DRIVING | `uc-emerg-001-resilient-community-bulletin.md` |
| `UC-IOT-001` | Community sensor ferry | collect many tiny time-series observations from sparse sensors and deliver later | PRIMARY / PROTOTYPE-DRIVING | `uc-iot-001-community-sensor-ferry.md` |
| `UC-MOBILITY-001` | Scheduled vehicle / commuter relay | exploit repeated mobile routes as predictable bridges between disconnected clusters | PRIMARY / PROTOTYPE-DRIVING | `uc-mobility-001-scheduled-vehicle-relay.md` |
| `UC-OPS-001` | Offline fleet management and configuration ferry | converge signed config/version/health state for disconnected Pollicino nodes | PRIMARY / PROTOTYPE-DRIVING | `uc-ops-001-offline-fleet-management.md` |
| `UC-EDU-001` | Offline classroom resource and assignment relay | distribute learning-resource metadata and return private receipts across intermittent student contacts | PRIMARY / PROTOTYPE-DRIVING | `uc-edu-001-classroom-resource-relay.md` |
| `UC-TRACE-001` | Privacy-preserving encounter observatory | collect bounded contact summaries and replay the real temporal graph without turning the network into student tracking | PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE | `uc-trace-001-privacy-preserving-encounter-observatory.md` |
| `UC-CITSCI-001` | Student field-observation / citizen-science ferry | move compact human observations now and resolve rich evidence later | PRIMARY / PROTOTYPE-DRIVING | `uc-citsci-001-student-field-observation-ferry.md` |
| `UC-TASK-001` | Offline task and volunteer coordination board | reconcile claims/completions/leases/deadlines for work items created under partitions | PRIMARY / PROTOTYPE-DRIVING, emergency-adjacent | `uc-task-001-offline-task-coordination-board.md` |
| `UC-EGRESS-001` | Opportunistic Internet request/reply ferry | carry an idempotent request to a trusted rich-link egress and return the asynchronous reply | PRIMARY / PROTOTYPE-DRIVING MULTI-BEARER | `uc-egress-001-opportunistic-internet-request-reply-ferry.md` |
| `UC-PREFETCH-001` | Mobility-aware cache prepositioning | decide which bounded objects/references to seed on which carriers before the school graph fragments | PRIMARY / PROTOTYPE-DRIVING SCHEDULING | `uc-prefetch-001-mobility-aware-cache-prepositioning.md` |
| `UC-SERVICE-001` | Offline service / capability directory | discover which intermittent node can eventually provide egress, compute, resolver or sensor service | PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE | `uc-service-001-offline-service-capability-directory.md` |
| `UC-QUERY-001` | Delay-tolerant federated metadata query | carry an active search request to disconnected indexes and return compact result references asynchronously | PRIMARY / PROTOTYPE-DRIVING INTEGRATION | `uc-query-001-delay-tolerant-federated-metadata-query.md` |
| `UC-CODEBOOK-001` | Shared compression side-information ferry | pre-position exact shared dictionaries/models so later scarce-link objects can be represented with fewer total bits | PRIMARY / PROTOTYPE-DRIVING RESEARCH | `uc-codebook-001-shared-compression-side-information-ferry.md` |

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
| `UC-COURIER-001` | Physical object custody and handoff | reconcile delayed handoff/return receipts for supervised kits, samples or lab items | PROTOTYPE / educational field candidate | `uc-courier-001-physical-object-custody-handoff.md` |
| `UC-MUSTER-001` | Privacy-preserving school muster / assembly reconciliation | converge synthetic or privacy-minimized check-in state across disconnected assembly points | PROTOTYPE / educational safety drill | `uc-muster-001-privacy-preserving-school-muster.md` |
| `UC-CORROBORATE-001` | Multi-source event corroboration | combine independent delayed sensor/human evidence without promoting one faulty report into an event | PROTOTYPE / emergency-adjacent research | `uc-corroborate-001-multi-source-event-corroboration.md` |

## Domain-specific / security / future research use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-AI-001` | Edge AI artifact sync | reconcile model/adapter/dataset versions and defer large artifact retrieval to rich links | RESEARCH + PROTOTYPE, child of CONTENT | `uc-ai-001-edge-ai-artifact-sync.md` |
| `UC-FL-001` | Delay-tolerant federated evaluation / learning rendezvous | handle staleness/provenance/fairness of asynchronous computed model contributions | RESEARCH / SOFTWARE PROTOTYPE | `uc-fl-001-delay-tolerant-federated-learning-rendezvous.md` |
| `UC-ROBOT-001` | Field robot / drone delayed data exchange | move supervisory/status/reference data during intermittent field contacts; bulk data later | RESEARCH | `uc-robot-001-field-robot-data-exchange.md` |
| `UC-TRUST-001` | Offline trust, key-rotation and revocation ferry | distribute compact signed trust generations when online status services are unavailable | RESEARCH / SECURITY INFRASTRUCTURE | `uc-trust-001-offline-trust-revocation-ferry.md` |
| `UC-COMPUTE-001` | Delay-tolerant edge job and result ferry | carry asynchronous jobs toward compute-rich nodes and return result references | RESEARCH / PROTOTYPE | `uc-compute-001-delay-tolerant-job-result-ferry.md` |
| `UC-TIME-001` | Signed time-anchor and clock-drift ferry | maintain bounded time/freshness uncertainty across disconnected nodes without assuming permanent NTP/GNSS | RESEARCH / INFRASTRUCTURE PROTOTYPE | `uc-time-001-signed-time-anchor-ferry.md` |
| `UC-WITNESS-001` | Offline transparency / witness gossip | compare compact signed publication checkpoints across partitions to detect synthetic split views/rollback | RESEARCH / SECURITY INFRASTRUCTURE | `uc-witness-001-offline-transparency-witness-gossip.md` |
| `UC-SHARD-001` | Diversity-coded multipath object carriage | test k-of-n coded redundancy versus one-copy/full replication under carrier dropout and storage limits | RESEARCH / SOFTWARE PROTOTYPE | `uc-shard-001-diversity-coded-multipath-object-carriage.md` |
| `UC-CREDENTIAL-001` | Offline verifiable capability / permit | verify a minimal signed capability while disconnected and ferry fresh revocation/generation state later | RESEARCH / SECURITY PROTOTYPE | `uc-credential-001-offline-verifiable-capability.md` |

## Practical priority for the Messina student network

Town names are scenario labels, never assumed RF links. The most immediately actionable workloads are those that produce useful, measurable traffic without collecting sensitive student data.

`UC-FARO-001` is intentionally not ranked as a field/student-network workload here: it is a software-first cross-project conformance case for the generic substrate.

### Tier A — first real-network candidates after HW-006 and their own governance gates

1. `UC-TRACE-001`: privacy-bounded encounter evidence so later topology/routing claims can use measured temporal graphs.
2. `UC-GAME-001`: synthetic signed tokens as a safe first student workload with known expected outcomes.
3. `UC-CODEBOOK-001`: classical shared-dictionary experiment directly tests the Pollicino thesis with public/synthetic records and exact fallback.
4. `UC-QUERY-001`: public-course and Raiatea-fixture metadata queries exercise asynchronous request/result paths without moving documents over LoRa.
5. `UC-PREFETCH-001`: exploit the dense school phase to seed small objects/references before students return to territorial clusters.
6. `UC-SERVICE-001`: advertise safe test services such as school resolver/egress/compute fixtures and discover them through carried state.
7. `UC-OPS-001`: manage harmless signed version/config fixtures for the distributed boards themselves.
8. `UC-IOT-001`: fixed sensors + student data mules create repeatable tiny-data traffic.
9. `UC-EDU-001`: public/open classroom resource descriptors make the network visibly useful.
10. `UC-CITSCI-001`: field observations create a real educational project while rich media stays on Wi-Fi.
11. `UC-TASK-001`: harmless lab task cards introduce conflict/deadline semantics; emergency drills come later.
12. `UC-EGRESS-001`: fake/allowlisted services exercise `DTN -> RICH_HOME -> DTN` request/reply behavior.
13. `UC-MUSTER-001`: synthetic one-time tokens can exercise multi-checkpoint reconciliation before any real attendance data is considered.
14. `UC-COURIER-001`: supervised kit/sample handoff creates tangible physical/digital custody state without GPS.
15. `UC-CONTENT-002`: reference discovery/reconciliation naturally matches scarce contacts and later home resolution.
16. `UC-ASSET-001`: synthetic/public physical-asset catalogs provide a safe eventual-consistency workload.
17. `UC-MOBILITY-001`: repeated routes become testable after privacy-safe contact logging exists.

### Tier B — software-first, stronger governance before field use

- `UC-EMERG-001`, `UC-MAP-001`, `UC-EVIDENCE-001` and `UC-CORROBORATE-001`: high public value but non-operational until authenticity, authoritative sources, security and field evidence are independently validated.
- `UC-TRANSIT-001`: strong territorial relevance, but operator/vehicle experiments need separate governance.
- `UC-MSG-001`: use bot/test endpoints first; human messaging requires E2E key lifecycle, metadata minimization and school/privacy governance.
- `UC-TIME-001`: potentially foundational; physical oscillator/drift measurements are needed before real bounds.
- `UC-TRUST-001`: security-critical and unsuitable for casual production rollout.
- `UC-WITNESS-001`: test-log split-view experiment is safe in software; production transparency integration requires a concrete threat model and independent security review.
- `UC-CREDENTIAL-001`: synthetic capabilities are safe in software; real student/institutional credentials require an explicit identity, privacy, revocation and security governance process.
- `UC-BACKUP-001`: useful with encrypted fixtures and bounded trusted replicas.

### Tier C — integration/research expansion

- FARO exact-content integration and later bounded-reference conformance, Raiatea rich integration, rural kiosk, AI artifacts, `UC-FL-001`, robots/drones and delay-tolerant compute jobs.
- `UC-SHARD-001`: keep software-only until coded diversity beats simple bounded replication after accounting for all bytes/compute/storage.

## Cross-use-case architecture pressure

Many materially different workloads now need object state to survive:

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

The new 2026-08-31 cases stress different parts of this path:

- CODEBOOK: carry shared decoding side information from rich/dense contact into later scarce contacts;
- QUERY: asynchronous request and multi-provider result paths across different bearers;
- CORROBORATE: independent delayed evidence, provenance and freshness under partition;
- MUSTER: privacy-minimized state reconciliation at multiple checkpoints;
- CREDENTIAL: offline verification plus delayed security-state refresh;
- FARO: preserve an application-owned signed scientific-package identity across exact storage/providers and, later, distributed discovery without converting transport integrity into scientific trust.

FARO also creates a second independent consumer for exact-content/reference/catalog pressure beyond DNA/content workloads. This supports continued study of a shared substrate boundary; it does not by itself authorize a new wire protocol or promote PR #52 research APIs to stable status.

## Workloads that should remain distinct

Avoid collapsing everything into one generic “message” benchmark. Distinct success metrics now include:

- DNA/topic: semantic relevance/subscriptions;
- FARO: exact canonical package preservation while publisher authenticity, evidence grade, applicability, local validation and Recommendation remain application-owned;
- emergency: usefulness deadline + authenticity/provenance;
- event corroboration: independent-source freshness and false/stale promotion;
- sensor ferry: freshness / many-to-one time series;
- citizen science: human provenance, review state and deferred rich evidence;
- content/reference index: discovery, wanted state, catalog reconciliation and later retrieval;
- federated metadata query: first-useful-hit latency, bounded provider work and asynchronous result merge;
- shared codebook: total bootstrap + payload break-even with exact reconstruction;
- prefetch: placement utility per seeded/stored byte before separation;
- service directory: capability freshness, provider selection and authorization separation;
- fleet management: configuration convergence, acknowledgement and rollback;
- encounter observatory: privacy-filtered temporal-graph recovery;
- education: delivery-before-class plus private return receipt;
- muster: correct aggregate/check-in reconciliation per exposed identity bit/field;
- asset catalog: inventory convergence/reservation lease;
- physical courier: custody generation and handoff/return correctness;
- public transport: authoritative status generation and useful-before-departure deadline;
- private mailbox: confidentiality/metadata minimization/delayed receipt;
- task board: claim/completion conflict and lease;
- Internet egress: idempotent request/reply and gateway authorization;
- field evidence: integrity/provenance/custody gaps;
- game harness: known application completion under supervised mobility;
- federated learning: model-update staleness/convergence/fairness;
- time: uncertainty growth and signed anchors;
- trust: rollback-resistant security-state convergence;
- offline capability: minimal-claim verification plus stale-revocation window;
- witness gossip: cross-partition signed-view consistency;
- geospatial: geographic relevance/version/delta semantics;
- backup: durability and bounded replication;
- scheduled mobility: contact predictability/route robustness;
- compute: job deadline/capability/idempotency;
- robot/drone: delayed supervisory state under a strict safety boundary;
- coded shards: exact-reconstruction reliability versus replication/storage overhead.

They may share transport primitives while keeping different success/kill criteria.

## Messina educational network pattern

Use pseudonymous logical clusters rather than student addresses. Public town names such as Rometta, Spadafora, Saponara, Villafranca and other province areas may label scenarios, but no synthetic result is measured coverage.

```text
territorial cluster A -- student/vehicle mule --+
territorial cluster B -- student/vehicle mule --+--> school mixing hub
territorial cluster C -- student/vehicle mule --+       |
                                                        +--> Wi-Fi/Internet gateway
```

The morning school phase can exercise connected-mesh behavior, controlled pre-positioning and codebook synchronization; afternoon/evening phases exercise store-carry-forward; home/school rich links can resolve payloads, execute metadata queries, advertise services or execute allowlisted requests. Exact object/bundle identity must survive lifecycle transitions.

Province-specific research scenarios can later include ferry/commuter or island/mainland logical contact schedules, but real Strait/Aeolian/road coverage and vehicle contact capacity require separate measured campaigns and permissions.

## Software-first rule

All use cases can begin as `MODEL_SYNTHETIC` experiments. Useful immediate dimensions include:

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
- service advertisement freshness and provider churn;
- active query propagation and bounded result merging;
- classical shared-dictionary bootstrap / fallback / break-even accounting;
- multi-source event corroboration with independent-source constraints;
- privacy-minimized muster/checkpoint generations using synthetic tokens;
- synthetic offline capabilities with revocation generations and replay tests;
- morning pre-positioning under finite cache budgets;
- synthetic physical-item custody generations;
- synthetic encrypted mailbox payloads and receipts;
- integrity hashes, staged corruption and custody receipts;
- transparency checkpoint split-view fixtures;
- tiny-model FL staleness/convergence experiments;
- game-token anti-replay and controlled completion;
- coded-shard carrier dropout versus simple replication;
- FARO canonical-package exact-content round trips with trust/evidence/local-validation non-escalation.

A model result remains a model result even if the topology uses real town names.

## Physical evidence boundary

No use case in this index changes the frozen LoRa PHY or authorizes real coverage/capacity claims.

HW-006 remains required before claims about:

- real LoRa contact availability;
- distance/NLOS behavior;
- useful bytes per encounter;
- real student/vehicle route capacity;
- real topology/routing/pre-positioning superiority;
- physical energy/battery performance;
- real encounter/inter-contact distributions;
- real oscillator/RTC drift bounds;
- real shared-dictionary CPU/energy versus airtime savings;
- real query/result, corroboration or muster completion latency over LoRa;
- embedded erasure-code feasibility/energy;
- real service-advertisement or physical-handoff latency over LoRa.

The frozen first campaign remains **42-byte frames / 2 dBm**, following the existing same-room -> separation -> wall -> multi-wall/floor -> outdoor evidence sequence.

Use-case-specific hardware/security/privacy gates may add requirements after HW-006; they do not weaken it.
