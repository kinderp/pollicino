# PX19-PN-B8 adversarial matrix

| Scenario | Result | Classification |
|---|---|---|
| Two-host environment and route metadata | collected | pass |
| Same clean implementation SHA | yes | pass |
| Host B environment import initially failed | lazy import repaired | A: harness error |
| Host B durable endpoint import | `fcntl` unavailable | M: platform portability limit |
| Host A valid frame to absent Host B port | local send success, timeout | expected missing-peer behavior |
| Direct/reversed query | not run | blocked by M |
| Result/reference | not run | blocked by M |
| Exact/compact/adaptive | not run | blocked by M |
| Fragmentation and registered ceilings | not run | blocked by M |
| Crash/restart/sender uncertainty | not run | blocked by M |
| Peer disappearance/MTU mismatch | not run | blocked by M |
| Physical interruption | not performed | optional |

One inherited PX17 10,000-record stream test exceeded its original 0.45-second
startup horizon during the baseline run. Adding an explicit 2-second horizon
for that registered large case repaired the harness; the full suite then
passed. A first missing-peer diagnostic supplied invalid upper bytes to B4 and
was rerun with a valid inherited compact frame. Neither issue changed protocol
semantics.

No I/J/K/L-class correctness failure was observed because the physical-LAN
endpoint path never became executable. It would be scientifically invalid to
record unrun cases as passes.
