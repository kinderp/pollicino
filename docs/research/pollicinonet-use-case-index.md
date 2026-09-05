# PollicinoNet use-case index

Status: living index, 2026-09-02 — **47 distinct use-case families**

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
| `UC-PREFETCH-001` | Mobility-aware cache prepositioning | decide which bounded objects/references to seed on which carriers before the school graph fragments | PRIMARY / PROTOTYPE-DRIVING SCHEDULING | `uc-prefetch-001-mobility-aware-cache-prepositioning.md` |
| `UC-SERVICE-001` | Offline service / capability directory | discover which intermittent node can eventually provide egress, compute, resolver or sensor service | PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE | `uc-service-001-offline-service-capability-directory.md` |
| `UC-QUERY-001` | Delay-tolerant federated metadata query | carry an active search request to disconnected indexes and return compact result references asynchronously | PRIMARY / PROTOTYPE-DRIVING INTEGRATION | `uc-query-001-delay-tolerant-federated-metadata-query.md` |
| `UC-CODEBOOK-001` | Shared compression side-information ferry | pre-position exact shared dictionaries/models so later scarce-link objects can be represented with fewer total bits | PRIMARY / PROTOTYPE-DRIVING RESEARCH | `uc-codebook-001-shared-compression-side-information-ferry.md` |
| `UC-RFMAP-001` | Privacy-bounded RF evidence survey and site planning | replace guessed range with controlled replayable RF checkpoint evidence before infrastructure/coverage claims | PRIMARY / PHYSICAL-EVIDENCE INFRASTRUCTURE | `uc-rfmap-001-privacy-bounded-rf-evidence-survey.md` |
| `UC-ENERGY-001` | Energy-aware relay conservation | preserve delivery while respecting local battery reserves and fair relay load | PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE | `uc-energy-001-energy-aware-relay-conservation.md` |
| `UC-SENSORQ-001` | Delay-tolerant sensor query and aggregation ferry | move a small query to disconnected sensor history and return only the exact aggregate/result actually needed | PRIMARY / PROTOTYPE-DRIVING | `uc-sensorq-001-delay-tolerant-sensor-query-aggregation-ferry.md` |
| `UC-DRAIN-001` | Graceful pre-shutdown bundle/custody drain | hand off the most important network state before a relay is intentionally or predictably lost | PRIMARY / PROTOTYPE-DRIVING INFRASTRUCTURE | `uc-drain-001-graceful-pre-shutdown-bundle-custody-drain.md` |

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
| `UC-FIND-001` | Privacy-preserving lost-object finding ferry | carry authorized search state and delayed beacon sightings without continuous location tracking | PROTOTYPE / privacy-sensitive educational field candidate | `uc-find-001-privacy-preserving-lost-object-finding.md` |
| `UC-CALIB-001` | Opportunistic sensor calibration ferry | move calibration evidence/reference encounters so disconnected low-cost sensors can reduce drift/error | PROTOTYPE / IoT + citizen-science field candidate | `uc-calib-001-opportunistic-sensor-calibration-ferry.md` |
| `UC-NEED-001` | Offline need/offer resource matching | reconcile expiring consumable quantities and partial fulfillment without double-counting stale stock | PROTOTYPE / emergency-adjacent | `uc-need-001-offline-need-offer-resource-matching.md` |

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
| `UC-ACTIVE-001` | Delay-tolerant active-learning / expert-review ferry | carry uncertain-sample references to a later reviewer and return labels without continuous connectivity | RESEARCH / SOFTWARE PROTOTYPE | `uc-active-001-delay-tolerant-active-learning-review.md` |
| `UC-CONSENT-001` | Delay-tolerant consent and retention-policy ferry | propagate monotonic data-usage/restriction generations and make stale-policy windows explicit | RESEARCH / PRIVACY INFRASTRUCTURE | `uc-consent-001-delay-tolerant-consent-retention-policy-ferry.md` |
| `UC-SECADV-001` | Offline vulnerability advisory and patch-reference ferry | tell disconnected nodes whether they are actually affected and where to retrieve a trusted patch later | PROTOTYPE / SECURITY OPERATIONS | `uc-secadv-001-offline-vulnerability-advisory-patch-reference-ferry.md` |

## Practical priority for the Messina student network

Town names are scenario labels, never assumed RF links. The most immediately actionable workloads produce useful, measurable traffic without collecting sensitive student data.

### Tier A — first real-network candidates after HW-006 and their own governance gates

1. `UC-RFMAP-001`: controlled checkpoint RF evidence so future topology/gateway claims stop relying on guessed range.
2. `UC-TRACE-001`: privacy-bounded encounter evidence so later topology/routing claims can use measured temporal graphs.
3. `UC-GAME-001`: synthetic signed tokens as a safe first student workload with known expected outcomes.
4. `UC-CALIB-001`: harmless environmental sensors + reference checkpoint create a repeatable calibration/data-mule experiment.
5. `UC-SENSORQ-001`: small sensor queries/aggregates directly test information minimization without moving full histories.
6. `UC-DRAIN-001`: planned shutdown/low-battery fixtures stress custody, persistence and bounded final handoff.
7. `UC-CODEBOOK-001`: classical shared-dictionary experiment directly tests the Pollicino thesis with public/synthetic records and exact fallback.
8. `UC-QUERY-001`: public-course and Raiatea-fixture metadata queries exercise asynchronous request/result paths without moving documents over LoRa.
9. `UC-PREFETCH-001`: exploit the dense school phase to seed small objects/references before students return to territorial clusters.
10. `UC-SERVICE-001`: advertise safe test services such as school resolver/egress/compute fixtures and discover them through carried state.
11. `UC-OPS-001`: manage harmless signed version/config fixtures for the distributed boards themselves.
12. `UC-ENERGY-001`: begin with local reserve/budget policies; calibrate them with real current measurements before deployment claims.
13. `UC-IOT-001`: fixed sensors + student data mules create repeatable tiny-data traffic.
14. `UC-EDU-001`: public/open classroom resource descriptors make the network visibly useful.
15. `UC-CITSCI-001`: field observations create a real educational project while rich media stays on Wi-Fi.
16. `UC-FIND-001`: authorized lab-object beacon finding is a strong demo after explicit privacy/consent governance.
17. `UC-TASK-001`: harmless lab task cards introduce conflict/deadline semantics; emergency drills come later.
18. `UC-EGRESS-001`: fake/allowlisted services exercise `DTN -> RICH_HOME -> DTN` request/reply behavior.
19. `UC-MUSTER-001`: synthetic one-time tokens can exercise multi-checkpoint reconciliation before any real attendance data is considered.
20. `UC-COURIER-001`: supervised kit/sample handoff creates tangible physical/digital custody state without GPS.
21. `UC-CONTENT-001` / `UC-CONTENT-002`: authorized reference carriage/search naturally matches scarce contacts and later home resolution.
22. `UC-ASSET-001`: synthetic/public physical-asset catalogs provide a safe eventual-consistency workload.
23. `UC-MOBILITY-001`: repeated routes become testable after privacy-safe contact logging exists.

### Tier B — software-first, stronger governance before field use

- `UC-EMERG-001`, `UC-MAP-001`, `UC-EVIDENCE-001`, `UC-CORROBORATE-001` and `UC-NEED-001`: high public value but non-operational until authenticity, authoritative sources, security and field evidence are independently validated.
- `UC-TRANSIT-001`: strong territorial relevance, but operator/vehicle experiments need separate governance.
- `UC-MSG-001`: use bot/test endpoints first; human messaging requires E2E key lifecycle, metadata minimization and school/privacy governance.
- `UC-DNA-001` and `UC-CONSENT-001`: synthetic topic/policy data first; real student/privacy semantics require an explicit governance and lawful-basis process.
- `UC-TIME-001`: potentially foundational; physical oscillator/drift measurements are needed before real bounds.
- `UC-TRUST-001`, `UC-WITNESS-001`, `UC-CREDENTIAL-001` and `UC-SECADV-001`: security-sensitive; use test keys, synthetic advisories/capabilities/logs and independently validate rollback/recovery before field claims.
- `UC-BACKUP-001`: useful with encrypted fixtures and bounded trusted replicas.

### Tier C — integration/research expansion

- `UC-RAIATEA-001`, `UC-RURAL-001`, `UC-AI-001`, `UC-FL-001`, `UC-ROBOT-001` and `UC-COMPUTE-001`.
- `UC-ACTIVE-001`: test delayed uncertain-sample review on public/synthetic data before any richer edge-AI integration.
- `UC-SHARD-001`: keep software-only until coded diversity beats simple bounded replication after accounting for all bytes/compute/storage.

## Cross-use-case architecture pressure

Many materially different workloads require object state to survive:

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

The 2026-09-02 additions stress new dimensions:

- SENSORQ: active request -> delayed local computation -> compact result return;
- DRAIN: custody/persistence under a known node-disappearance deadline;
- CONSENT: privacy-policy generation, stale-state windows and rollback resistance;
- SECADV: software applicability/security advisory -> later rich-link patch resolution;
- NEED: quantity/expiry/partial-fulfillment convergence under partitions.

This supports continued study of a shared bearer/runtime boundary; it does not by itself authorize a new wire protocol.

## Workloads that should remain distinct

Avoid collapsing everything into a generic “message” benchmark. Distinct success metrics include:

- DNA/topic: semantic relevance/subscriptions;
- consent/policy: stale-policy exposure window and monotonic restriction enforcement;
- emergency bulletin: usefulness deadline + authenticity/provenance;
- need/offer: quantity fulfillment, expiry and double-count prevention;
- event corroboration: independent-source freshness and false/stale promotion;
- sensor ferry: freshness / many-to-one time series;
- sensor query: aggregate correctness and raw bytes avoided per query/result cost;
- sensor calibration: calibration error and age of trusted calibration state;
- citizen science: human provenance, review state and deferred rich evidence;
- lost-object finding: time-to-authorized-sighting per disclosed location/identity field;
- RF survey: measured/unknown link evidence, reproducibility and site-plan sensitivity;
- energy-aware relay: delivery/deadline success versus remaining energy/fair relay load;
- graceful drain: post-shutdown delivery rescued per final-handoff byte/energy while preserving custody;
- content/reference index: discovery, wanted state, reconciliation and later retrieval;
- software advisory: time-to-awareness, applicability precision and rich-link patch retrieval;
- federated metadata query: first-useful-hit latency and bounded provider work;
- shared codebook: total bootstrap + payload break-even with exact reconstruction;
- prefetch: placement utility per seeded/stored byte before separation;
- service directory: capability freshness, provider selection and authorization separation;
- fleet management: configuration convergence, acknowledgement and rollback;
- encounter observatory: privacy-filtered temporal-graph recovery;
- education: delivery-before-class plus private return receipt;
- muster: correct aggregate/check-in reconciliation per exposed identity field;
- asset catalog: inventory convergence/reservation lease;
- physical courier: custody generation and handoff/return correctness;
- public transport: authoritative status generation and useful-before-departure deadline;
- private mailbox: confidentiality/metadata minimization/delayed receipt;
- task board: claim/completion conflict and lease;
- Internet egress: idempotent request/reply and gateway authorization;
- field evidence: integrity/provenance/custody gaps;
- game harness: known application completion under supervised mobility;
- federated learning: model-update staleness/convergence/fairness;
- active learning: model gain per delayed review/label byte and stale-label handling;
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

Use pseudonymous logical clusters rather than student addresses. Public town names such as Rometta, Spadafora, Saponara, Villafranca, Messina and other province areas may label scenarios, but no synthetic result is measured coverage.

```text
territorial cluster A -- student/vehicle mule --+
territorial cluster B -- student/vehicle mule --+--> school mixing hub
territorial cluster C -- student/vehicle mule --+       |
                                                        +--> Wi-Fi/Internet gateway
```

The morning school phase can exercise connected-mesh behavior, controlled pre-positioning, codebook/policy/advisory synchronization and synthetic needs/queries; afternoon/evening phases exercise store-carry-forward; home/school rich links can resolve payloads, execute queries, retrieve harmless patch fixtures or return receipts/results. Exact object/bundle identity must survive lifecycle transitions.

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
- active metadata and sensor query propagation with bounded results;
- classical shared-dictionary bootstrap/fallback/break-even accounting;
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
- synthetic RF checkpoint matrices with UNKNOWN-aware planning;
- sensor bias/drift/noise plus opportunistic calibration encounters;
- synthetic lost-beacon detections with rotating IDs and replay/expiry;
- per-action synthetic energy budgets and reserve policies;
- toy active-learning review with delayed label return/model-generation checks;
- synthetic policy withdrawal/restriction generations and stale-peer enforcement;
- synthetic SBOM/advisory applicability and delayed patch-reference resolution;
- synthetic NEED/OFFER quantities, partial fulfillment and stale replay;
- planned node disappearance plus bounded custody/bundle drain policies.

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
- real metadata/sensor query or corroboration completion latency over LoRa;
- embedded erasure-code feasibility/energy;
- real service-advertisement or physical-handoff latency over LoRa;
- real RF coverage/site suitability or gateway/relay count;
- real BLE lost-object detection/scan energy;
- real sensor calibration improvement;
- real active-learning handoff/inference energy or label-return capacity;
- real pre-shutdown drain completion, brownout timing or persistence under power loss;
- real policy/advisory propagation windows or embedded signature/update cost;
- real need/offer matching latency in an operational emergency context.

The frozen first campaign remains **42-byte frames / 2 dBm**, following the existing same-room -> separation -> wall -> multi-wall/floor -> outdoor evidence sequence.

Use-case-specific hardware/security/privacy gates may add requirements after HW-006; they do not weaken it.