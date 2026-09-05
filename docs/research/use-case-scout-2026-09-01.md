# PollicinoNet use-case scout — 2026-09-01

Status: research checkpoint; documentation only; no PHY or hardware configuration change

## Repository check

The existing catalog contained 37 distinct use-case families through 2026-08-31. Searches for lost-object finding, battery/energy-aware relay conservation, sensor drift/calibration, RF coverage/site-planning evidence and active-learning review did not find an already formalized use-case family.

This checkpoint adds five new families without changing the frozen H2/PHY contract:

- `UC-FIND-001` — Privacy-preserving lost-object finding ferry;
- `UC-ENERGY-001` — Energy-aware relay conservation;
- `UC-CALIB-001` — Opportunistic sensor calibration ferry;
- `UC-RFMAP-001` — Privacy-bounded RF evidence survey and site planning;
- `UC-ACTIVE-001` — Delay-tolerant active-learning / expert-review ferry.

## Why they are distinct

- FIND is not ASSET/COURIER: the object location is unknown and must be opportunistically detected.
- ENERGY is not OPS: the objective is to protect network lifetime/fairness under relay load, not merely report battery health or push configuration.
- CALIB is not IOT: successful packet delivery can still produce bad measurements; the objective is sensor-quality/calibration-state convergence.
- RFMAP is not TRACE: TRACE records temporal node encounters; RFMAP records controlled RF outcomes at known experiment checkpoints/geometry.
- ACTIVE is not FL/AI artifact sync: it transports uncertain-sample review requests and labels, not model updates or model binaries.

## Top 3 for the Messina educational network

### 1. UC-RFMAP-001

Highest infrastructure value. The future student network needs measured RF evidence before any province-scale placement/routing claim. RFMAP turns HW-006 and later controlled checkpoints into a reproducible evidence/planning workflow while explicitly rejecting continuous student GPS tracking.

### 2. UC-CALIB-001

Best new educational application. Low-cost temperature/humidity/environmental sensors plus one reference checkpoint create a safe, measurable project in which students act as data/calibration mules. It tests provenance, freshness and store-carry-forward while producing a scientifically meaningful metric: calibration error over time.

### 3. UC-FIND-001

Best tangible application demo after privacy governance. A deliberately placed lab object with a BLE beacon can be discovered by student-carried nodes and return a sighting asynchronously over LoRa/physical carry. Start only with synthetic/authorized objects and rotating IDs.

`UC-ENERGY-001` is a strong enabling infrastructure case and should be developed in parallel once real current measurements are available. `UC-ACTIVE-001` is promising but remains software/research-first.

## Software-first experiments

No new hardware is needed to begin:

1. RFMAP: synthetic checkpoint/link matrices, UNKNOWN-aware planning and greedy fixed-site selection; no real coverage interpretation.
2. CALIB: synthetic sensor bias/drift/noise, co-location events and simple offset correction versus hub-only/no-calibration baselines.
3. FIND: synthetic BLE-beacon encounters, rotating IDs, WANT-scoped search, duplicate/replay sightings and delayed return.
4. ENERGY: synthetic per-action energy costs; compare no policy, local reserve threshold, daily relay budget and priority-aware reserve.
5. ACTIVE: toy classifier; compare random review versus uncertainty-threshold review with delayed label return and model-generation checks.

A model result remains a model result even if public town names are used as logical cluster labels.

## Messina scenario shape

Use pseudonymous/logical territorial clusters such as `Rometta-like`, `Spadafora-like`, `Saponara-like`, `Villafranca-like` and `Messina-like` without assuming RF links between them.

```text
morning school hub
  -> sensor/reference state
  -> search tokens
  -> AI review requests
  -> students depart

territorial afternoon
  -> physical carry + opportunistic LoRa/BLE contacts
  -> sensor calibration encounters
  -> lost-object beacon detection
  -> bounded relay work under energy reserve

home / next school phase
  -> Wi-Fi/LAN upload
  -> evidence analysis / review / resolution
```

## Related-work signals

- Privacy-preserving crowd object finding has established prior art (e.g. SecureFind, IEEE TWC 2016, DOI `10.1109/TWC.2015.2495291`) and published privacy analyses of crowd-sourced Bluetooth finding systems.
- Energy-aware DTN/DTWSN forwarding is established prior art; remaining battery and delivery predictability have been explicitly studied in intermittently connected sensor networks (Kang & Chung 2017, DOI `10.1177/1550147717717389`).
- Opportunistic sensor calibration has been studied using co-located mobile sensor encounters (Gosangi et al., arXiv `2006.12381`).
- LoRa/LoRaWAN coverage and gateway placement are active research topics, including 2026 geometry-aware/digital-twin placement work; these studies are methodology only and cannot substitute Pollicino measurements.
- Human-in-the-loop/active-learning edge systems are established; the new Pollicino question is specifically whether delayed query/label carriage is useful under intermittent connectivity.

## Physical evidence gates

Nothing in this checkpoint relaxes HW-006. The first physical campaign remains:

```text
42-byte frames / 2 dBm
same room
-> greater separation
-> one wall
-> multiple walls / floor
-> outdoor
```

After HW-006:

- RFMAP needs supervised known-checkpoint measurements before any coverage/site claim;
- CALIB needs real sensors/reference instrumentation and a separate data-quality/metrology gate;
- FIND needs BLE scan/detection/energy tests and explicit privacy/consent governance;
- ENERGY needs actual idle/RX/TX/sleep/flash/battery measurements before calibrating energy-aware decisions;
- ACTIVE needs on-device inference/handoff energy and latency measurements, separate from RF calibration.

No real Messina/province coverage, battery life, sensor accuracy or application success is claimed here.

## Decision

Add all five families to the living catalog. Prioritize RFMAP and CALIB for the next concrete experiment design; keep FIND field-capable only with privacy-safe synthetic objects; keep ENERGY and ACTIVE software-first until their measurement prerequisites exist.