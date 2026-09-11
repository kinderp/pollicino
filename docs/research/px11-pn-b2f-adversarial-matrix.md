# PX11-PN-B2F adversarial matrix

| Adversary | Observation | Classification |
|---|---|---|
| PX10 prefix replay, final item at 10,000 | three fresh contacts, zero commits | B — B2 paging implementation error for the PX11 hypothesis |
| B2F final item at 10,000 | committed; 199/200 received page descriptors already matched | pass |
| late suffix of 1,000 | all committed in 11 contacts | pass |
| alternating and sparse gaps | canonical convergence | pass |
| two-way 1,000 + 1,000 | both directions progressed every contact | pass |
| 1,000 queries + results + selected refs | every category progressed in contact one | pass |
| directory/advertisement loss | no invalid mutation; fresh contact recovered | pass |
| page-request loss | no invalid mutation; fresh contact recovered | pass |
| missing-ID request loss | no invalid mutation; fresh contact recovered | pass |
| complete-record loss | receiver unchanged for that record | pass |
| duplicated directory metadata | idempotent planning and native state | pass |
| duplicated query record | one durable semantic record | pass |
| delayed complete message | bounded delivery, one durable record | pass |
| disconnect | finite report; fresh contact resumed | pass |
| sender uncertainty after commit | next contact sent zero record messages | pass |
| query conflict | `QUERY_CONFLICT`, receiver bytes unchanged | pass |
| corrupt/truncated/unknown B2F envelope | deterministic decode failure, no mutation | pass |
| permanent loss | finite partial outcome, zero false progress | pass |
| restart after every contact | 250 records converged without cursor | pass |
| subprocess restart | 105 queries + 105 results restored | pass |
| paged mule | query/result/reference paths passed with loss, disconnect, uncertainty | pass |
| bounded prefix churn | safe; post-churn static convergence | H — continuous churn limit |
| arbitrary infinite churn | not claimed | H — continuous churn limit |
| high-overlap exact disclosure | fair but expensive | I — disclosure efficiency limit |

Two test-harness contact horizons were initially too low for their registered
25-attempt budget (1,000 queries and 1,000 results). Both showed monotonic
progress and exceeded only the test horizon. They were classified A — test
harness error; the horizons were corrected without changing the protocol.

No D2/D3/D4 correctness bug, persistent-progress requirement, direction
starvation, or category starvation was found.
