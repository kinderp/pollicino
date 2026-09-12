# PX17-PN-B6 datagram/stream comparison

## Same upper contract

| Property | PX16 Unix datagram | PX17 Unix stream |
| --- | --- | --- |
| kernel interface | `AF_UNIX/SOCK_DGRAM` | `AF_UNIX/SOCK_STREAM` |
| address | filesystem pathname | filesystem listener pathname |
| kernel message boundary | yes | no |
| byte ordering | datagram sequence observed locally | ordered byte stream |
| B4 input/output | one complete frame | one complete frame |
| outer framing | 0 bytes | 0 bytes |
| B4 changes | none | none |
| B2/D4 changes | none | none |
| persistent transport state | none | none |
| ACK/retry | none | none |

The same B4 ceiling sweep (53, 64, 128, 256, 512, 1024, 1500, 4096) and the
same capacity-10 fragment counts passed both families.  The 29,245-byte maximum
B2-family message remained 385 B4 frames at ceiling 128.  Transport selection
did not change fragmentation.

## Canonical equivalence

Independent stream and datagram contacts started from equivalent 10-query
durable states.  Final native state digests matched:

```text
TRANSPORT_FAMILY_CANONICAL_MISMATCHES = 0
```

PX11 exact, PX12 compact, PX13 capacity failure/exact fallback, reference
selection, restart, sender uncertainty, and mule behavior remain above the
adapter boundary.

## Accounting sample

For the deterministic 10-query capacity-10 contact at B4 ceiling 128:

| Direction | B4 frames | B4 bytes | stream bytes | OS writes | OS reads |
| --- | ---: | ---: | ---: | ---: | ---: |
| initiator to responder | 28 | 3,458 | 3,458 | 28 | 5 |
| responder to initiator | 4 | 438 | 438 | 4 | 29 |

OS calls vary with segmentation and are not protocol-message counts.  Stream
bytes equalled B4 bytes exactly.

## Capability conclusion

Evidence justifies a small common frame-transport protocol/interface, not a
large class hierarchy.  Connection orientation and kernel boundary behavior
are adapter-internal for the validated orchestration.  No automatic transport
selection policy or general capability negotiation is justified yet.

## Remaining distinction

Stream correctness depends on ordered, non-corrupt bytes while a connection is
healthy.  B4 itself remains unordered-fragment-safe for message-oriented
transports.  This transport-family distinction did not leak into B4.
