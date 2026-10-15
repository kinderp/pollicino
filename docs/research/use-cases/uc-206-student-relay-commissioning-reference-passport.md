# UC-206 — Student Relay Readiness Passport

**Problem:** Different board condition, software versions, antennas or storage faults can invalidate field comparisons.

**Nodes:** 4–8 school LoRa boards, teacher, reference station, volunteer relay nodes near approved checkpoints in Messina province.

**Why PollicinoNet:** Compact signed readiness status and evidence hash travels when Internet is absent.

**Bearers:** LoRa for status; BLE for local exchange; Wi-Fi/Internet or physical media for full logs.

**Software test:** Inject incomplete reports and inconsistent equipment profiles; missing evidence means UNKNOWN.

**Hardware test:** Compare actual bench transmission and reception records, battery and storage health.

**Privacy/security:** Pseudonymous IDs; no tracking; signed evidence; follow radio and electrical rules.

**Difficulty:** Medium. Different from UC-062 diagnostics and UC-068 enrollment: this is pre-deployment readiness. PHY unchanged.