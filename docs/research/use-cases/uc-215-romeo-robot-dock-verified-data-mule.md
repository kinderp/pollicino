# UC-215 — Romeo verified dock-and-handoff data mule

Problem: a robot reaching a checkpoint does not prove that the stored object was transferred or accepted by the next custodian.

Actors: Romeo rover, two disconnected laptop or Raspberry Pi stations, two to four LoRa boards, and a supervised test observer.

Why PollicinoNet: physical motion bridges disconnected islands. Object identity, integrity verification, explicit receipt and durable queue state are independent of the moving bearer.

Bearers: LoRa only for compact appointment/status messages; BLE or Wi-Fi for full transfer; local storage physically carried by the rover; optional Internet for later report upload.

Software now: model appointment, arrival, authentication, transfer, verification and acceptance states. Inject missed dock, partial transfer, stale token, wrong digest, receiver restart and duplicate receipt. Accept custody only after verified complete reception.

Hardware later: start with Romeo stationary and manual repositioning between two benches. Progress to slow supervised laboratory movement with independent stop control. Log arrivals, session setup, verified bytes and final receipts separately.

Privacy/security: synthetic payloads, no personal imagery or tracking. Robotics safety stays under direct local control; delayed DTN messages must not be relied on for emergency stopping or active collision avoidance.

Difficulty: medium-high. UC-005 covers vehicle transport and UC-010 robot tasks; this case tests a physically completed, verified station handoff. PHY frozen; no field reliability claims.
