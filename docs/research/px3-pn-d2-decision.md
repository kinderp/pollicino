# PX3-PN-D2 decision

## Explicit answers

1. **Is the bounded catalog locally READY?** Yes, as a validated local generic
   primitive.
2. **Where is it?** `src/pollicino/net/catalog.py`.
3. **Does core contain application branches?** No;
   `APPLICATION_SPECIFIC_CORE_BRANCHES = 0`.
4. **Logical-key representation?** Non-empty canonical caller-supplied `bytes`,
   ordered lexicographically, maximum 256 bytes.
5. **Is one opaque reference per key sufficient?** Yes for both fixtures.
6. **Was a generic alternative set required?** No.
7. **Why?** Both callers can canonically encode their alternatives inside one
   opaque value; core comparison/merge rules were not independently justified.
8. **Which PX2 bounds became generic?** 4096-byte references, 10000 items,
   16 MiB model payload, and 100-item exchange pages.
9. **Which did not?** Eight retrieval alternatives remains application-only; a
   new 256-byte key bound was added defensively.
10. **Is state canonical?** Yes, as a versioned local format with sorted entries
    and a SHA-256 body-integrity field.
11. **Is insertion order irrelevant?** Yes, including a separate-process test.
12. **Are duplicates idempotent?** Yes: `NOOP_DUPLICATE`, no growth.
13. **Are conflicts fail-closed?** Yes: `ReferenceConflictError`, no overwrite.
14. **Is failed mutation atomic?** Yes for single and batch operations and every
    tested bound.
15. **Do A/B/C work independently?** Yes; their initial digests differ and no
    backing mapping is shared.
16. **Do equal logical states canonicalize identically?** Yes.
17. **Which strategy won natively?** `RECONCILE_AND_PULL` for discovery of an
    unknown catalog followed by selected delivery. `PULL_SELECTED` is cheaper
    only when wanted keys are already known.
18. **Did it cross the threshold?** Yes: 92.801774% reduction versus the 50%
    preregistration in the 1000/0%/1% target.
19. **Are advanced structures still unjustified?** Yes; exact lists already pass.
20. **Did the FARO-like fixture use the same core?** Yes.
21. **Did the CONTENT-like fixture use the same core?** Yes.
22. **Was FARO scientific logic copied?** No.
23. **Was CONTENT semantic logic copied?** No.
24. **Any PR #52 dependency?** None.
25. **Any network?** None; local method calls only.
26. **Any stable wire protocol introduced?** No. The serialization is classified
    only as `LOCAL_CANONICAL_STATE_FORMAT`.
27. **Does removal affect underlying exact bytes?** No; it only removes a local
    catalog mapping, and a `PollicinoStore` separation test passes.
28. **Does source/provider count influence authority?** No count is stored.
29. **Does the catalog contain application trust?** No.
30. **What exact next Gate is justified?** `PN-D2R — Persistent Bounded Reference
    Catalog Restart/Recovery`.

## Gate result

```text
GATE: PX3-PN-D2
CLASSIFICATION: POLLICINO_BOUNDED_REFERENCE_CATALOG_LOCAL_READY
CONFIDENCE: HIGH

BASE_COMMIT: 750405a4aba86e7335141383396edf84347fc1d8
BRANCH: pollicino/px3-pn-d2-bounded-reference-catalog
IMPLEMENTATION_COMMIT: 5fd578ac54a223892ddaa692119606d9e99d151b

PR52_DEPENDENCY: NONE
NETWORK_USED: NOT_USED_BY_DESIGN
BENCHMARK: NOT_RUN_BY_DESIGN
MODEL_ACCOUNTING: MODEL_PROTOCOL_ACCOUNTING_ONLY

CATALOG_MODULE: src/pollicino/net/catalog.py
CATALOG_SCHEMA_OR_STATE_FORMAT: LOCAL_CANONICAL_STATE_FORMAT
NETWORK_WIRE_FORMAT_CREATED: NO

LOGICAL_KEY_TYPE: bytes
MAX_KEY_BYTES: 256
MAX_REFERENCE_BYTES: 4096
MAX_CATALOG_ITEMS: 10000
MAX_CATALOG_BYTES: 16777216
MAX_EXCHANGE_ITEMS: 100

VARIANT_MODEL: A_SINGLE_OPAQUE_REFERENCE
APPLICATION_SPECIFIC_CORE_BRANCHES: 0
DUPLICATE_RESULT: NOOP_DUPLICATE
CONFLICT_RESULT: REFERENCE_CONFLICT
FAILED_MUTATION_ATOMIC: PASS

STRATEGY_WINNER: RECONCILE_AND_PULL
SUCCESS_THRESHOLD: >=50%
TARGET_RESULT: 92.801774% REDUCTION / PASS
ADVANCED_RECONCILIATION: DEFERRED_NOT_JUSTIFIED

BASE_TESTS: 125 PASS / 2 SKIP
PX3_TESTS: 43 PASS
FULL_TESTS: 168 PASS / 2 SKIP

PRODUCT_FRONTIER: VALIDATED LOCAL GENERIC PRIMITIVE
NEXT_GATE: PN-D2R
```

The final closure commit, clean-worktree result, and post-commit scan results are
necessarily reported after this document is committed.
