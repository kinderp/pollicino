# UC-013 — Field Report and Evidence Capsules

## Idea

Support **offline, signed field observations** during a civil-protection or school emergency drill. A field node creates a small structured report such as `road blocked`, `water level high`, `building checked` or `sensor alarm`; PollicinoNet moves the compact report through store-and-forward relays. Photos, audio or larger evidence remain exact objects that can be fetched later over a richer bearer.

This is the reverse direction of UC-002's authoritative bulletin: UC-002 disseminates a trusted message *outward*; UC-013 brings observations *back* from disconnected field teams and preserves provenance.

A Messina-area exercise can use entirely synthetic incidents across pre-agreed zones, with student nodes acting as relays between field teams and a school command node.

## Problem solved

After an infrastructure failure, a command point may need many small status updates from disconnected locations. Sending rich media over a scarce link is wasteful, while unstructured text can be duplicated, stale or hard to verify. We need compact, prioritized observations with exact evidence retrievable later.

## Actors / nodes

- field observer/student team;
- student-carried relay nodes;
- school command/aggregation node;
- optional fixed sensors;
- optional Raiatea/provenance store for exact evidence objects.

## Why PollicinoNet fits

PollicinoNet can carry a compact `DISCOVERY`/structured report envelope over LoRa, use TTL/hop limits and duplicate suppression across partitions, and resolve exact evidence later through content-addressed manifests. The scenario exercises delay tolerance and provenance without changing the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact report code, priority, coarse zone, timestamp window, evidence coordinate and acknowledgement;
- **BLE:** nearby team/relay exchange;
- **Wi-Fi/Internet:** exact photos, audio, documents and aggregated map state;
- **physical transport:** a team member or vehicle can carry queued reports/evidence to a connected node.

## What we can test now in software

- synthetic incident generator and field-report schema;
- signed report envelopes with sequence IDs and expiry;
- duplicate/conflicting report handling;
- priority queues for `routine`, `important` and `urgent drill` traffic;
- provenance chain from report to exact evidence hash;
- network partition/reunion simulations;
- command-side aggregation without pretending that multiple reports prove ground truth;
- metrics: report delivery rate, age-of-information, duplicate overhead and evidence-resolution success.

## What requires real hardware

- controlled 3–6 node field drill with synthetic events;
- measured delivery delay, retries and contact-window behavior;
- one report relayed through multiple store-and-forward nodes;
- LoRa report followed by real Wi-Fi/BLE retrieval of an evidence object;
- only after repeated drills, explore collaboration with qualified civil-protection personnel.

This is **not** an operational emergency system until independently validated, hardened and accepted by the relevant authorities.

## Privacy / security

Reports may reveal people, locations or vulnerable infrastructure. Use coarse zones where possible, role-based signing, encryption for sensitive reports, limited retention and strong provenance. A relay must be able to forward an encrypted/signed report without being able to alter it. Do not include real casualty/medical information in school experiments.

## Difficulty

**Medium.** The report/state logic is approachable and highly testable; trustworthy identity, conflict handling and operational safety become harder if the scenario ever moves beyond drills.
