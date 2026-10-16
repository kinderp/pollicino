# UC-214 — Coastal relay enclosure humidity health

Problem: a coastal relay enclosure may become damp over time. Internal moisture can cause maintenance issues, while an apparent network outage may otherwise be misdiagnosed as a connectivity problem.

Actors: four to six sensor-equipped boards, two enclosure prototypes, indoor and outdoor reference instruments, teacher and collector.

Why PollicinoNet: compact device-health observations can reach a maintenance gateway after an extended period without Internet; richer logs can follow when Wi-Fi or a physical collector becomes available.

Bearers: LoRa for summaries; BLE for local service; Wi-Fi or Internet for histories; USB, SD or physical carry for complete logs.

Software now: generate synthetic internal and external temperature/humidity series with faulty readings, missing intervals and reboots. Distinguish normal, inspect and unknown states. Do not equate a humidity threshold with proven corrosion.

Hardware later: first compare sensors and sealed prototypes using supervised non-destructive tests. Keep powered electronics and batteries protected from water and saline contamination. Consider approved fixed coastal checkpoints only after bench review.

Privacy/security: publish only coarse authorized site IDs and signed diagnostics; no household or participant location histories. Use independent inspections as reference evidence.

Difficulty: medium. UC-197 measures external weather, UC-206 initial board readiness and UC-113 maintenance tickets; this case covers changes inside the enclosure. No corrosion, lifetime or radio results claimed.
