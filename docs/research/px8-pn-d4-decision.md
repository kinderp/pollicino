# PX8-PN-D4 decision

```text
GATE:
PX8-PN-D4

CLASSIFICATION:
POLLICINO_BEARER_NEUTRAL_CONTACT_STORE_CARRY_FORWARD_READY_WITH_LIMITS

CONFIDENCE:
HIGH

CONTACT_PROGRESS_MODEL:
EPHEMERAL_SESSION_DURABLE_STATE_RECONCILIATION

CONTACT_RESUME_MODEL:
NEW_CONTACT_RECONCILES_FROM_DURABLE_STATE

CONTACT_PERSISTENCE_REQUIRED:
NO

FARO_CONTACT_CONFORMANCE:
FARO_PX8_CONTACT_CONFORMANCE_READY_WITH_LIMITS

NEXT_GATE:
PX9-PN-B1 — Bearer Adapter Contract and Lossy In-Memory Link Validation
```

Model A is sufficient because the receiver's atomic durable D2/D3 mutation is
both progress and possession evidence. Fresh reconciliation omits committed
records from missing work. Reports can be deleted; no session cursor, ACK, or
custody log contributes to correctness.

The WITH_LIMITS classification records local complete-record method calls,
bounded linear ID scans, POSIX-tested single-writer full-snapshot persistence,
no concurrent-reader contract, and deferred TTL/GC, authentication, routing,
custody, fragmentation, wire protocol, and delivery guarantees. These are
explicit frontier limits, not hidden resume, duplication, bounds, neutrality,
or corruption defects.

## Explicit questions

1. Yes, exact PX6 was the base.
2. No local PX6 recovery was required.
3. Yes, exact FARO PX7 was available.
4. No, FARO was not modified.
5. Model A: ephemeral session with durable-state reconciliation.
6. Atomic durable possession plus idempotent reconciliation proved sufficient.
7. No contact-session state is persisted.
8. Existing persistent D2 catalog and D3 query/result state enable resume.
9. No; deleting ContactReport has no effect.
10. No persistent session cursor is needed.
11. No custody log is needed.
12. Positive item and canonical-entry byte budgets, capped at 100 and 2,606,200.
13. It returns normal `BUDGET_EXHAUSTED`; earlier commits remain.
14. Yes, it can stop after every completed record.
15. Before apply, the receiver is unchanged.
16. After apply, the full record is durable.
17. No, it is not retransferred as missing.
18. Zero already-durable records were retransferred.
19. Yes, sender, receiver, and mule restart between contacts.
20. Yes, a real subprocess restart passed.
21. Yes, Q survives A→C, C restart, C→B.
22. Yes, R survives B→C, C restart, C→A.
23. No, C does not interpret query semantics.
24. Yes, C carries a bounded orphan result.
25. Yes, it correlates only after query arrival.
26. Yes, explicit selection carries D2 reference B→C→A.
27. Yes, logical key and reference bytes are identical.
28. Yes, D2 selection is explicit at every hop.
29. No automatic pull follows result receipt.
30. No package bytes are fetched by contact.
31. No import is performed by contact.
32. No incoming query is executed by contact.
33. Yes, query conflicts fail closed.
34. Yes, result conflicts fail closed.
35. Yes, reference conflicts fail closed.
36. No; quota failure cannot partially apply its record.
37. Yes, partial convergence is a valid outcome.
38. Yes, repeated bounded contacts converge intended shared state.
39. No, tested contact orders produce the same canonical final state.
40. No, contact history changes no record identity.
41. No hop count was introduced.
42. No TTL was introduced.
43. No GC was introduced.
44. Query authentication remains deferred.
45. No routing was introduced.
46. No custody semantics were introduced.
47. No stable wire format was introduced.
48. No fragmentation was introduced.
49. No socket or network code was introduced.
50. No PR #52 runtime dependency exists.
51. Application-specific contact-core branches: zero.
52. Bearer-specific contact-core branches: zero.
53. Yes, exact FARO PX7 passed the mule scenario.
54. Yes, knowledge remains unchanged after candidate arrival.
55. Trust remains unchanged and receiver-local.
56. Recommendation remains unchanged.
57. Yes, explicit D2 transfer works afterward.
58. Yes, explicit PX1 exact retrieval passes.
59. Yes, explicit import passes and is the first knowledge mutation.
60. Yes, invalid signature remains `FARO_SIGNATURE_FAILURE`.
61. No, multiple carriers do not alter scientific evidence.
62. Yes, a synthetic CONTENT-like consumer used the same core.
63. Yes, local bounded store-carry-forward semantics are validated.
64. Remaining limits are the explicit local/persistence/frontier limits above.
65. `PX9-PN-B1 — Bearer Adapter Contract and Lossy In-Memory Link Validation`.
