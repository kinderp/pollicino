# PX19-PN-B8 scientific report

## Question and result

Could unchanged UDP/B4 cross two physical machines on one real IPv4 LAN?

PX19 prepared and validated the required harness and proved that the two
physical hosts have direct, non-loopback LAN routes. It could not execute the
Pollicino contact because Host B is Windows while inherited durable persistence
imports POSIX-only `fcntl`.

The only honest classification is:

```text
PX19_REAL_LAN_EVIDENCE_PENDING
```

Confidence is high in the blocker and in the absence of qualifying cross-host
protocol evidence. This is not evidence that UDP/B4 failed on the LAN.

## Evidence

- PX18 baseline: 815 passed, 5 skipped, 1 inherited timing failure;
- focused PX15--PX18 baseline: 252 passed;
- corrected implementation: 822 passed, 5 skipped;
- focused PX18/PX19: 59 passed;
- compileall: pass;
- Host A and B: distinct physical machines, distinct IPv4 addresses, clean
  worktrees and the same implementation SHA;
- both routes: physical Wi-Fi, MTU 1500, no loopback/VPN/overlay;
- physical-LAN Pollicino contacts: zero;
- Host A missing-peer diagnostic: one valid 128-byte B4/UDP datagram accepted
  locally, followed by bounded timeout and no delivery inference.

## Implementation finding

Generalizing the UDP adapter required only address validation. B4 and all upper
semantic layers stayed unchanged. The new harness can enforce SHA cleanliness,
record environment/contact counters and create distinct evidence files.

An eager persistence import initially prevented even environment collection on
Windows. Lazy imports repaired that harness error. The actual endpoint still
cannot open its durable root on Windows, and repairing PX5 portability is beyond
the frozen PX19 question.

## Historical validity

PX3, PX5, PX6 and PX8--PX18 remain valid for their tested platforms and scopes.
PX5's newly exposed platform limit does not retroactively falsify its POSIX
evidence. PX12's 128/64 preregistration versus 64/32 executable
fingerprint/checksum discrepancy remains recorded and untouched.

## Frontier

PX19 should be resumed unchanged on a second physical POSIX host. If Windows is
a required deployment target, the smallest separate preceding gate is bounded
cross-platform durable-locking/persistence validation—not a UDP or B4 change.
Discovery, security, Internet, radio and reliability experiments are premature
until the physical-LAN contact exists.
