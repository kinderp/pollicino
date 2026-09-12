# PX18-PN-B7 preregistration

Status: preregistered before production implementation.

`PX18-PN-B7` is the repository-owner candidate identifier derived from the
closed PX17 recommendation. No authoritative replacement identifier exists in
the exact baseline tree. Historical PX3--PX17 evidence will not be rewritten.

## Hypothesis

One complete bounded experimental B4 frame can map one-for-one to one UDP
datagram over explicitly configured IPv4 loopback endpoints. A connected
`AF_INET/SOCK_DGRAM` adapter can remain an opaque replaceable transport beneath
B4 without additional framing, persistent state, ACK/retry, routing,
discovery, authentication, or application semantics.

## Candidate admission

Two models were evaluated before implementation:

- unconnected UDP with `sendto/recvfrom` and adapter-level source comparison;
- connected UDP with `connect/send/recv`.

Connected UDP is selected because a contact already has one explicit peer and
the kernel can filter other source tuples. UDP `connect()` is only default-peer
configuration; it creates no handshake, delivery session, reliability, trust,
or identity. Correctness must not depend on ICMP feedback.

The preimplementation platform probe on macOS 15.7.9 arm64 observed that a
first send to an unused loopback port returned success, while a later receive
reported `ECONNREFUSED`/61. This is diagnostic only and preregisters the weak
meaning of send success.

## Registered implementation

- IPv4 only: `AF_INET/SOCK_DGRAM`, numeric `127.0.0.1`;
- explicit `(address, port)` endpoints; no hostname resolution;
- one B4 frame per UDP payload and one UDP payload per B4 frame;
- configured frame ceiling 53--4096 bytes;
- bounded receive of ceiling plus one byte for truncation detection;
- finite blocking timeout;
- no outer framing, queue, resend, ACK, FEC, PMTU discovery, MTU negotiation,
  broadcast, multicast, routing, discovery, DNS, or NAT support;
- endpoint subprocess sockets may be pre-bound to port zero by the test
  coordinator and inherited solely to eliminate free-port races. This is test
  setup, not discovery or protocol authority.

## Success invariants

```text
UDP_LOOPBACK_CANONICAL_MISMATCHES = 0
THREE_TRANSPORT_CANONICAL_MISMATCHES = 0
SHARED_ENDPOINT_OBJECTS = 0
DIRECT_REMOTE_STORE_READS = 0
UDP_DATAGRAMS_PER_B4_FRAME = 1
B4_FRAMES_PER_UDP_DATAGRAM = 1
UDP_EXTRA_FRAMING_BYTES = 0
SILENT_UDP_TRUNCATIONS_ACCEPTED = 0
PARTIAL_B4_NATIVE_MUTATIONS = 0
FALSE_CONVERGENCE_AFTER_UDP_LOSS = 0
UDP_UNBOUNDED_USER_QUEUE = 0
PERSISTENT_UDP_SESSION_STATE = 0
PERSISTENT_UDP_ACK_STATE = 0
PERSISTENT_FRAGMENT_STATE = 0
APPLICATION_SPECIFIC_UDP_BRANCHES = 0
UDP_SPECIFIC_D4_BRANCHES = 0
UDP_SPECIFIC_B2_FAMILY_BRANCHES = 0
UDP_SPECIFIC_B4_BRANCHES = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

## Falsification matrix

Direct and relayed independent processes; ceilings 53 through 4096; empty,
short, exact-ceiling, oversized, malformed, foreign-source, and corrupt
datagrams; missing/unused destination; bind collision; loss, duplication,
reordering, delay, permanent loss; timeout and receive-buffer pressure; MTU
mismatch; receiver/sender/both-process crash; sender uncertainty; exact,
compact, adaptive fallback, fairness, and mule paths.

## Kill criteria

Stop before adding persistent UDP/session/ACK/fragment state if correctness
requires it. Any partial native mutation, undetected truncation, false
convergence, upper-layer UDP branch, or oracle mismatch falsifies the intended
contract. Reliability, physical path MTU, LAN, routing, discovery, and security
pressure are classified for later gates rather than implemented here.

## Success classification threshold

Passing local evidence requires every hard invariant above and three-transport
canonical equivalence. A successful result remains `WITH_LIMITS` because
loopback supplies no real NIC, LAN, router-path, physical-MTU, Internet, or
security evidence.
