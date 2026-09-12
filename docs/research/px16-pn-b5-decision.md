# PX16 decision

```text
GATE: PX16-PN-B5
CLASSIFICATION: POLLICINO_UNIX_DATAGRAM_TRANSPORT_READY_WITH_LIMITS
CONFIDENCE: HIGH
```

Transport remains a clean replaceable adapter beneath B4. A successful Unix
`sendto()` is not receiver possession; only durable receiver state influences a
future reconciliation. No change was required in D2/D3/D4/B2/B2F/B2C/B2A/B4.

Reliability is not required for correctness before another transport: drop,
buffer pressure, process exit, and timeout all end the current opportunity
safely. Reliability/ARQ may later be evaluated as an efficiency concern.

The smallest next experiment is a materially different real transport family:
a bounded pathname-based `AF_UNIX/SOCK_STREAM` adapter using the existing B4
header length for incremental frame delimiting. This tests connection and
stream behavior without introducing IP, RF, routing, or security.

