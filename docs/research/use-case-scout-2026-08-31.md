# PollicinoNet use-case scouting checkpoint — 2026-08-31

Status: research checkpoint only; no PHY or hardware configuration change

## Repository-first duplicate check

The current catalog contained 32 distinct families before this checkpoint, including DNA/data-mule, content/reference search, emergency bulletin, IoT sensor ferry, scheduled mobility, fleet management, education, TRACE, citizen science, task coordination, Internet egress, prefetch, service discovery, backup, Raiatea, rural kiosk, geospatial delta, asset reservation, transit, private mailbox, evidence, game harness, physical custody, AI/FL, robot/drone, trust, compute, time, witness gossip and coded shards.

The repository was searched for the new concepts (`corroboration`, `muster`, `credential`, `federated query`, `compression dictionary` / shared side information) before adding them. No existing formal use-case family covered them with the same success metric.

## New use cases

### 1. UC-CODEBOOK-001 — Shared compression side-information ferry

**Why it is new:** this is not application-object prefetch. It prepositions shared decoding state so later objects may be represented losslessly with fewer total bits.

**Why it matters:** it creates a concrete bridge between Pollicino compression research and PollicinoNet. Zstandard is a useful classical baseline because its reference implementation explicitly supports trained dictionaries for correlated small-data families, requiring the same dictionary at compression and decompression.

**First gate:** public/synthetic small records only; compare raw, ordinary classical compression and shared-dictionary compression while charging dictionary bootstrap, identity, fallback and all wire bytes.

**Decision:** PRIMARY / PROTOTYPE-DRIVING. Start classical; learned side information remains gated by Track A evidence and embedded feasibility.

### 2. UC-QUERY-001 — Delay-tolerant federated metadata query

**Why it is new:** `UC-CONTENT-002` is passive/encounter-driven catalog discovery. QUERY begins with an explicit request that may be carried to several disconnected indexes and receive asynchronous partial results by different paths.

**Why it matters:** it can integrate PollicinoNet with Raiatea/NAS/local indexes without moving documents over LoRa. Prior work on opportunistic networks explicitly treats content search/retrieval as difficult under changing topology and intermittent contact; this justifies studying a simple bounded query/result application model before inventing complex indexing protocols.

**Decision:** PRIMARY / PROTOTYPE-DRIVING INTEGRATION. Start with opaque query IDs, explicit bounded results and public-course metadata.

### 3. UC-CORROBORATE-001 — Multi-source event corroboration

**Why it is new:** sensor ferry moves observations; emergency bulletin moves notices. CORROBORATE asks whether multiple independent delayed observations support the same event without allowing one faulty source to promote an alert-like state.

**Local relevance:** Messina municipal civil-protection notices repeatedly address meteo, hydrogeological and hydraulic risk. This makes synthetic rain/stream/landslide-indicator scenarios locally understandable, but the Pollicino prototype must never be represented as an operational warning system.

**Decision:** PROTOTYPE / emergency-adjacent. Begin with signed synthetic sources and a simple `2-of-3 independent fresh sources` baseline; no probabilistic fusion/ML/consensus unless that baseline fails a concrete workload.

### 4. UC-MUSTER-001 — Privacy-preserving school muster / assembly reconciliation

**Why it is new:** task coordination is about claims/work; muster is about reconciling presence/checkpoint state while minimizing identity exposure.

**Why it matters:** it is a concrete school exercise that can use synthetic one-time tokens, multiple assembly points and a disconnected coordinator. It provides a real-world state-reconciliation workload without needing public Internet or student home locations.

**Decision:** PROTOTYPE. Real student attendance stays out of the first pilot; use staff/synthetic tokens until privacy/legal governance exists.

### 5. UC-CREDENTIAL-001 — Offline verifiable capability / permit

**Why it is new:** TRUST distributes network/security generations; CREDENTIAL studies a holder presenting a minimal capability to an offline verifier, while revocation/generation updates arrive later through the DTN.

**Why it matters:** W3C Verifiable Credentials 2.0 became a Recommendation in May 2025 and provides a standards reference for signed, machine-verifiable, privacy-aware claims. Pollicino should not automatically implement the full VC stack: first benchmark tiny signed synthetic capabilities and compact standards-shaped alternatives.

**Decision:** RESEARCH / SECURITY PROTOTYPE. Synthetic identities/keys only until independent security and institutional governance exist.

## Practical priority

For the student-network roadmap the new cases are ordered:

1. **CODEBOOK** — safest and most directly tied to the core Pollicino scientific thesis.
2. **QUERY** — concrete multi-bearer/Raiatea integration with public metadata.
3. **MUSTER** — very tangible educational reconciliation workload using synthetic tokens.
4. **CORROBORATE** — high public value, but stronger emergency/security boundary.
5. **CREDENTIAL** — useful security primitive, but production identity is deliberately deferred.

CORROBORATE can still be a top research priority because it creates a discriminating emergency workload; it is lower in *field rollout* priority because safety/authenticity requirements are stronger.

## Messina synthetic day scenario

No town-to-town RF path is assumed.

```text
morning / school hub
  - synchronize codebook/topic-v1
  - issue public metadata queries
  - initialize synthetic muster tokens

students physically disperse

Rometta-like     Spadafora-like     Saponara-like     Villafranca-like
   |                  |                  |                   |
 sensor fixture   local index       checkpoint fixture   local index
   |                  |                  |                   |
 observations      query hits         muster state        query hits
   +--------- store / carry / forward through student nodes ----------+

next school/home rich contact
  - merge query results
  - verify exact codebook decoding
  - reconcile synthetic muster
  - evaluate corroboration evidence
```

Every location name is a logical cluster label only.

## Software-first experiments

### CODEBOOK

- 100–10,000 correlated small records;
- charge dictionary bootstrap + identity + fallback;
- sweep number of later messages and find break-even;
- exact SHA verification;
- compare raw, no-dictionary classical and shared-dictionary classical baselines.

### QUERY

- 4 disconnected indexes;
- overlapping catalogs;
- query/result asymmetric routes;
- bounded top-k;
- provider churn and stale responses;
- duplicate query suppression.

### CORROBORATE

- independent vs copied sources;
- delayed evidence;
- false source;
- stale replay;
- `first report wins` vs simple threshold corroboration.

### MUSTER

- multiple checkpoints;
- one-time synthetic tokens;
- duplicate/out-of-order check-ins;
- disconnected coordinator;
- compare identity-rich baseline with privacy-minimized summaries.

### CREDENTIAL

- synthetic issuer/holder/verifier;
- expiry;
- revocation generation delay;
- rollback/replay;
- compact signed fixture vs standards-shaped representation at the byte/verification-cost level.

All of the above remain `MODEL_SYNTHETIC` until measured hardware evidence exists.

## Hardware boundary

No new case changes the frozen LoRa PHY.

HW-006 remains the first physical gate:

```text
42-byte frames / 2 dBm
same-room
 -> greater separation
 -> one wall
 -> multiple walls / floor
 -> outdoor
```

After HW-006, use-case-specific physical gates include:

- CODEBOOK: actual ESP32 RAM/flash/CPU/energy and real airtime savings after measured frame-size calibration;
- QUERY: real request/result envelopes per encounter and `mesh -> carry -> home Wi-Fi` latency;
- MUSTER: supervised usability/contact behavior with synthetic tokens only;
- CORROBORATE: controlled harmless sensors, source independence and sensor-to-mule latency;
- CREDENTIAL: crypto verification cost, key storage and revocation-state propagation.

None of these measurements can be inferred from synthetic town-labelled schedules.

## External references used in this checkpoint

- City of Messina civil-protection notice, 15 March 2026, orange alert for meteo/hydrogeological/hydraulic risk: https://comune.messina.it/it/news/6477232
- Zstandard project documentation: dictionary compression for correlated small data: https://facebook.github.io/zstd/
- W3C, Verifiable Credentials 2.0 Recommendation family, 15 May 2025: https://www.w3.org/press-releases/2025/verifiable-credentials-2-0/
- Hyytiä, Bayhan, Ott, Kangasharju, "Searching a needle in (linear) opportunistic networks", 2014, DOI 10.1145/2641798.2641828.
- Current IETF DTN work remains relevant background, including BP SAND draft-ietf-dtn-bp-sand-03 (July 2026), but none of today's use cases adopts BPv7/SAND automatically.

## Repository effect

Added five detailed use-case documents and updated `pollicinonet-use-case-index.md` from 32 to 37 distinct families. Documentation/research only: no protocol source, LoRa PHY setting or hardware configuration was changed.