# UC-183 — Paired Shadow-Routing and Field-Trial Evidence Courier

## The problem
A routing algorithm can appear better simply because it was tested on a busier day, with different students or with better weather. Conversely, a policy replayed against a contact trace may choose a contact that did not actually have enough time/capacity to carry the bytes. We need **fair, auditable comparisons**, not invented counterfactual field successes.

## Actors and concrete Messina scenario
School experiment coordinator, 8–15 opt-in LoRa boards used as relay/store-and-forward nodes, two or three authorized public/school checkpoints (for example Messina, Villafranca, Rometta/Venetico and Spadafora), and an evidence collector. Each fixed test message has a predetermined hash, destination, size class, TTL and expected observation schedule. Students move only along normal, permitted routes; no individual trajectory collection.

## Why PollicinoNet
PollicinoNet has delayed receipts and intermittent contacts. It can carry a very small **trial manifest and per-policy decision digest**, leaving detailed logs to local storage. Compare policies such as direct-only, first-contact, UC-169 probabilistic routing, and UC-179 bounded diverse-copy forwarding.

## Bearers
- **LoRa:** trial ID, policy ID, bundle hash, compact decision/receipt counters and trial-close state, subject to verified payload/radio constraints.
- **BLE/Wi-Fi/LAN:** full contact observations, per-relay decisions and evidence packs; Internet only for later review.
- **Physical carry:** school laptop or removable storage transports large trace archives when no electronic rich bearer is available.

## Software-only test now
Construct a deterministic contact-event simulator with known bandwidth and storage constraints. Run each routing policy on identical input seeds; record delivery outcomes, attempts, copy count, buffer pressure and estimated time-to-delivery. Then introduce an intentionally biased experiment in which one policy sees an easier trace. Produce a report explaining why that apparent gain is invalid. For *shadow mode*, compute alternative forwarding decisions on locally recorded encounters **without transmitting extra packets**; mark any predicted deliveries as simulated/counterfactual only.

## Physical validation required
Run a pre-registered, randomized crossover: at each controlled exercise, swap policy order, keep payloads/destinations/participants as constant as practicable, record schedule deviations and use UC-178 for missing log denominators. On the real nodes measure confirmed application delivery, real contact windows, radio retries if exposed above the frozen PHY, queue occupancy and transmitted bytes. Use multiple repeats; avoid interpreting a single day as a comparative advantage. A shadow policy never proves the radio transfer it did not actually attempt.

## Privacy, safety and security
Rotating trial identities, short retention of coarse checkpoint encounters, opt-in student participation and teacher-controlled data access. Signed/hashed policy manifests and provenance-bound outcomes; never use scores to rank students. Follow actual frequency/duty-cycle/site rules and school permissions. No emergency-service guarantees.

## Difficulty and distinctness
**High.** UC-097 schedules experiments; UC-008 observes contacts; UC-173 checks temporal reachability; UC-178 audits missing evidence; UC-169/179 propose policies. **UC-183 specifically designs paired causal comparisons and separates field measurements from shadow-mode estimates.**

## Acceptance gates
1. Software run detects injected experiment-order bias.
2. Report labels physical, replayed and shadow outcomes separately.
3. Every confirmed delivery links to an exact bundle/policy/evidence manifest.
4. Incomplete logs remain UNKNOWN, never silently dropped.

## References
- DTN reproducible evaluation (DTN-COMET): https://arxiv.org/abs/2501.10006
- DTN Bundle Protocol v7: https://www.rfc-editor.org/rfc/rfc9171
