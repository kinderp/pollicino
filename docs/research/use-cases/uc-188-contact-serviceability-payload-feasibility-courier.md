# UC-188 — Contact Serviceability and Payload-Feasibility Courier

## Idea and problem

A temporal contact between two student boards is **not** proof that a particular object could have crossed it. It may be long enough for a LoRa greeting, but too short for secure rich-bearer setup or for a 4 MB artifact. UC-188 learns the distinction between (a) *a contact was observed*, (b) *a session was usable* and (c) *an exact payload was actually completed*, without inventing capacity from signal strength or a coverage map.

## Actors and nodes

Student-carried LoRa relay/store-and-forward boards, optional phone/laptop/Raspberry Pi BLE–Wi-Fi companions, authenticated school checkpoints, a school-side replay/analysis worker and synthetic virtual contacts.

## Why PollicinoNet

A short **serviceability evidence capsule** can be forwarded across the same delay-tolerant network after the encounter: scoped contact ID, bearer, session outcome, exact object-size bucket, setup duration, verified delivered bytes, interrupted/completed state, observed time-quality and measurement policy version.

`DISCOVERY` records the opportunity; `EXACT` binds measurements to the specific test object and protocol version; `SEMANTIC` produces cautious categories such as 'discovery-only', 'small-object-completed' and 'bulk-capacity-unknown'. A predictive model is **not** a physical result.

## Bearers

- **LoRa:** compact contact/opportunity summaries, test-intent and later result receipts; no change to frozen PHY/MAC.
- **BLE:** controlled small-object and handoff measurements.
- **Wi-Fi/LAN:** controlled bulk transfers with verified byte counts.
- **Internet:** optional aggregation of logged evidence at school.
- **Physical carry:** logs or artifacts travel with a consented device/managed storage when no link exists.

## Software-only experiment now

1. Generate a time-expanded graph with contacts having start/end, setup latency, interruptions and bearer-specific *synthetic* verified-byte capacities.
2. Test fixed payload sizes (e.g., 1 kB / 50 kB / 5 MB): compare 'path exists' against 'object can complete before TTL' under identical traces.
3. Compare optimistic path selection, conservative lower-bound serviceability and no-prediction baselines.
4. Inject false short contacts, zero-byte rich-bearer handoffs, time uncertainty, repeated partial progress (UC-112), unknown measurements and misleading RSSI.
5. Produce confusion matrices for **software-predicted** completability versus the simulator's known ground truth; mark all simulation outputs as simulated.

Example record:
```json
{"trial":"synthetic-07","contact":"opaque-23","bearer":"wifi",
 "object_hash":"sha256:<test-hash>","target_bytes":50000,
 "verified_bytes":31872,"handshake_ms":900,"status":"INTERRUPTED",
 "source":"SIMULATED","time_quality":"BOUNDED"}
```

## Required real-hardware evidence

Use **6–10 existing student boards** and 2–3 authenticated public/school checkpoints, with BLE/Wi-Fi companion hosts if available. Repeat scripted short meetings between nodes across two school-side islands; run small, medium and large test objects with actual hashes. Log setup time, verified bytes, interrupted sessions, real contacts and object completion. Separate contact discovery evidence from rich-bearer evidence. Calibrate predictions **only after** measured trials; report misses and measurement denominators (UC-178). No geographical range or capacity claim without a repeatable trial.

## Messina scenario

One exact Raiatea teaching pack starts at a Messina school node and must reach a Venetico school checkpoint through public/school contacts near Villafranca and Rometta. The path may exist on paper, yet only a manifest or a few chunks may cross each meeting. UC-188 reports which exact representation (UC-141) was serviceable, rather than counting a partial Wi-Fi encounter as full delivery. No home coordinates or individual commuting schedules are required.

## Privacy and security

Experiment-scoped rotating IDs, explicit opt-in for mobility trials, no student names/addresses, locally encrypted detailed logs, coarse public checkpoints, bounded retention. Sign or authenticate trial/result receipts; prevent a participant from falsifying 'completed' status by requiring receiver hash verification. Do not expose private object names or per-student contact calendars.

## Evaluation and difficulty

**Medium–High.** Metrics: measured contact count, setup success fraction with denominator, completed-object fraction by size and bearer, verified bytes per opportunity, simulator calibration error, unknown-observation fraction, duplicate traffic and replay reproducibility. Explicitly distinguish **measurement / estimate / unknown**.

## Why distinct

UC-008 observes contacts; UC-124 selects bearers; UC-128 reserves expected capacity; UC-173 checks temporal reachability; UC-183 compares routing policies fairly. **UC-188 asks whether a specific sized transfer is physically serviceable in the observed contact sequence**, with measured handshake overhead and interrupted payload progress.

Reference: https://www.rfc-editor.org/rfc/rfc9171.html
