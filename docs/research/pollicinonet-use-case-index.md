# PollicinoNet use-case index

Status: living index, 2026-08-27

This index is the navigation surface for concrete PollicinoNet use cases. Detailed proposals remain governed by `use-case-justification-gate.md`: appearing here does not imply adoption of a protocol, dependency, routing algorithm or PHY change.

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
| `UC-EDU-001` | Offline classroom resource and assignment relay | distribute signed learning-resource metadata and return private receipts across intermittent student contacts | PRIMARY / PROTOTYPE-DRIVING | `uc-edu-001-classroom-resource-relay.md` |

## Integration / territorial use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-BACKUP-001` | Opportunistic safe-copy | preserve important exact data during gateway outages through bounded trusted replication | PROTOTYPE | `uc-backup-001-opportunistic-safe-copy.md` |
| `UC-RAIATEA-001` | Raiatea offline document sync | carry rights-aware document identity/manifest/wanted state, retrieve authorized payload later | PROTOTYPE / integration | `uc-raiatea-001-offline-document-manifest-sync.md` |
| `UC-RURAL-001` | Offline community knowledge/service kiosk | keep a useful local cache offline and asynchronously refresh it via mobile relays | PROTOTYPE | `uc-rural-001-offline-service-kiosk.md` |
| `UC-MAP-001` | Offline geospatial and local-hazard delta exchange | move only relevant changed map/layer references instead of full geospatial datasets | PROTOTYPE / emergency-adjacent | `uc-map-001-offline-geospatial-delta-exchange.md` |

## Domain-specific / security / future research use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-AI-001` | Edge AI artifact sync | reconcile model/adapter/dataset versions and defer large artifact retrieval to rich links | RESEARCH + PROTOTYPE, child of CONTENT | `uc-ai-001-edge-ai-artifact-sync.md` |
| `UC-ROBOT-001` | Field robot / drone delayed data exchange | move supervisory/status/reference data during intermittent field contacts; bulk data later | RESEARCH | `uc-robot-001-field-robot-data-exchange.md` |
| `UC-TRUST-001` | Offline trust, key-rotation and revocation ferry | distribute compact signed trust generations when online status services are unavailable | RESEARCH / SECURITY INFRASTRUCTURE | `uc-trust-001-offline-trust-revocation-ferry.md` |
| `UC-COMPUTE-001` | Delay-tolerant edge job and result ferry | carry asynchronous jobs toward compute-rich nodes and return result references | RESEARCH / PROTOTYPE | `uc-compute-001-delay-tolerant-job-result-ferry.md` |

## Practical priority for the Messina student network

The most immediately actionable workloads are not necessarily the most ambitious ones.

### Tier A — first real-network candidates after HW-006

1. `UC-OPS-001`: the network needs to manage its own distributed nodes; start with harmless signed version/config fixtures, not firmware flashing.
2. `UC-IOT-001`: fixed sensors + student data mules create repeatable, measurable tiny-data traffic.
3. `UC-EDU-001`: public/open classroom resource descriptors make the experimental network understandable and useful to students without requiring personal data.
4. `UC-CONTENT-002`: compact reference discovery/reconciliation is well matched to scarce LoRa links and later home Wi-Fi resolution.
5. `UC-MOBILITY-001`: repeated school/commuter routes can be tested after privacy-safe contact logging exists.

### Tier B — software-first, stronger governance before field use

- `UC-EMERG-001` and `UC-MAP-001`: high public value but must remain non-operational until authenticity, authoritative sources and field evidence are independently validated.
- `UC-TRUST-001`: needed for a mature network, but security-critical and unsuitable for casual production rollout.
- `UC-BACKUP-001`: useful with encrypted fixtures and bounded trusted replicas.

### Tier C — integration/research expansion

- Raiatea, rural kiosk, AI artifacts, robots/drones and delay-tolerant compute jobs.

## Cross-use-case architecture pressure

The catalog contains materially different workloads that need state to survive bearer changes:

```text
CONNECTED_MESH / local contacts
          |
          v
OPPORTUNISTIC_DTN / physical carry
          |
          v
RICH_LOCAL / Wi-Fi or LAN
          |
          v
INTERNET / remote provider or gateway
```

Examples now include DNA micro-information, content references, sensor observations, emergency bulletins, fleet configuration, educational resources, trust state, backups and document/map manifests. This is increasingly strong evidence for **studying** a shared bearer/runtime boundary, but the architecture gate still requires measured simplification before stable adoption.

## Workloads that should remain distinct

Avoid collapsing the following into one generic “message” benchmark:

- **DNA/topic:** semantic relevance and subscriptions;
- **emergency bulletin:** usefulness deadline + authenticity/provenance;
- **sensor ferry:** freshness / many-to-one time series;
- **content/reference index:** discovery, wanted state, catalog reconciliation and later rich retrieval;
- **fleet management:** configuration convergence, acknowledgement and rollback;
- **education:** delivery-before-class/deadline plus privacy-preserving return receipts;
- **trust:** rollback-resistant security-state convergence;
- **geospatial:** geographic relevance, version/delta semantics and location privacy;
- **backup:** durability and bounded replication;
- **scheduled mobility:** contact predictability and route robustness;
- **compute:** job deadline/capability, idempotency and result return;
- **robot/drone:** delayed supervisory state with a strict safety boundary.

They can share transport primitives while keeping different success metrics.

## Messina educational network pattern

Use pseudonymous logical clusters rather than student addresses. Public town names can label scenario areas (for example Rometta, Spadafora, Saponara, Villafranca or other province clusters), but no synthetic result should be presented as measured coverage.

A recurring laboratory topology can be:

```text
territorial cluster A -- student/vehicle mule --+
territorial cluster B -- student/vehicle mule --+--> school mixing hub
territorial cluster C -- student/vehicle mule --+       |
                                                        +--> Wi-Fi/Internet gateway
```

The morning school phase can exercise connected-mesh behavior; afternoon/evening phases exercise store-carry-forward. The exact same object identity/cache/custody state should survive both.

## Software-first rule

All use cases above can begin with `MODEL_SYNTHETIC` experiments using the existing scenario-family/contact-window framework. Useful immediate dimensions include:

- topology/contact schedule;
- logical byte budget independent from duration;
- priorities and TTL;
- application deadline where the use case explicitly needs one;
- initial cache/reference overlap;
- finite storage;
- gateway intermittency;
- multiple bearers;
- canonical DTN baselines;
- version/generation convergence;
- signed fixture verification;
- job/capability queues;
- coarse geographic-interest filters.

## Physical evidence boundary

No use case in this index changes the frozen LoRa PHY or authorizes real coverage/capacity claims.

HW-006 remains required before claims about:

- real LoRa contact availability;
- distance/NLOS behavior;
- useful bytes per encounter;
- real student/vehicle route capacity;
- real topology/routing superiority;
- physical energy or battery performance.

The frozen first campaign remains **42-byte frames / 2 dBm**, following the existing same-room → separation → wall → multi-wall/floor → outdoor evidence sequence.
