# PX6-PN-D3 scientific report

## Hypothesis

A bounded persistent application-neutral asynchronous query/result primitive can connect application-owned evaluation to native D2 catalog keys without semantic parsing, automatic action or network execution.

## Frozen baseline

Pollicino base `2169489b766f84ad64920fd95cb8c9c075d879d0`; PX5 implementation `cdae923e6084eabe24ce593c7e591bbff68504a5`; FARO conformance `44af3e4f0fbdd4f3373a9d464f54892481f0d891`. The declared baseline was 235 PASS / 2 SKIP.

## Implementation

`query.py` implements bounded immutable opaque query and catalog-key result records, fail-closed duplicate/conflict rules, deterministic canonical state, bounded orphan correlation and exact local reconciliation. `persistent_query.py` composes that state with the extracted PX5 `DualGenerationSnapshotStore`. `persistent_catalog.py` now uses the same helper without changing PX5 format or semantics.

Model A won. It avoids both duplicating key-list semantics in every consumer and conflating discovery intent with D2 reference knowledge. IDs remain caller/responder-owned because Pollicino cannot determine semantic query equality.

## Evidence

Independent A/B/C stores demonstrate offline requester and responder phases, process restart, out-of-order correlation, duplicate loops, two-responder order independence and post-restart convergence. A CONTENT-like evaluator and an exact FARO RegistryQuery test adapter use the same core. FARO positive/zero matching, selected D2 pull, PX1 exact retrieval, explicit import, trust divergence, invalid-signature layering and variant conflict all preserve earlier boundaries.

Representative inherited persistence faults cover pre-replace failure, post-replace fail-stop, truncation, corruption, unsupported version, previous-generation recovery, both-generation corruption, ambiguity and second-writer rejection. The complete PX5 regression remains authoritative for the low-level matrix.

Final results: PX3 focused 43 PASS; PX5 catalog/persistence 55 PASS with FARO optional absent or 67 PASS with exact FARO available; PX6 focused 46 PASS; declared Pollicino suite 281 PASS / 2 SKIP. PX1 over the candidate passed 20/20. The frozen PX4 suite passed 40/40 against its exact PX3 pin; against PX6, all 39 behavioral checks passed and only its intentional `HEAD == PX3` dependency-pin assertion rejected the newer commit.

## Negative results and limits

No stable network format, networking, routing, custody, query authentication, confidentiality, TTL, GC, cancellation, exactly-once execution, ranking or global delivery was established. Persistence remains POSIX-tested, single-writer, full-snapshot and without a concurrent-reader contract. FARO production integration is not changed; conformance uses a test adapter.

## Conclusion

The generic local persistent primitive is correct within those explicit limits. Classification: `POLLICINO_ASYNC_QUERY_RESULT_LOCAL_PERSISTENT_READY_WITH_LIMITS`, confidence HIGH. Next Gate: `RG3-PX7 — FARO RegistryQuery over Native Pollicino Persistent Async Query/Result`.
