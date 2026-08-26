# PollicinoNet use-case index

Status: living index, 2026-08-26

This index is the navigation surface for concrete PollicinoNet use cases. Detailed proposals remain governed by `use-case-justification-gate.md`: appearing here does not imply adoption of a protocol, dependency or routing algorithm.

## Current primary / prototype-driving use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-DNA-001` | School hub / student data mule for topic-scoped DNA information | dense morning mixing + sparse territorial dissemination of relevant micro-information | PRIMARY / PROTOTYPE-DRIVING | `pollicinonet-use-cases.md` |
| `UC-CONTENT-001` | Reference and content data mule | carry magnet/URL/CID/manifest/wanted state now, retrieve authorized content later on rich links | PRIMARY / PROTOTYPE-DRIVING | `uc-content-001-reference-and-content-data-mule.md` |
| `UC-EMERG-001` | Resilient community bulletin | move compact time-sensitive/provenance-aware notices across disrupted clusters | PRIMARY / PROTOTYPE-DRIVING | `uc-emerg-001-resilient-community-bulletin.md` |
| `UC-IOT-001` | Community sensor ferry | collect many tiny time-series observations from sparse sensors and deliver later | PRIMARY / PROTOTYPE-DRIVING | `uc-iot-001-community-sensor-ferry.md` |
| `UC-MOBILITY-001` | Scheduled vehicle / commuter relay | exploit repeated mobile routes as predictable bridges between disconnected clusters | PRIMARY / PROTOTYPE-DRIVING | `uc-mobility-001-scheduled-vehicle-relay.md` |

## Integration / territorial use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-BACKUP-001` | Opportunistic safe-copy | preserve important exact data during gateway outages through bounded trusted replication | PROTOTYPE | `uc-backup-001-opportunistic-safe-copy.md` |
| `UC-RAIATEA-001` | Raiatea offline document sync | carry rights-aware document identity/manifest/wanted state, retrieve authorized payload later | PROTOTYPE / integration | `uc-raiatea-001-offline-document-manifest-sync.md` |
| `UC-RURAL-001` | Offline community knowledge/service kiosk | keep a useful local cache offline and asynchronously refresh it via mobile relays | PROTOTYPE | `uc-rural-001-offline-service-kiosk.md` |

## Domain-specific / future research use cases

| ID | Use case | Core problem | Status | Detailed document |
|---|---|---|---|---|
| `UC-AI-001` | Edge AI artifact sync | reconcile model/adapter/dataset versions and defer large artifact retrieval to rich links | RESEARCH + PROTOTYPE, child of CONTENT | `uc-ai-001-edge-ai-artifact-sync.md` |
| `UC-ROBOT-001` | Field robot / drone delayed data exchange | move supervisory/status/reference data during intermittent field contacts; bulk data later | RESEARCH | `uc-robot-001-field-robot-data-exchange.md` |

## Cross-use-case architecture pressure

The catalog now contains several materially different workloads that need the same state to survive bearer changes:

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

Examples are DNA micro-information, content references, sensor observations, emergency bulletins, backups and document manifests. This is increasingly strong evidence for **studying** a shared bearer/runtime boundary, but the architecture gate still requires measured simplification before stable adoption.

## Workloads that should remain distinct

Avoid collapsing the following into one generic “message” benchmark:

- **DNA/topic:** semantic relevance and subscriptions;
- **emergency bulletin:** usefulness deadline + authenticity/provenance;
- **sensor ferry:** freshness / many-to-one time series;
- **content/Raiatea/AI:** object identity, manifest, wanted state and later rich retrieval;
- **backup:** durability and bounded replication;
- **scheduled mobility:** contact predictability and route robustness;
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
- initial cache overlap;
- finite storage;
- gateway intermittency;
- multiple bearers;
- canonical DTN baselines.

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