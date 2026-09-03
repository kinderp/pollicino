# PX8-PN-D4 FARO conformance

Exact read-only FARO closure:
`43725b2988f24ebad93fbb79f11cbb3d410432aa`. FARO was not modified and no
checkpoint recovery was required.

Production `FAROPollicinoAsyncQuerySource` objects supplied native persistent
D3 and D2 stores to the generic `ContactNode`. Mule C was a plain Pollicino
node, proving that it did not require RegistryQuery knowledge.

Validated flow:

```text
A submit RegistryQuery
→ A-to-C query contact
→ C restart
→ C-to-B query contact
→ explicit B evaluator call
→ B-to-C result contact
→ C restart
→ C-to-A result contact
→ RegistryDiscoveryCandidate visible at A
→ explicit B-to-C and C-to-A D2 selections
→ exact FAROPollicinoReference bytes at A
→ explicit PX1 retrieval
→ FARO verification
→ explicit import
```

Candidate arrival left A's D2 catalog, LocalKnowledgeStore, LocalTrustStore,
and recommendation unchanged. Reference arrival and PX1 fetch still left them
unchanged. Two receiver-local trust stores classified the same signed bytes as
`UNKNOWN` and `REVOKED/BLOCKED`; contact state remained valid. Only explicit
import changed LocalKnowledgeStore.

A zero-match result survived the same mule path and remained local
`ZERO_MATCH_RESULT_PRESENT`, never global completeness. Multiple carriers did
not change evidence or recommendation. A bad signature passed Q, R, selected
D2, and PX1 exact retrieval and then failed at `FARO_AUTHENTICITY` with
`FARO_SIGNATURE_FAILURE`. Compatible operational reference variants remain
fail-closed as `REFERENCE_VARIANT_CONFLICT` at FARO.

Focused PX8 FARO tests: 4 passed. Exact FARO PX7/PX4/PX1 focused regressions: 74
passed. Exact FARO complete test tree: 542 tests and 40 subtests passed.

When those legacy tests are deliberately pointed at the committed PX8 worktree,
PX7 (14/14) and PX1 (20/20) pass. PX4 has 39 functional passes and one expected
checkpoint guard failure because that historical test allowlists only PX3/PX6
Git HEAD values. The same PX4 suite passes on exact PX6 and no PX4 runtime code
was changed.

```text
FARO_CONTACT_CONFORMANCE:
FARO_PX8_CONTACT_CONFORMANCE_READY_WITH_LIMITS
```
