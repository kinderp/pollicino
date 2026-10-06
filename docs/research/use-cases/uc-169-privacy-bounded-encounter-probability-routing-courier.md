# UC-169 — Privacy-Bounded Encounter-Probability Routing Courier

**Problem:** choose useful relays without blind epidemic forwarding or a central detailed mobility graph.

**Actors/nodes:** student relay boards, source, destination/public checkpoint, optional gateway.

**Why PollicinoNet:** repeated opportunistic contacts create local routing evidence; compact decaying reachability scores fit LoRa control while bulk stays on BLE/Wi-Fi/physical carry.

**Software now:** replay contact traces and compare direct-only, epidemic, first-contact and PRoPHET-like forwarding. Measure simulated delivery, delay, duplicate bytes and buffer pressure.

**Hardware:** 8–15 boards on repeated school/public routes. Compare routing policies on the same public test bundles.

**Privacy/security:** no homes, exact trajectories or stable social graphs; use coarse destination classes, local-only score calculation, bounded retention and authenticated score advertisements.

**Difficulty:** **High.**

**Distinctness:** UC-008 observes contacts, UC-040 places replicas and UC-073 plans courier checkpoints; UC-169 makes decentralized per-contact forwarding decisions from local encounter history. RFC 6693 PRoPHET is a baseline, not a performance claim for PollicinoNet.
