# UC-187 — Cross-School Reproducible Science Round Courier

## The problem
Students from several schools can perform the “same” practical science experiment yet obtain different results. Without an exact common protocol and provenance, they cannot tell whether the difference comes from calibration, measurement method, environmental conditions, software or late/missing data.

## Actors and Messina scenario
A teacher-coordinator, small teams at approved school/lab checkpoints in Messina, Villafranca, Rometta/Venetico and Spadafora, low-cost safe sensors, one optional reference kit, LoRa relay/store-and-forward nodes and a reviewer. An initial round compares **controlled light intensity at a known lamp distance**, or co-located classroom temperature sensors; it is not a regional climate study.

## Why PollicinoNet
A complete protocol can be pre-positioned by Wi-Fi/physical media. Later, compact `round_id + protocol_hash + sensor/calibration_hash + data_snapshot_hash + run_state` capsules propagate opportunistically. Large time-series data and student lab reports follow by rich bearer. A second school can independently repeat the run even while the Internet is unavailable.

## Bearers
- **LoRa:** signed protocol/round version, short aggregated result and evidence receipt.
- **BLE/Wi-Fi/LAN:** instrument logs, plots, photos of non-personal apparatus and reviewer comments.
- **Internet:** optional final classroom aggregation; **physical:** school device or managed drive for full experiment packs.

## Software-only test now
Publish a machine-readable protocol defining units, sensor placement, warm-up, sampling interval, baseline, validity thresholds and expected output schema. Create three synthetic lab datasets with known offset/drift, protocol mismatches, dropped windows and intentionally altered units. Compare naïve pooled results with provenance-filtered results. Emit `VALID / PROTOCOL_MISMATCH / SENSOR_UNCALIBRATED / INCOMPLETE / NEEDS_REPEAT` with citations to exact input logs.

Metrics: valid independently replicated runs, unexplained deviations, missing evidence, total transferred bytes, reviewer effort, and time to a complete scientifically interpretable round.

## Hardware validation required
6–10 boards (not all need sensors), 2–3 school-owned instruments per location and one reference logger. Start in a single lab with isolated groups, then run at authorized school checkpoints. Move short status via LoRa and raw recordings via BLE/Wi-Fi or a school-managed carried medium. Record actual setup variation, repeatability and contact opportunity; do not claim geographical representativeness.

## Privacy/security
Use anonymized team IDs, no home locations or student performance ranking, signed protocol and immutable raw-data hashes, teacher review and controlled access to student reports. No tracking of relay paths. Avoid unsafe heating/electrical setups, and stay within school permissions and radio rules.

## Difficulty and distinctness
**Medium.** UC-097 evaluates *network* experiments, UC-054 ferries assignments, UC-031 tracks calibration, UC-116 validates citizen-science reports. **UC-187 delivers a reproducible cross-school scientific investigation with predeclared method, evidence-linked discrepancies and independent replication**, using the network as an enabling tool.

## Acceptance gates
1. Two honest groups can interpret one exact protocol without an Internet path.
2. Protocol/version mismatch is flagged rather than merged silently.
3. A late repeat is tied to the original round and never rewrites raw results.
4. Physical repeatability findings are clearly separated from transfer performance.
