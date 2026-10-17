# UC-216 — Privacy-Reviewed Synthetic Contact-Trace Benchmark Ferry

**Problem.** A student-operated LoRa testbed needs shareable replay traces, but releasing real encounter logs could expose routes and identities. UC-216 generates a documented synthetic benchmark while keeping source records private.

**Actors.** School coordinator, privacy reviewer, 8–12 opt-in test boards, fixed school checkpoints in Messina and Rometta, two lab computers and relay students. Never collect home locations.

**Why PollicinoNet.** A signed generator manifest, approved synthetic trace and replay results can travel store-and-forward between labs. LoRa carries digests and permission status; BLE/Wi-Fi transfers the artificial trace, with Internet or encrypted USB/SD as alternatives.

**Software now.** Generate synthetic contact traces for 12 virtual nodes. Compare routing policies using a held-out synthetic reference. Run linkability tests and reject unsafe releases. Verify generator version, policy, hashes, seeds and publication status under stale/offline approvals. Differentiate simulated from measured outcomes.

**Hardware later.** 8–12 boards at authorized, supervised fixed checkpoints; short voluntary trials. Record completeness of legitimate observations, generate synthetic derivatives locally, and do not publish any per-student traces. Do not infer PDR, range or coverage until measured.

**Privacy/security.** Privacy lead approval, lawful basis to be assessed by the school, data minimization, no student identifiers, no home-school trajectories, explicit retention/release controls, signed manifests and withdrawal handling. Pseudonymization is not guaranteed anonymization.

**Difficulty:** high. Separate from UC-008 observatory, UC-183 routing replay and UC-189 linkability audit: the deliverable here is a privacy-reviewed synthetic dataset that other sites can safely reuse.

Background: https://datatracker.ietf.org/doc/html/rfc9171 ; https://www.edpb.europa.eu/edpb_en
