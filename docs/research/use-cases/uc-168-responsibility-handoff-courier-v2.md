# UC-168 — Responsibility-Handoff Courier

Problem: a relay may receive an object without a clear statement that it will keep that object available for a later hop.

Actors: origin, student relay, next cache, destination and experiment observer.

PollicinoNet fit: compact handoff state and object identifiers can use LoRa, while the object itself moves by BLE, Wi-Fi, Internet or physical transport.

Software test: compare ordinary forwarding with explicit accept/refuse handoff state under limited storage, duplicate messages, delayed receipts and node unavailability.

Hardware test: 4–6 boards plus 2–3 storage hosts using public test files. Measure only observed state and transfer outcomes.

Messina scenario: public course packs or environmental data move between school/public islands through student relays that record whether they accepted temporary storage responsibility.

Privacy/security: use pseudonymous experiment nodes, exact object hashes and bounded retention; avoid detailed route histories.

Difficulty: **Medium–High**.

Distinct from UC-098 forwarding receipts and UC-109 replica retirement: this case focuses on an explicit temporary responsibility handoff.
