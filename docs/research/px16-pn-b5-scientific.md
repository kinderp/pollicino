# PX16 scientific report

```text
GATE: PX16-PN-B5
CLASSIFICATION: POLLICINO_UNIX_DATAGRAM_TRANSPORT_READY_WITH_LIMITS
CONFIDENCE: HIGH
BASELINE: 82ba2e70fe1262f2eac47ab656cd45a304a58a0c
IMPLEMENTATION: e8c02ac5c09ef10909e5a3ffd39963be91f49ddd
```

Pathname-based `AF_UNIX/SOCK_DGRAM` carried one opaque B4 frame per kernel
datagram with zero outer bytes. Two independent workers opened separate durable
roots and sockets. Direct and PASS-relay canonical state matched. The relay was
a third process and interpreted no B2/B4/application semantics.

The actual macOS/Darwin sweep passed at MTU 53, 64, 128, 256, 512, 1024, 1500,
and 4096. The 797-byte capacity-10 message used 797, 67, 11, 4, 2, 1, 1, and 1
datagrams respectively; MTU 53 intentionally has one payload byte per frame.
The 29,245-byte maximum message crossed as 385 datagrams at MTU 128.

Oversize receive used ceiling plus one and accepted zero silent truncations.
Empty, short, malformed, corrupt, foreign-source, missing-destination, collision,
and MTU-mismatch cases failed boundedly. Owned stale socket recovery passed and
unowned paths were preserved. Socket files used mode 0600, which is OS access
control rather than Pollicino authentication.

Duplicate, reorder, and delay through a real relay converged. Whole-datagram
loss produced incomplete B4 state and no native mutation. Compact loss did not
become capacity evidence. Loss during exact fallback preserved only earlier
complete commits, and a fresh contact converged. Receiver crashes before apply
left state missing; crashes after commit preserved durable state and fresh
reconciliation skipped it. The mule carried query and reverse result state.

Observed `SO_SNDBUF` was 2,048 bytes and `SO_RCVBUF` 4,096 bytes. With the
receiver deliberately not draining, 26 128-byte sends succeeded before macOS
returned `ENOBUFS` (errno 55). No retry or Python queue was added. This is a
quantified backpressure limit; repeated contacts still made fair progress.

Baseline was 667 passed, 5 skipped; focused inherited PX13-PX15 was 206 passed.
Final validation was 704 passed, 5 skipped; PX16 focused was 37 passed;
compileall passed. Application/Unix leakage counts above B4 are zero, as are
persistent transport/ACK/fragment state, routing, discovery, and security logic.

The result does not establish UDP/IP, LAN, radio, authentication, stable wire
format, or reliable delivery. Path length/permissions and macOS buffer behavior
remain platform-specific. MTU remains configured rather than negotiated.

