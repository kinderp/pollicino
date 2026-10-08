# PollicinoNet use-case catalog — addendum 2026-10-08

The [primary catalog](CATALOG.md) currently indexes UC-001–UC-177. This **new addendum** indexes **UC-178–UC-182**; together they cover UC-001–UC-182. The previous [cumulative addendum](CATALOG-ADDENDUM-2026-10-07.md) is retained for historical context.

| ID | Full use-case document | Distinct outcome | Readiness |
|---|---|---|---|
| UC-178 | [Experiment Evidence Completeness and Denominator Audit](uc-178-observation-denominator-missing-log-audit-courier.md) | quantify missing evidence before interpreting measured reliability | software first, then field |
| UC-179 | [Limited Redundant Delivery](uc-179-limited-redundant-relay-delivery.md) | compare bounded diverse transport copies against simpler forwarding | software first, then field |
| UC-180 | [Offline Package Validation](uc-180-offline-package-validation.md) | defer artifact consumption until a valid approval arrives | software first, then safe lab |
| UC-181 | [Minimal Reproducer and Cross-Site Debug](uc-181-minimal-reproducer-cross-site-debug-courier.md) | ferry minimized software failure reproductions between isolated machines | software immediately |
| UC-182 | [Blind-Holdout Edge-AI Evaluation](uc-182-blind-holdout-commit-reveal-edge-ai-evaluation-courier.md) | bind submitted predictions before reference-label disclosure | software immediately |

## Three priorities for the next experiment
1. **UC-178** — improves the scientific validity of all field networking conclusions, by keeping missing logs visible.
2. **UC-179** — directly tests whether a distributed real network gains anything from limited route diversity.
3. **UC-181** — produces a practical, teachable distributed debugging workflow using existing lab laptops.

UC-182 is the strongest AI integrity/research candidate. UC-180 supports safer application-level artifact exchange.

## Cross-cutting constraints
The frozen LoRa PHY and radio drivers are out of scope. LoRa carries compact control when feasible; BLE/Wi-Fi/Internet or physical media carry rich content. Only controlled field measurements support claims about range, packet delivery, energy, contact windows or throughput. Use synthetic/public datasets and temporary exercise identities; never track personal movements.
