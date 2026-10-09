# UC-185 — Survey Effort and Negative-Observation Courier

## The problem
A sensor reporting *no event detected* is not the same as a site that was never observed. A missing report is also not a zero. For environmental and citizen-science data, confusing absence, non-detection and no observation can produce a misleading map.

## Actors and provincial field scenario
Student sensing teams, school-owned light/temperature/beacon detectors, two or three authorized coarse public/school observation sites, intermittently connected LoRa relay nodes, a data-quality worker and a teacher/reviewer. First task: detect (or explicitly fail to detect) a harmless periodic test LED or beacon in a defined observation window; later extend to non-sensitive citizen-science protocols.

## Why PollicinoNet
A compact capsule can distinguish:
- `POSITIVE_OBSERVATION` — an event was observed;
- `SURVEYED_NOT_DETECTED` — a **defined and actually executed** observation protocol found nothing;
- `NOT_SURVEYED` — no observation occurred;
- `INSTRUMENT_INVALID` — sensor/self-test failed;
- `UNKNOWN` — logs/evidence are missing.

Each record binds site class, protocol/version, observation window and clock quality, instrument health, sampling effort (number/duration of samples), observer authorization and evidence digest. Never infer “definitely absent” from one non-detection.

## Bearers
- **LoRa:** short authenticated status, protocol and window IDs, effort count, evidence hash.
- **BLE/Wi-Fi/LAN:** sample logs, site notes, calibration provenance and optional safe images.
- **Internet/physical carry:** later science archive reconciliation or teacher review.

## Software-only test now
Generate ground-truth event windows, observation schedules and deliberately imperfect detection probabilities. Distinguish cases with a missed event, genuinely absent event, broken detector, duplicate report and entirely missing site logs. Compare a naïve analysis (“every missing/zero means absent”) with a protocol-aware estimate that keeps non-detection and missingness distinct. Metrics: false absence assertions, unknown fraction, coverage of valid effort windows and fraction of observations linked to usable evidence.

## Physical validation required
4–6 boards plus safe LED/light or reed-switch fixtures and one reference logger. Alternate known event-present and event-absent periods under a teacher-controlled schedule; intentionally interrupt a sensor and a relay. Compare received reports with the reference schedule. Report detection performance only for this **specific instrument and experiment**, not for environmental hazards or wildlife populations.

## Privacy and security
Use coarse authorized school/public location names, no home positions, student movement histories, face/audio capture or sensitive species/location records. Authenticated measurement protocol, signed device health claims when feasible, retention limits and separation of measurement from interpretation.

## Difficulty and relation to existing work
**Medium.** UC-116 covers verification of submitted citizen-science observations; UC-131 repairs missing *time-series intervals*; UC-178 audits missing experimental logs; UC-022 corroborates events. **UC-185 adds a scientifically explicit negative observation with measured survey effort and imperfect detection.**

## Acceptance gates
1. Three distinct outcomes `SURVEYED_NOT_DETECTED`, `NOT_SURVEYED`, `INSTRUMENT_INVALID` survive all merges.
2. Duplicate or late survey capsules do not overwrite newer verified windows.
3. Evidence uncertainty is retained after store-and-forward.

## Reference
Imperfect detection and structured sampling in citizen science: https://arxiv.org/abs/2412.15559
