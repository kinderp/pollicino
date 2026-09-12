# PX16 adversarial matrix

| Case | Result |
|---|---|
| MTU 53/64/128/256/512/1024/1500/4096 | byte-exact kernel roundtrip |
| maximum 29,245-byte B2 message | 385 real datagrams at MTU 128, exact reassembly |
| datagram at ceiling | accepted exactly |
| outgoing/incoming oversize | rejected before send / after ceiling+1 receive |
| empty/short/foreign datagram | bounded rejection, no native mutation |
| missing destination/timeout | finite transport failure |
| active collision/unowned path | fail closed |
| dead owned socket path | safely recovered |
| PASS-only relay | canonical state equals direct path |
| duplicate/reorder/delay relay | converged |
| drop/corrupt compact fragment | no fallback-as-capacity inference |
| loss during exact fallback | only complete commits survive; fresh contact converges |
| permanent loss | finite non-convergence |
| receiver crash before apply | record remains missing |
| receiver crash after commit | durable record survives; fresh contact skips |
| 105 exact records under buffer pressure | fresh contacts converge, zero starvation |
| semantic-blind mule | query and reverse result pass |

Repaired local failures were sandbox denial of AF_UNIX and an attempt-bound
violation (`A.TEST_HARNESS_ERROR`), a relay exit on a departed receiver
(`A.TEST_HARNESS_ERROR`), and a burst assumption beyond observed kernel
buffering (`K.BACKPRESSURE_LIMIT`, retained as bounded partial-contact behavior).

