# PollicinoNet use-case scouting — 2026-08-28

Status: research checkpoint

## Repository state checked

The active research branch was reviewed before adding new cases. The catalog already covered DNA/topic data mules, reference/content distribution and search, emergency bulletins, fixed IoT/sensor ferrying, scheduled mobility, fleet management, educational resources, backup, Raiatea, rural kiosks, geospatial deltas, trust/revocation, AI artifacts, robots/drones and delay-tolerant compute.

This round therefore avoids adding another generic “message”, “sensor”, “content”, “map” or “vehicle” variant. Each new entry introduces a distinct success criterion or operational requirement.

## New use cases added

### UC-TRACE-001 — Privacy-preserving encounter observatory

Distributed student nodes record bounded encounter summaries, ferry them to school and reconstruct a privacy-filtered temporal graph that can be replayed in the simulator.

Why it matters: this is the bridge from synthetic mobility assumptions to future measured routing evidence. It also gives DNATrace-style analysis a concrete integration target without assuming such an integration already exists.

Difficulty: medium-high because privacy, time uncertainty and reproducible replay matter more than the wire format.

### UC-CITSCI-001 — Student field-observation / citizen-science ferry

Students generate small structured observations such as biodiversity, coastline litter, garden/phenology or other non-sensitive educational field records. Photos/audio remain references until Wi-Fi/Internet is available.

Why it matters: it creates useful real application traffic for the student network without turning LoRa into a bulk-media link.

Difficulty: medium. Main new work is schema, review state, duplicate handling and geoprivacy.

### UC-TIME-001 — Signed time-anchor and clock-drift ferry

Authoritative gateways issue signed time generations with explicit uncertainty; disconnected nodes carry/refresh them and track uncertainty growth.

Why it matters: TTL, deadlines, freshness, encounter traces and trust-state validity all become less defensible if every simulated/real node is silently assumed to have perfect time.

Difficulty: medium-high. The payload is tiny, but fail-closed uncertainty and recovery semantics need care.

### UC-ASSET-001 — Offline physical-asset catalog and reservation ferry

Compact availability generations and bounded reservation leases for physical resources such as robotics kits, sensors, books, tools or loan devices propagate through student relays.

Why it matters: this is not content delivery; it tests eventual inventory consistency and conflict/lease semantics for a physical resource that is picked up separately.

Difficulty: medium.

### UC-TRANSIT-001 — Offline public-transport timetable/service delta ferry

Authoritative route/timetable/service generations are filtered by route interest and carried across intermittent contacts, while full GTFS/NeTEx/SIRI feeds stay on rich links.

Why it matters: it gives the Messina-area network a territorial public-information workload with a clear usefulness deadline: an update delivered after the relevant departure may be technically delivered but useless.

Difficulty: medium in simulation; higher for any real operator/vehicle integration.

## Top three from this round

### 1. UC-TRACE-001

Most important for the research program. After HW-006 and privacy governance, a small student pilot can create the first real temporal contact evidence. Those traces can then be replayed against the current routing baselines instead of extrapolating from synthetic schedules.

Immediate software experiment: generate partial encounter reports from a known synthetic temporal graph; compare raw trace, rotating-pseudonym trace and time-bucketed aggregate, then quantify how much routing conclusions change after privacy filtering.

### 2. UC-CITSCI-001

Best new student-facing application. It can become an actual school project and naturally demonstrates “small metadata now, rich evidence later”. It also combines DNA-like topic interests, content references, provenance and physical student movement without duplicating any one of those existing use cases.

Immediate software experiment: three territorial/topic cohorts generate observation descriptors; compare broadcast, topic-only and topic+coarse-area filtering; return teacher-review acknowledgements later through the DTN.

### 3. UC-TIME-001

Most strategically useful infrastructure addition. TRACE, sensor freshness, application deadlines and security generations all benefit from explicit clock uncertainty.

Immediate software experiment: assign independent offset/drift to every node, inject sleep/reboot and stale signed anchors, then count TTL/deadline decisions that differ between “perfect clock” and uncertainty-aware execution.

`UC-ASSET-001` is close behind because it is easy to demonstrate safely with synthetic/public inventory. `UC-TRANSIT-001` has strong territorial relevance but should remain software/public-data-first until provenance and any operator interaction are separately governed.

## Literature / standards context used

- Chaintreau et al., real human contact traces and opportunistic forwarding: https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-617.html
- de Montjoye et al., mobility traces can remain highly identifying even after apparent anonymization: https://doi.org/10.1038/srep01376
- NITOS BikesNet, volunteer-carried city-scale mobile sensing with intermittent connectivity: https://doi.org/10.1109/MDM.2014.17
- RFC 4838, DTN architecture dependence on time for identification, routing and expiration: https://www.rfc-editor.org/rfc/rfc4838.html
- IETF DTN time-synchronization problem statement: https://datatracker.ietf.org/doc/html/draft-templin-dtntsync-00
- Bujari et al., public-transport vehicles as delay-tolerant carriers in Milan: https://doi.org/10.3233/AIS-170443
- Italian National Access Point for multimodal mobility / NeTEx context: https://www.cciss.it/nap/mmtis/public/en/static/multimodal

These sources motivate workload families and constraints. They do not provide physical evidence for PollicinoNet or Messina province.

## What can be tested before hardware

The existing `MODEL_SYNTHETIC` framework can already test:

- partial encounter-log reconstruction, privacy filtering and trace replay;
- citizen-science topic/coarse-area filtering, duplicate suppression and delayed review;
- clock offset/drift, uncertainty growth, signed anchor generations and anti-rollback;
- physical-asset availability generations, leases and reservation conflicts;
- route/status generations, subscriptions, stale suppression and useful-before-departure deadlines.

No LoRa PHY change is required for any of these experiments.

## Physical evidence required later

HW-006 remains the first physical gate and the frozen campaign remains **42-byte frames / 2 dBm**, same-room → separation → wall → multi-wall/floor → outdoor.

Use-case-specific later evidence:

- TRACE: real contact-definition threshold, encounter/inter-contact distributions and privacy-safe field logging after consent/governance;
- CITSCI: field handling, battery impact and measured observation-delivery latency;
- TIME: RTC/oscillator drift across sleep/reboot/temperature and real verification cost;
- ASSET: scan/tag reliability and real room/site inventory workflow;
- TRANSIT: only after separate permission, measured station/route contact opportunities and provenance-safe source ingestion.

No real coverage, range, capacity, battery or routing-superiority claim is made in this scouting round.

## Repository changes

Added:

- `uc-trace-001-privacy-preserving-encounter-observatory.md`;
- `uc-citsci-001-student-field-observation-ferry.md`;
- `uc-time-001-signed-time-anchor-ferry.md`;
- `uc-asset-001-offline-physical-asset-catalog.md`;
- `uc-transit-001-offline-public-transport-delta-ferry.md`;
- this checkpoint.

Updated:

- `pollicinonet-use-case-index.md` — catalog date, five new entries, practical Messina priority tiers, cross-use-case pressures, distinct metrics and software/physical evidence dimensions.

No source code, LoRa PHY value or hardware configuration was changed.
