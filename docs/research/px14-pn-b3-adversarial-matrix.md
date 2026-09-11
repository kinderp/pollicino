# PX14 adversarial matrix

| Case | Observed result | Classification |
|---|---|---|
| Lossless independent workers | canonical equality | PASS |
| 1-byte and arbitrary segmentation | identical decode/apply | PASS |
| Concatenated/reordered self-contained records | each applied once, canonical ordering | PASS |
| EOF mid-header/body | deterministic failure, zero mutation | PASS |
| Oversized declared body | rejected after 42-byte header | PASS |
| Corrupt magic/version/type/body | non-zero worker exit, zero mutation | PASS |
| Kill after 90% record | zero mutation after reopen | PASS |
| Hard exit immediately after commit | full record survives; fresh contact skips it | PASS |
| Sender process gone before receiver commit result | fresh reconciliation resolves possession | PASS |
| Compact probe dropped/corrupted | no fallback inferred from transport failure | PASS |
| Capacity-10 delivered failure | initiator receives peer summary and starts exact fallback | PASS |
| Receiver has source set plus extra records | no unintended reverse transfer | PASS |
| Crash during exact fallback | fresh stateless contact converges | PASS |
| Tiny attempt budget | finite partial outcome, no false convergence | PASS |
| Stalled subprocess | coordinator safety timeout returns control | PASS |
| Slow one-byte writes / bounded output | finite completion, no unbounded queue | PASS_WITH_LIMIT |
| Semantic-blind mule | query/result and explicitly selected reference survive restarts | PASS |

Repaired experiment failures were limited to test harness/accounting errors:
an initially impossible 100-record/100-attempt expectation, impairment role
inspection after corruption, an overlarge requested `read_size`, and duplicate
byte accounting. One new worker-direction bug was found and repaired before
closure: a returned summary was initially treated like an ordinary reverse
discovery summary and could pull receiver-only state back to the source. The
initiator role now treats it only as byte-visible equality/failure evidence.
No existing B2 correctness defect or partial-commit behavior was found.
