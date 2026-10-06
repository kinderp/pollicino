# UC-171 — Coastal Water-Quality Cross-Validation Courier

**Problem:** low-cost field sensors can be noisy, while a trusted reference or lab result may arrive much later.

**Actors/nodes:** field sensor, student sampling team, relay, reference station/lab, evidence collector.

**Why PollicinoNet:** sample ID, sensor summary, uncertainty and status fit LoRa; full time series and photos use Wi-Fi; an optional teaching sample can move physically.

**Software now:** simulate delayed reference results, sensor drift, disagreement, missing samples and wrong calibration versions. Track FIELD_ONLY, REFERENCE_PENDING, CROSS_VALIDATED and DISAGREES.

**Hardware:** start on a tabletop with safe prepared samples and low-cost temperature/conductivity/turbidity or pH sensors; later use only authorized public sites.

**Messina scenario:** several public coastal/stream checkpoints keep local histories while student relays ferry summaries and later evidence back to school.

**Privacy/safety:** use coarse public site IDs and never treat an educational reading as drinking-water or public-health certification.

**Difficulty:** **Medium–High.**

**Distinctness:** combines delayed environmental reference validation with sensor data and optional physical sample transport; it is narrower than generic sensor collection or citizen science.
