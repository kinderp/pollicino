# UC-170 — Offline Security-Algorithm Migration Courier

Study how intermittently connected devices can advertise supported security profiles and receive signed policy updates when a fleet contains mixed hardware generations.

Use LoRa only for compact capability/version metadata; use BLE, Wi-Fi, Internet or managed physical transport for larger update artifacts. Software tests can emulate old/new device capabilities and delayed policy arrival. Hardware tests need 4–6 boards plus laptops/Pi and must measure memory, CPU, serialized message size and energy before any feasibility claim.

Privacy/security: use established standardized libraries and signed policy versions; do not design new cryptographic primitives.

Difficulty: **High**. Distinct from trust revocation, enrollment and group rekey because this case focuses on staged fleet-wide algorithm migration.
