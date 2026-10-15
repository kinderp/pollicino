# UC-208 — Accessible Footpath Barrier Evidence

**Problem:** A path may be open but unsuitable for some users due to steps, rough surfaces or a temporary obstruction.

**Actors:** teacher, campus survey teams, school map reviewer, 6–10 LoRa relay boards.

**Why PollicinoNet:** Time-bounded signed observations and reviewer decisions can move between disconnected checkpoints.

**Bearers:** LoRa for status and location cell; BLE/Wi-Fi for measurement sheets; Internet optional; paper or USB offline.

**Software:** Generate a fictitious campus map with conflicting and stale reports. Require review before publication.

**Hardware:** Start with safe mock obstacles indoors; later measure permitted school paths and relay actual reports.

**Privacy/security:** No photos of people or private routes; signed correction records; human review. Never promise official navigation safety.

**Difficulty:** Medium. Unlike UC-049 and UC-122, this models accessibility-specific obstacles and uncertain suitability. PHY unchanged.