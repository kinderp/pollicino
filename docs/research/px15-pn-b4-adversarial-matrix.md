# PX15 adversarial matrix

The registered tests attempted to falsify B4 at codec, process, persistence,
and reconciliation boundaries.

| Case | Required outcome | Result |
|---|---|---|
| exact/one-byte-over/max-size boundaries | byte-exact round trip | pass |
| first/middle/final/multiple loss | incomplete, no apply | pass |
| identical duplicates | idempotent | pass |
| reverse/seeded order | byte-exact round trip | pass |
| conflicting duplicate | fail closed | pass |
| cross-message fragment | fail closed | pass |
| payload/header corruption | bounded rejection | pass |
| truncated frame | bounded rejection | pass |
| unknown magic/version/type | bounded rejection | pass |
| impossible index/count/shape | bounded rejection | pass |
| oversized total length | reject at header | pass |
| receiver crash during reassembly | no native mutation | pass |
| crash after reassembly/before apply | no native mutation | pass |
| crash after durable apply | fresh reconciliation skips record | pass |
| sender disappears mid-message | whole-message loss | pass |
| both sides restart | fresh contact converges | pass |
| compact fragment loss | transport failure, no capacity inference | pass |
| exact-fallback fragment loss | only earlier full commits survive | pass |
| permanent loss | finite non-convergence | pass |
| 105-record exact paging | zero starvation across fresh processes | pass |
| process mule | query/result/selected reference converge | pass |

The test harness relays, drops, duplicates, reverses, and corrupts frames but
does not reassemble protocol messages or calculate missing sets. Reassembly
occurs inside the receiving worker. Fixed deterministic orders replace timing
races.

One implementation defect was found: a duplicate delivered after completion
was initially interpreted as a new incomplete message. Classification:
`C. REASSEMBLY_IMPLEMENTATION_ERROR`. The repair retains only bounded volatile
last-completed identity metadata for the current opportunity. It introduced no
persistent progress authority.

