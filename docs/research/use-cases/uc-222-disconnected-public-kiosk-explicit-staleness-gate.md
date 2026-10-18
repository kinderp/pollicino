# UC-222 — Disconnected Public Information Kiosk with Explicit Staleness Gate (Drill Only)

## Problem and practical value
An offline screen in a school entrance can continue showing an outdated notice after a newer cancellation reaches only another node. Ordinary caching may deliver old text perfectly. The new problem is **what the human-facing display is allowed to show when authority, freshness, or clock confidence is missing**, rather than how messages are routed.

## Actors and province scenario
One teacher-authorized fictional exercise publisher, a supervised public-display PC/e-paper emulator at a school checkpoint, 4–6 student relay boards, optional second display at a Villafranca/Rometta laboratory, and a safety reviewer. A fictitious "EXERCISE ONLY: entrance B closed" notice is created, updated and cancelled across a partition. A late relay cannot cause the original sign to reappear as current.

## Why PollicinoNet and bearer mapping
A tiny signed manifest can be forwarded through intermittent relay contacts long before a replacement image or multilingual notice. Local display policy should use explicit states: VERIFIED_CURRENT, STALE_VISIBLE_WITH_LABEL (non-safety content only), EXPIRED_HIDE, CANCELLED_HIDE, CLOCK_UNCERTAIN_HIDE, CONFLICT_HOLD, and UNVERIFIED_HOLD. Design must not assume synchronized student clocks.
- **LoRa:** signed notice ID, issuer, version/epoch, update/cancel reference, validity evidence and display-state hint.
- **BLE:** short approved text and full signed metadata.
- **Wi-Fi/LAN:** image/multilingual accessibility asset and management logs.
- **Internet:** optional official publisher sync in the lab, never essential to test logic.
- **Physical carry/QR:** manifest/replacement signage only under supervised experiment conditions.
No frozen LoRa PHY/MAC change; exact signatures and supersession references outrank presentation labels.

## Software-only experiment (proposed, not executed)
Implement a tiny kiosk UI simulator with fictional EXERCISE messages:
1. initial authorized notice;
2. update;
3. cancellation arrives before original;
4. old relay brings original after cancellation;
5. network remains down beyond expiry;
6. reboot erases RTC confidence;
7. contradictory same-epoch signed notices;
8. incorrect or unsigned language derivative.
Assertions: display never silently presents superseded/unknown-time drill content as current; cancelled notice remains hidden when an older copy returns; conflict and uncertain time are explicit; the UI never hides its EXERCISE watermark. Count erroneous-current displays and time spent in safe fallback, not imagined public-warning coverage.

## Real hardware
Use 4–6 boards, one Raspberry Pi/old laptop with display and two controlled lab islands. Schedule reconnects, unplug Internet, reset device clock, recover the full event log later. Measure actual propagation and kiosk state after each physical contact. Any extension to genuine public warnings would require independent legal/operational approval and safety validation; this UC is **not** a civil-protection alert system.

## Privacy, security and difficulty
**Medium-high.** Authenticate the specific publisher and cancellation authority; prevent replay/epoch rollback; fail visibly closed for exercise safety notices; provide large accessible text and a manual local emergency-off control. Do not collect who looked at the display. Do not advertise live emergency instructions from student experiments.

## Nonduplication check
UC-132 defines authoritative message update/cancel ordering; UC-107 defines object-cache freshness; UC-106 produces translations; UC-200 runs a drill. UC-222 tests the **last-meter human display policy and visible safe fallback**, especially after reboot/unknown time.
