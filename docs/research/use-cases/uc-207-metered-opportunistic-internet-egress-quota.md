# UC-207 — Shared Gateway Data Budget

**Problem:** Temporary connectivity at an educational checkpoint has a limited data allowance. Duplicate uploads waste capacity.

**Actors:** 4–6 relay boards, school cache, authorized gateway, remote data store.

**Why PollicinoNet:** Offline requests include object hash, estimated size and permission; a later verified receipt records completion.

**Bearers:** LoRa for status; BLE and Wi-Fi for bulk; Internet at a gateway; teacher-managed USB fallback.

**Software:** Simulate two disconnected gateways, quotas, delayed receipts and retries.

**Hardware:** 4–6 boards, laptop and local data-meter emulator. Measure actual transferred bytes and completed objects.

**Privacy/security:** Authorized destinations, signed decisions, no personal student hotspots or public identity logs.

**Difficulty:** Medium-high. Unlike UC-088 and UC-095, this accounts for shared Internet allowance. No PHY changes.