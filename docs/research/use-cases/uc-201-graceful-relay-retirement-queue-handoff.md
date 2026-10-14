# UC-201 — Graceful Student-Relay Retirement and Orphan-Queue Recovery

## Problem and concrete scenario
A student loaner node in Venetico is returned to school, breaks, or loses the owner's permission to relay. It may still hold bundles accepted for later forwarding. Simply switching it off loses pending messages; silently exporting everything can breach policy. We need an explicit **retirement state**, a bounded attempt to move permitted bundles to another holder, and an honest outcome for items that cannot be moved.

## Actors / nodes
Volunteer-owned or school-loaned LoRa board; its local queue manager; one or two authorized new holder nodes; school-managed collector; original sender and intended recipient. Suggested supervised route: Messina school cache ↔ Villafranca ↔ Rometta/Venetico, with no need to log students' journeys.

## Why PollicinoNet fits and precise contract
An intermittent network cannot assume every relay remains available. An authenticated `RETIRE_INTENT` carries pseudonymous node epoch, retirement deadline class, queue digest and accepted policy class. A `HANDOFF_OFFER` refers to each exact object hash, size, expiry and eligibility; a new holder can `ACCEPT` only after obtaining and verifying the full object and enough persistent storage. Merely hearing an offer is **not** a successful handoff. Outcomes: `MOVED_VERIFIED`, `EXPIRED`, `UNTRANSFERABLE`, `DESTINATION_CONFIRMED` or `UNKNOWN`. If a node dies suddenly, surviving senders and caches must not infer success; reconciliation uses delayed receipts and retry policy.

## Bearers
- **LoRa:** compact retirement notice, object IDs, offer/accept/refusal and policy epochs if they fit the existing PHY constraints.
- **BLE:** close-range transfer to another authorized node.
- **Wi-Fi/LAN:** exact queued objects and receipt logs to a school cache.
- **Internet:** optional coordination, never required for correctness.
- **Physical transport:** supervised USB/SD handoff with encryption and checksum; no personal device is implicitly trusted.

## Software-only experiment (proposed; not run)
Create six virtual relays with 20 synthetic objects, three sensitivity classes and random contact disruptions. Compare naive power-off, best-effort dump and verified handoff. Inject: receiver out of space, accept-before-write, duplicate acknowledgement, missing sender, crash midway, stale key epoch, privacy-policy refusal, no contacts before retirement. Assert **no falsely successful handoff**, no policy-bypassing export and exact verifiable queue totals. Report lost/unresolved objects, accepted bytes transferred and stale receipts separately.

## Physical test and measurements needed
Start with 4–6 school-owned boards and two laptop/cache endpoints; retire one node while its queue is nonempty. Force a link loss and power-off after partial transfer, recover, verify exact hashes and new-holder durable storage. Collect real contact opportunity, completed bytes, queue recovery fraction, latency and energy only with appropriate instruments. A test that fails to rescue bundles is still valid evidence.

## Privacy, security, difficulty
**Medium–high.** Participation and retirement are voluntary; never require route tracking, home coordinates or publicly visible contribution scores. Private payloads remain end-to-end protected and only pass to eligible holders; erase local plaintext/key material according to the device's verified storage capabilities, without promising secure erasure where impossible. Prevent replay of old `ACCEPT` and keep minimal retention-bounded audit evidence.

## Distinction from existing catalog
UC-095 caps volunteer relay budgets, UC-109 concerns replica retirement, UC-156 group rekeying, and UC-168 custody offers. **UC-201 addresses the end-to-end operational *departure of an entire student relay***, with incomplete queue ownership and honest failure accounting.

## Guardrails
Application-layer work only. Frozen LoRa PHY/MAC untouched. Do not claim delivery, privacy of trajectories, energy saving or coverage without appropriate field measurement.