# PX18-PN-B7 scientific report

## Question and result

Can unchanged B4 frames cross real UDP/IP between independent processes on
explicit loopback endpoints without upper-layer leakage or delivery state?

Yes, within registered loopback limits. The primary classification is:

```text
POLLICINO_UDP_LOOPBACK_TRANSPORT_READY_WITH_LIMITS
```

Confidence is high. Real kernel sockets, distinct interpreters and roots,
direct and relayed paths, bounds, impairments, crashes, restart, exact fairness,
compact/adaptive paths, mule flow, and three-family equivalence agree.

## Evidence

- baseline: 763 passed, 5 skipped; focused PX15--PX17: 199 passed;
- final: 816 passed, 5 skipped; focused PX18: 53 passed;
- compileall: pass;
- 53--4096 byte B4 ceilings: all pass;
- maximum message: 29,245 bytes, 385 UDP datagrams at ceiling 128;
- direct/PASS relay and three-transport canonical mismatches: zero;
- adapter framing overhead and upper-layer UDP branches: zero;
- silent truncations, partial mutations, starvation, oracle mismatches, and
  undetected false negatives: zero.

A measured 10-query clean contact carried 2,232 B2 bytes as 3,896 B4 bytes and
exactly 3,896 UDP payload bytes in 32 datagrams, committing 10 native records.
Direct and PASS-relay state digests were identical.

## Falsification findings

Connected UDP filtering required no semantic identity. A send to an unused port
succeeded before later platform feedback, directly confirming send success is
weak evidence. Loss and corruption did not cause compact-capacity inference or
partial mutation. No ACK, resend, persistent socket session, or fragment state
was needed. A bounded 2,000-send pressure probe completed on this host; it proves
only a bounded user loop and records kernel behavior, not portable buffer limits.

## Historical discipline and inherited validity

PX3, PX5, PX6, and PX8--PX17 remain valid unchanged. PX12's historical text
still says 128-bit fingerprints/64-bit checksums while its closed executable
uses 64-bit fingerprints/32-bit checksums; PX18 exercises the executable and
does not rewrite history. PX16's previously recorded capacity-status artifact
imprecision also remains documented and untouched.

## Limits and frontier

Evidence is macOS 15.7.9 arm64, Python 3.14.2, IPv4 loopback only. There is no
real NIC, two-machine LAN, physical/path MTU, IP fragmentation, IPv6, DNS, NAT,
routing, discovery, authentication, encryption, or reliable-UDP claim.

No further same-machine transport experiment is justified. The smallest new
boundary is two physical machines on an explicitly configured IPv4 LAN using
the unchanged UDP/B4 adapter, with discovery, routing, security, reliability,
and automatic MTU selection still excluded.
