# PX17-PN-B6 decision

## Decision

```text
GATE:
PX17-PN-B6

IDENTIFIER_STATUS:
REPOSITORY_OWNER_CANDIDATE_FROM_PX16_CLOSURE_RECOMMENDATION

CLASSIFICATION:
POLLICINO_UNIX_STREAM_TRANSPORT_READY_WITH_LIMITS

CONFIDENCE:
HIGH
```

## Architectural finding

The complete experimental B4 frame remains the replaceable transport unit.
The closed B4 fixed header and payload length delimit frames over
`AF_UNIX/SOCK_STREAM`; no outer bytes were added.  Datagram and stream adapters
coexist beneath unchanged B4/B2/D4:

```text
                    UnixDatagramAdapter
B4 frame ----------|
                    UnixStreamAdapter
```

The minimal `max_frame_bytes`, `send_frame`, `receive_frame`, `close` surface is
now evidence-justified.  A generalized capability hierarchy or automatic
transport selection policy is not.

## Frozen correctness result

```text
TRANSPORT_FAMILY_CANONICAL_MISMATCHES = 0
STREAM_TRANSPORT_EXTRA_FRAMING_BYTES = 0
STREAM_SEGMENTATION_DEPENDENT_B4_FRAMES = 0
PARTIAL_STREAM_FRAME_NATIVE_MUTATIONS = 0
PERSISTENT_STREAM_SESSION_STATE = 0
PERSISTENT_STREAM_PROGRESS_STATE = 0
PERSISTENT_TRANSPORT_ACK_STATE = 0
UNIX_STREAM_SPECIFIC_D4_BRANCHES = 0
UNIX_STREAM_SPECIFIC_B2_FAMILY_BRANCHES = 0
TRANSPORT_FAMILY_SPECIFIC_B4_BRANCHES = 0
APPLICATION_SPECIFIC_STREAM_BRANCHES = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

Connection and write success are not progress.  Durable receiver state remains
the sole later possession authority.

## Limits

The result is local pathname Unix-stream evidence only.  It does not prove
TCP/IP, UDP/IP, LAN, Internet, radio, routing, discovery, authentication,
encryption, stable wire compatibility, reconnect policy, or reliable Pollicino
delivery.  Backpressure can terminate a finite opportunity when the receiver
stops reading; no retry or queue was added.

## Next experiment

No further local Unix transport abstraction gate is justified.  The smallest
new boundary is a bounded UDP/IP datagram adapter with configured loopback
addresses, one complete B4 frame per datagram, truncation/source/address
semantics audited, and no routing/discovery/reliability/security expansion.
This is a candidate experiment only; PX17 does not authorize or implement it.
