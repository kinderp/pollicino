# PX16-PN-B5 preregistration

`PX16-PN-B5` is the repository-owner candidate derived directly from the PX15
decision. No authoritative later identifier exists in the baseline.

## Hypothesis

Complete B4 frames can cross pathname-based `AF_UNIX/SOCK_DGRAM` endpoints
one-for-one. Kernel message boundaries require no outer framing. Local durable
D2/D3 state remains the sole progress authority; OS send success is never a
durable-commit claim.

## Selected model

The adapter owns one filesystem socket path inside an explicitly supplied
directory, has one configured peer path and B4/datagram ceiling, uses a blocking
socket with a finite timeout, and holds no user-space send queue. Receive reads
at most ceiling plus one byte so oversize datagrams are detected rather than
silently accepted. The adapter carries opaque B4 bytes and does not reassemble.

Stale-path recovery is opt-in and requires an adapter-created owner sidecar
whose recorded process is no longer alive. Active collisions and unowned paths
fail closed. Filesystem mode is local OS access control, not authentication.

## Success invariants

```text
REAL_TRANSPORT_CANONICAL_MISMATCHES = 0
SHARED_ENDPOINT_OBJECTS = 0
DIRECT_REMOTE_STORE_READS = 0
DATAGRAMS_PER_B4_FRAME = 1
PROCESS_TRANSPORT_EXTRA_FRAMING_BYTES = 0
SILENT_DATAGRAM_TRUNCATIONS_ACCEPTED = 0
PARTIAL_B4_NATIVE_MUTATIONS = 0
FALSE_CONVERGENCE_AFTER_DATAGRAM_LOSS = 0
PERSISTENT_TRANSPORT_SESSION_STATE_REQUIRED = NO
PERSISTENT_TRANSPORT_ACK_STATE = 0
PERSISTENT_FRAGMENT_STATE = 0
APPLICATION_SPECIFIC_TRANSPORT_BRANCHES = 0
UNIX_DATAGRAM_SPECIFIC_D4_BRANCHES = 0
UNIX_SPECIFIC_B2_FAMILY_BRANCHES = 0
CONCRETE_TRANSPORT_B4_BRANCHES = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

## Kill criterion

Stop before adding durable transport session/ACK state, retransmission, routing,
discovery, authentication, application semantics, or an outer datagram frame.
A partial native mutation or correctness dependency on transport history
falsifies the hypothesis.

