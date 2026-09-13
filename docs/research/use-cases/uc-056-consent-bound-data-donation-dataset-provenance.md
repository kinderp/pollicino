# UC-056 — Consent-Bound Data Donation and Dataset Provenance Courier

## Idea

Let people or sensor owners **donate selected data for a declared research/teaching purpose** even when connectivity is intermittent, while carrying the consent scope and provenance together with the contribution.

The important object is not just `data.bin`. It is something closer to:

```text
Contribution
  data_hash
  contributor_pseudonym
  purpose = microclimate_teaching_2026
  allowed_fields = temperature, humidity
  coarse_area = yes
  exact_home_location = no
  expires / withdrawal_epoch
  provenance
```

A relay may carry encrypted bytes without becoming entitled to inspect or reuse them.

## Problem solved

Crowdsensing and AI/data projects often treat collection as the easy part and consent/governance as paperwork outside the system. In a delay-tolerant network that is dangerous: data and permission state may arrive at different times, and a withdrawal may propagate after a contribution has already been copied.

UC-037 gathers privacy-safe environmental measurements and UC-032 handles active-learning labels. UC-056 focuses on a more general question:

> how can a dataset ingest pipeline know **why this exact contribution may be used, for which purpose, and under which current consent state** when updates travel asynchronously?

## Actors / nodes

- consenting contributor or sensor owner;
- student relay/store-and-forward nodes;
- school/research ingest node;
- dataset curator;
- optional Raiatea provenance/documentation node;
- optional UC-019 trust/status source;
- optional UC-020 time-checkpoint source.

## Why PollicinoNet fits

Consent/provenance metadata is compact while the donated artifact may be large.

- **DISCOVERY:** `contribution available`, `consent-status update available`, `dataset needs contributions of class X`;
- **EXACT:** contribution hash, grant ID/version, purpose, allowed data fields, retention class, contributor key/pseudonym and provenance chain;
- **SEMANTIC:** descriptive research labels, never a substitute for the exact grant/policy state.

LoRa can move contribution manifests and consent-state revisions. BLE/Wi-Fi/physical carry can move images, sensor batches or other large data. The ingest node accepts bytes only after checking the exact authorization/provenance state it knows.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** contribution manifest, consent/grant ID, scope digest, withdrawal/status update, dataset need and compact receipt;
- **BLE:** nearby opt-in contribution transfer;
- **Wi-Fi/LAN:** full sensor/image/text batches and dataset synchronization;
- **Internet:** optional authoritative consent/status synchronization and remote archive;
- **physical transport:** encrypted contributions and consent updates carried by student nodes between disconnected groups.

## What we can test now in software

Use only synthetic/public data and synthetic contributor identities at first.

Implement:

- immutable `DataContribution` bound to an exact hash;
- versioned `DonationGrant` with purpose, allowed fields, retention and expiry;
- delayed contribution arriving before the grant;
- grant arriving before the contribution;
- withdrawal/status update racing with ingest;
- strict `accepted`, `quarantined`, `rejected`, `withdrawn-for-future-use`, `status-unknown` states;
- dataset manifest listing every accepted contribution and its grant version;
- derivative dataset/version lineage;
- duplicate contribution suppression;
- contributor-side redaction before transfer;
- purpose mismatch negative test;
- expired/stale grant negative test;
- malicious relay altering metadata or swapping payloads;
- metrics: contribution-to-ingest delay, quarantined time, stale-consent exposure window, metadata bytes and provenance-completeness rate.

A key invariant is:

> possessing the bytes is not the same as having permission to ingest or reuse them.

The first prototype should also make one limitation explicit: a later withdrawal can stop future processing and mark lineage, but it cannot magically erase an already published irreversible derivative. Policy for derivatives must therefore be explicit rather than promised away.

## What requires real hardware

- 4+ LoRa nodes;
- harmless opt-in sensor/photo/text contributions;
- one contributor group disconnected from the ingest node;
- one moving relay;
- a real consent/status update that overtakes or lags the payload;
- rich-bearer transfer of the full contribution;
- measured time until ingest sees both exact data and usable grant state.

For student experiments, use synthetic identities and non-sensitive data. Do not collect health, biometric, precise-home-location or other sensitive personal data merely to test the network.

## Messina teaching scenario

Run a voluntary **microclimate teaching dataset** using only coarse public zones such as `school`, `Rometta/Venetico`, `Spadafora` and `Villafranca`.

Students may opt in to contribute temperature/humidity readings from school-controlled sensors. Their node carries an exact contribution manifest plus a narrow grant saying that those measurements may be used only for the class dataset. A relay later transports the encrypted batch.

In a second exercise, one synthetic contributor changes the grant before the payload arrives. The class checks whether the ingest node quarantines/rejects the stale-purpose contribution rather than silently using it.

## Privacy / security

This use case is primarily about governance and therefore needs stricter rules than ordinary telemetry.

- opt-in only for real people;
- use synthetic participants for protocol testing;
- minimize collected fields before transport;
- keep precise identity/location mapping separate from dataset IDs;
- encrypt payloads for the authorized ingest node;
- authenticate grant/status updates;
- treat consent status as versioned/freshness-sensitive;
- do not broadcast human-readable research interests or sensitive categories over LoRa;
- preserve audit/provenance without creating a permanent movement history;
- apply institutional/legal review before any real research involving minors or sensitive data.

## Difficulty

**High.** Transport is simple; correct consent lifecycle, delayed withdrawal, lineage and data minimization are the hard parts.

## Research / policy signal

The EU Data Governance Act created a framework for trusted data sharing and explicitly includes voluntary **data altruism** for objectives of general interest such as scientific research and climate-related goals. Separately, OGC SensorThings STAplus was developed for citizen-science scenarios where observations may be owned by different users. These are useful governance/model signals; PollicinoNet should still keep its first experiment small, synthetic and purpose-limited.

References:

- https://digital-strategy.ec.europa.eu/en/news/european-strategy-data-data-governance-act-becomes-applicable
- https://data.europa.eu/en/news-events/news/data-governance-act-became-applicable-24-september
- https://ogcapi.ogc.org/sensorthings/
