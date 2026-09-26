# PollicinoNet use-case scout — 2026-09-02

Status: research checkpoint; documentation/use-case governance only

## Scope

This checkpoint extends the living use-case catalog only after checking the existing 42 families for overlap. No LoRa PHY, hardware configuration, production wire format or field-performance claim is changed.

Five new families are added:

1. `UC-CONSENT-001` — delay-tolerant consent and retention-policy ferry;
2. `UC-SECADV-001` — offline vulnerability advisory and patch-reference ferry;
3. `UC-SENSORQ-001` — delay-tolerant sensor query and aggregation ferry;
4. `UC-NEED-001` — offline need/offer resource matching;
5. `UC-DRAIN-001` — graceful pre-shutdown bundle/custody drain.

The catalog therefore moves from 42 to **47 distinct use-case families**.

## Why these are not duplicates

### CONSENT versus TRUST / DNA

`UC-TRUST-001` revokes or rotates trust/security credentials. `UC-CONSENT-001` changes whether a particular data scope may still be retained/forwarded/exposed. DNA already provides application privacy/visibility semantics; CONSENT gives a concrete stale-policy workload for propagating monotonic policy generations. It is a technical experiment, not a legal-compliance claim.

### SECADV versus OPS / TRUST

`UC-OPS-001` manages generic node configuration/version/health. `UC-SECADV-001` asks whether a node is actually affected by a vulnerability and should retrieve a specific patch later. SBOM/VEX-like applicability and time-to-security-awareness are the discriminating metrics. It does not replace signed update/recovery engineering.

### SENSORQ versus IOT / QUERY

`UC-IOT-001` pushes/ferries observations. `UC-QUERY-001` searches disconnected metadata catalogs. `UC-SENSORQ-001` moves a bounded request toward sensor/time-series state, executes local aggregation/filtering and returns a compact exact result or reference. The key metric is raw sensor bytes avoided per query/result cost.

### NEED versus TASK / ASSET / SERVICE / EMERG

`UC-TASK-001` coordinates work, `UC-ASSET-001` reserves durable objects, `UC-SERVICE-001` advertises capabilities and `UC-EMERG-001` publishes notices. `UC-NEED-001` reconciles expiring consumable quantities (`NEED`/`OFFER`) with partial fulfillment and double-count prevention.

### DRAIN versus ENERGY / BACKUP

`UC-ENERGY-001` tries to conserve a relay so it remains available. `UC-DRAIN-001` assumes disappearance/shutdown is imminent and asks how to hand off network bundle/custody state before the node is gone. It is not a backup of user files.

## Most promising additions

### 1. UC-SENSORQ-001

Best immediate software/teaching candidate. It gives the existing sensor-ferry family an active request/response mode and directly tests Pollicino's information-minimization principle: carry a query and a few aggregate bytes instead of a large raw history when the application truly needs only the aggregate.

Start with fixed operations (`mean`, `min`, `max`, `count`, `latest`, `anomaly`) and deterministic public/synthetic environmental time series. Do not build a generic SQL engine.

### 2. UC-DRAIN-001

Best infrastructure candidate. Student nodes will eventually be powered off, run low on battery or enter maintenance. A bounded pre-shutdown drain is a concrete stress test for persistent exact chunks, PNB1/PNC1 custody, duplicate suppression, restart and energy-aware scheduling.

Start with `no drain`, FIFO, earliest-deadline, priority and custody/least-replicated baselines. Complex prediction is not justified unless these fail.

### 3. UC-NEED-001

Best new emergency-adjacent field exercise. Synthetic colored tokens/boxes can represent quantities of water/batteries/blankets/robot parts while LoRa carries delayed need/offer/fulfillment state. This creates a tangible application without using real emergency needs or personal data.

Keep matching exact and human-approved first. No operational civil-protection claim is justified.

`UC-CONSENT-001` is strategically important for DNA/student privacy but should remain software/security-governance first. `UC-SECADV-001` is useful for the real Pollicino fleet but must remain separate from automatic firmware execution.

## Software-first experiments

A single synthetic two-day contact trace can exercise all five additions:

```text
morning school hub
  - publish policy generation 21
  - issue harmless advisory ADV-DEMO-12
  - create sensor query Q7
  - publish synthetic NEED/OFFER records
  - seed bundles on a node that will shut down at 18:00

students disperse to logical territorial clusters
  - delayed policy/advisory propagation
  - Q7 reaches sensor/cache and produces aggregate result
  - needs/offers partially match
  - draining node uses final contact to hand off selected custody

home / next morning school
  - rich-link patch reference resolved
  - Q7 result returned
  - fulfillment receipts and policy acknowledgements converge
  - post-shutdown delivery checked
```

Use only pseudonymous/synthetic clusters. Rometta, Spadafora, Saponara, Villafranca, Messina or other province names may label scenarios but never imply measured RF links.

Useful immediate comparisons:

- policy TTL-only versus monotonic signed generations;
- generic update broadcast versus component/version applicability;
- push-all sensor history versus query/aggregate;
- central-only resource matching versus delayed partial-fulfillment reconciliation;
- no-drain versus FIFO/deadline/priority/custody-first drain.

All results remain `MODEL_SYNTHETIC`.

## Related-work anchors

- GDPR Article 7(3) motivates the reality of consent withdrawal where consent is the lawful basis; PollicinoNet still needs an explicit stale-policy model rather than pretending every disconnected node learns the change instantly.
- CISA SBOM/VEX resources provide prior art for component inventory and machine-readable vulnerability applicability; Pollicino should transport only the minimum application state needed and defer patch bytes to rich links.
- TinyDB/acquisitional sensor query processing is prior art for requesting/filtering/aggregating sensor data near acquisition; Pollicino's discriminating factor is delayed physical query/result carriage.
- Humanitarian need/offer matching is established by systems/research such as NeedsList and NARMADA; Pollicino's question is reconciliation under intermittent store-carry-forward.
- DTN architecture explicitly models custody/retention state; DRAIN tests how existing custody can be used before a known node-disappearance deadline.

None of these references establishes performance on the Pollicino student network.

## Physical-evidence boundary

The first required physical gate remains **HW-006** with the frozen sequence:

```text
42-byte frames / 2 dBm
same room
-> greater separation
-> one wall
-> multiple walls / floor
-> outdoor
```

After HW-006, use-case-specific physical work may measure:

- SENSORQ: local compute/energy and query/result byte/airtime break-even;
- DRAIN: battery/brownout trigger, final-contact completion and persistence under sudden power loss;
- NEED: supervised synthetic-token propagation/receipt latency;
- SECADV: signature verification, rich-link patch handoff and safe restart/recovery with harmless test packages;
- CONSENT: signed-policy verification/persistence and measured stale-policy propagation windows using synthetic data.

No use case authorizes changing the PHY or claiming town-to-town coverage, real contact capacity, battery lifetime, privacy compliance, emergency readiness or update safety without the relevant measured evidence and governance.

## Decision

**CONTINUE all five as use-case documents.**

Promote `UC-SENSORQ-001` and `UC-DRAIN-001` as Tier-A software/field candidates after HW-006. Keep `UC-NEED-001`, `UC-CONSENT-001` and `UC-SECADV-001` behind stronger application/security/privacy governance before any real-data or operational use.