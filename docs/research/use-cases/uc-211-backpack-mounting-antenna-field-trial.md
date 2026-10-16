# UC-211 — Paired antenna-mounting field trial

Problem: identical nodes may produce different reception logs when mounted in different positions. Such variability can confound routing comparisons.

Actors: teacher, four to eight boards, two fixed receiver stations and a collector.

Fit: PollicinoNet is a delay-tolerant network whose relay contacts need reproducible measurements.

Bearers: LoRa for synthetic probes, BLE and Wi-Fi for bulk logs, Internet optional, SD or physical carry as fallback.

Software trial: generate paired A/B synthetic observations, missing records and uncertainty labels.

Hardware trial: use fixed approved stations and change one mounting factor at a time while keeping the frozen PHY and antenna configuration constant.

Privacy and safety: temporary experiment identifiers, no participant movement histories, standard radio compliance checks.

Difficulty: medium. Unlike UC-206 device readiness, this isolates mounting effects. No physical results claimed.
