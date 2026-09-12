# PX18-PN-B7 decision

## Decision

```text
GATE:
PX18-PN-B7

IDENTIFIER_STATUS:
REPOSITORY_OWNER_CANDIDATE_FROM_PX17_CLOSURE_RECOMMENDATION

CLASSIFICATION:
POLLICINO_UDP_LOOPBACK_TRANSPORT_READY_WITH_LIMITS

CONFIDENCE:
HIGH
```

## Architectural finding

Moving from Unix paths to UDP/IP tuples required no semantic change above the
adapter. B4 remained byte-for-byte unchanged and mapped one complete frame to
one UDP datagram. The same minimal transport contract now works over Unix
datagram, Unix stream, and UDP/IP loopback:

```text
                         Unix datagram
B2... -> B4 -> adapter -- Unix stream
                         UDP/IP loopback
```

The minimal generic transport adapter contract is evidence-justified. A larger
capability hierarchy or adaptive transport policy is not.

## Frozen result

```text
UDP_LOOPBACK_CANONICAL_MISMATCHES = 0
THREE_TRANSPORT_CANONICAL_MISMATCHES = 0
UDP_DATAGRAMS_PER_B4_FRAME = 1
B4_FRAMES_PER_UDP_DATAGRAM = 1
UDP_EXTRA_FRAMING_BYTES = 0
SILENT_UDP_TRUNCATIONS_ACCEPTED = 0
PARTIAL_B4_NATIVE_MUTATIONS = 0
FALSE_CONVERGENCE_AFTER_UDP_LOSS = 0
PERSISTENT_UDP_SESSION_STATE = 0
PERSISTENT_UDP_ACK_STATE = 0
PERSISTENT_FRAGMENT_STATE = 0
UDP_SPECIFIC_D4/B2/B4_BRANCHES = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

## Limits and next experiment

Loopback is not a LAN. PX18 proves neither a real NIC/path nor physical MTU,
PMTU, routing, discovery, authentication, reliability, NAT, or Internet
behavior. UDP send success remains only local-kernel acceptance.

Further same-machine transport work is not justified. The smallest
evidence-driven next gate is an explicitly configured two-physical-machine
IPv4 LAN experiment reusing the exact UDP/B4 adapter. PX18 does not implement
or authorize that gate.
