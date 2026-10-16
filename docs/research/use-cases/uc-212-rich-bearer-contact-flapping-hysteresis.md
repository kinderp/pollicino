# UC-212 — Rich-bearer handoff hysteresis

Problem: brief LoRa encounters repeatedly trigger BLE or Wi-Fi setup, although contacts end before any useful data are transferred.

Actors: mobile relay nodes, two checkpoint gateways, a test coordinator and six virtual nodes.

Why PollicinoNet: LoRa discovery can precede bulk transfer over a richer bearer. An application-layer state machine can decide when handoff is worthwhile without changing the frozen LoRa PHY or MAC.

Bearers: LoRa for compact discovery; BLE and Wi-Fi for data; optional Internet or carried SD card for the evidence log.

Software now: compare always-connect, fixed-threshold and hysteresis policies on synthetic contact traces. Inject interrupted sessions, duplicate beacons, stale clock information and reboot. Track handshake attempts, verified bytes, expired objects and time to delivery.

Hardware later: four to eight boards with two laptops or Pi gateways. Repeat timed encounters and measure session starts, failures and completed transfers.

Privacy and security: test-only identities, authenticated peers and explicit refusal of unsafe bearer downgrades. A brief urgent control notice must not be silently blocked by the bulk-transfer waiting policy.

Difficulty: medium-high. UC-033 covers secure handoff; UC-188 assesses transfer feasibility. UC-212 addresses unstable repeated handoff decisions. No physical performance claimed.
