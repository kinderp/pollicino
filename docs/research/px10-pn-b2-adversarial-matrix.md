# PX10-PN-B2 adversarial matrix

| Experiment | Result | Failure classification |
|---|---|---|
| lossless equivalence with PX8 | canonical states equal | none |
| advertisement loss | no mutation; later contact succeeds | none |
| request loss | no mutation; later request succeeds | none |
| complete-record loss | no mutation; later contact succeeds | none |
| duplicate advertisement | bounded duplicate requests; native state unique | none |
| duplicate request | bounded duplicate records; native state unique | none |
| duplicate query/result/reference record | native NOOP duplicate | none |
| sender uncertainty after commit | restart; zero record retransfers | none |
| stale advertisement omitting new state | old subset safe; fresh contact completes | none |
| request/record before advertisement | safe because messages are self-contained | none |
| bit-corrupt metadata | decode error; no mutation | none |
| bit-corrupt complete record | decode error before native apply | none |
| truncated message | decode error; no mutation | none |
| unknown magic/version/type | deterministic decode error | none |
| valid false digest for known identity | native conflict category; no mutation | none |
| query/result/reference conflict | fail closed; no overwrite | none |
| receiver quota after one commit | exact bounded error; first commit durable | none |
| disconnect after one commit | restart resumes missing work | none |
| permanent metadata/record loss | finite partial result; never convergence | none |
| directional asymmetry | one flow may progress; both states remain valid | none |
| control/record/total budgets | independently enforced | none |
| 105 queries + 105 results | 3 contacts/restarts; all 210 exact | none |
| A–C–B / B–C–A mule | loss, uncertainty, disconnect, restart pass | none |

One test initially matched the wrong native `QueryConflictError` text. The
implementation already failed closed. This was
`A. TEST_HARNESS_ERROR`; only the assertion changed.

The PX9 record-object bearer cannot itself represent control bytes. Adding a
B2-local complete-message adapter while retaining PX9 impairment actions is a
resolved `C. B1_ADAPTER_INTEGRATION_ERROR`, not a change to PX9 semantics.

No category D, E, F, G, or H failure occurred in the registered matrix.
Real I/O, authentication, fragmentation, clocks, private discovery, and
scalable reconciliation remain category I future work.

## Falsification boundary discovered

Exact full-page scans are linear. Fresh contacts restart enumeration from the
first sorted page. At extreme native state sizes, the 100-attempt contact bound
can repeatedly consume all work on early advertisement pages and starve later
pages or categories. The required 105+105 experiment converged, but general
fair multi-page scheduling is not proven. This is recorded as a new B2
scalability/fairness limit, not hidden by a larger attempt sentinel.
