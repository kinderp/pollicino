# UC-180 — Offline Package Validation

**Problem:** An offline cache may receive a package before its permitted-use state is known.

**Actors:** issuer, carrier, cache, reviewer, application.

**Why PollicinoNet:** small approval records arrive independently from bulky files.

**Bearers:** LoRa metadata; BLE/Wi-Fi files; Internet or physical transport optionally.

**Software:** simulate delayed approvals, expired versions, wrong digests and duplicate notices.

**Hardware:** 4–6 boards and two lab PCs exchanging a benign sample.

**Privacy/security:** validated signatures, purpose-limited access and inert storage.

**Difficulty:** medium–high.

**Distinct:** adds an intake decision gate to UC-076 and UC-165.

**Boundary:** no PHY edits or radio-performance claims.
