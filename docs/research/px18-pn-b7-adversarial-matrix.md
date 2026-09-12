# PX18-PN-B7 adversarial matrix

| Case | Outcome | Classification |
|---|---|---|
| Direct and PASS relay | canonical match | pass |
| 53--4096 ceilings | byte-exact frame/datagram mapping | pass |
| Empty/short/malformed | B4 candidate rejected, no mutation | pass |
| Oversized send/receive | local/bounded rejection | pass |
| Unexpected source | connected-socket filtering; timeout | pass |
| Unused destination | send may succeed; no delivery inference | platform limit |
| Bind collision | setup fails closed | pass |
| Drop/permanent loss | finite incomplete contact, no false convergence | pass |
| Duplicate/reorder/delay | B4 safely converges when complete | pass |
| Corruption | B4 fail-closed | pass |
| Receiver crash before commit | zero mutation; fresh recovery | pass |
| Receiver crash after commit | durable progress retained | pass |
| Sender crash after send | fresh reconciliation resolves uncertainty | pass |
| Both workers restart | durable-state convergence | pass |
| Compact datagram loss | transport failure, not capacity evidence | pass |
| Exact-fallback frame loss | incomplete message not applied | pass |
| Bounded 2,000-send pressure | no Python queue; platform kernel accepted loop | limit |

Two harness assertions were repaired without production changes: the 10,000
record worker needed a longer finite startup horizon, and permanent drop was
correctly asserted as dropping every A-to-B datagram rather than exactly one.
No existing B4 or B2-family fault was observed.
