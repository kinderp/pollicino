# PX17-PN-B6 adversarial matrix

| Case | Result | Classification |
| --- | --- | --- |
| lossless independent processes | canonical convergence | pass |
| one-byte read/write | exact frames and state | pass |
| partial header/payload | buffered; EOF fails closed | pass |
| concatenated frames | emitted individually | pass |
| random seed 20260912 | zero segmentation mismatch | pass |
| EOF at boundary | completed frame retained | pass |
| complete frames plus partial final | complete retained; final rejected | pass |
| invalid magic/type/bounds | terminal connection failure | pass |
| payload corruption | CRC rejection | pass |
| deleted stream byte | fail-stop, no resync | pass |
| declared payload over ceiling | rejected after header | pass |
| connection missing/refused | finite transport failure | pass |
| active pathname collision | fail closed | pass |
| unowned/stale pathname | unowned preserved; owned dead recovered | pass |
| peer exits after connect | bounded broken pipe | pass |
| receiver crash before apply | zero native mutation | pass |
| receiver crash after commit | durable record survives | pass |
| sender exit mid-frame | incomplete frame discarded | pass |
| sender exit after record write | receiver durable truth reconciled | pass |
| both processes restart | fresh connection converges | pass |
| blocked writer | finite timeout, zero queue | `L.BACKPRESSURE_LIMIT` |
| slow reader | bounded same-frame completion | pass |
| compact equality/small difference | compact path | pass |
| 100 differences | detected capacity failure, exact fallback | pass |
| compact stream interruption | transport failure, not capacity evidence | pass |
| exact fallback interruption | complete commits only; fresh resume | pass |
| exact 105 records | two finite contacts, zero starvation | pass |
| semantic-blind mule | query/result store-carry-forward | pass |

## Experiment repairs

- macOS rejected pytest's long socket pathname: `A.TEST_HARNESS_ERROR`; tests
  moved to an explicitly owned short `/tmp` directory.
- stale-listener subprocess lacked repository import context:
  `A.TEST_HARNESS_ERROR`; explicit `PYTHONPATH` fixed it.
- 20 differences were assumed to exceed capacity 10, but the closed executable
  sketch decoded that deterministic set: `A.TEST_HARNESS_ERROR`; the registered
  capacity-failure case uses 100.
- one-contact completion was initially assumed for 100 records despite the
  shared finite control/record count: `A.TEST_HARNESS_ERROR`; fresh contacts
  proved bounded convergence.
- a deliberately short 20-message large-state horizon may close while the peer
  is writing the exact batch: `L.BACKPRESSURE_LIMIT`; timeout/broken pipe is
  finite, no false convergence occurs, and no queue/retry was added.

No failure was classified as an existing B4/B2 correctness bug, atomicity
failure, framing extension requirement, persistent-state requirement,
transport-abstraction mismatch, or security requirement.
