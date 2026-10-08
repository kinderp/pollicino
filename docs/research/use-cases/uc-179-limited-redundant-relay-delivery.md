# UC-179 — Limited Redundant Delivery

**Problem:** Copies carried on identical paths add overhead without much resilience.

**Actors:** source, optional relays, authorized checkpoints, sink, tester.

**PollicinoNet:** store-and-forward can hold separate copies until independent encounters.

**Bearers:** LoRa for small forwarding status; BLE/Wi-Fi for payload; Internet or physical carry when useful.

**Software:** compare one copy, random two-copy and diversity-aware two-copy in synthetic contact schedules. Measure delivery, copies and queue use.

**Hardware:** run controlled exercises with 8–15 boards at public educational checkpoints in Messina province.

**Privacy/security:** temporary IDs, coarse checkpoint labels, bounded copy budgets, no route tracking.

**Difficulty:** high.

**Distinct:** UC-169 scores neighbors; UC-179 constrains the total number and diversity of transport copies. UC-163 studies storage placement.

**Limit:** no PHY modifications or unmeasured range/delivery claims.
