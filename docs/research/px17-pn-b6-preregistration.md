# PX17-PN-B6 preregistration

Status: preregistered before the PX17 production implementation.

`PX17-PN-B6` is the repository-owner candidate identifier derived from the
closed PX16 recommendation.  The exact PX16 tree contains no later
authoritative identifier.  Historical evidence is not rewritten.

## Hypothesis

The existing experimental B4 frame header contains sufficient length
information to delimit complete B4 frames over an ordered byte stream.  A
bounded pathname-based `AF_UNIX/SOCK_STREAM` adapter can therefore carry B4
frames between independent processes with no additional outer framing and no
persistent transport-session or progress state.

The stream layer is only:

```text
bytes <-> complete bounded B4 frames
```

B4 remains responsible for fragment validation and B2-message reassembly;
B2/B2F/B2C/B2A and native D2/D3 remain unchanged.

## Registered implementation model

- filesystem-path `AF_UNIX/SOCK_STREAM`;
- one connection for one bounded contact opportunity;
- blocking sockets with finite connect/accept/read/write deadlines;
- existing 52-byte B4 header plus its payload-length field for delimiting;
- no outer stream envelope and no stream resynchronization scan;
- bounded same-opportunity completion of a short OS write, never protocol
  retransmission;
- at most one incomplete B4 message per direction, inherited from PX15;
- no persistent parser, connection, reassembly, ACK, retry, or peer state;
- client/server addresses are transport addresses, never peer/trust identity.

## Success criteria

```text
TRANSPORT_FAMILY_CANONICAL_MISMATCHES = 0
SHARED_ENDPOINT_OBJECTS = 0
DIRECT_REMOTE_STORE_READS = 0
STREAM_TRANSPORT_EXTRA_FRAMING_BYTES = 0
STREAM_SEGMENTATION_DEPENDENT_B4_FRAMES = 0
PARTIAL_STREAM_FRAME_NATIVE_MUTATIONS = 0
UNBOUNDED_STREAM_ALLOCATION = 0
UNBOUNDED_STREAM_RESYNC_SCAN = 0
STREAM_UNBOUNDED_USER_QUEUE = 0
PERSISTENT_STREAM_SESSION_STATE = 0
PERSISTENT_STREAM_PROGRESS_STATE = 0
PERSISTENT_TRANSPORT_ACK_STATE = 0
UNIX_STREAM_SPECIFIC_D4_BRANCHES = 0
UNIX_STREAM_SPECIFIC_B2_FAMILY_BRANCHES = 0
TRANSPORT_FAMILY_SPECIFIC_B4_BRANCHES = 0
APPLICATION_SPECIFIC_STREAM_BRANCHES = 0
FALSE_CONVERGENCE_AFTER_STREAM_FAILURE = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

## Falsification priorities

The experiment will actively attempt to falsify the model with partial
headers and payloads, concatenated frames, one-byte reads/writes, deterministic
segmentation, EOF at and inside frame boundaries, invalid lengths/magic,
corruption and deleted-byte desynchronization, partial writes, backpressure,
timeouts, process crashes, adaptive compact/fallback interruption, restart,
fair exact transfer, and semantic-blind mule exchange.

An invalid header or desynchronized stream terminates the current opportunity;
the adapter will not scan for magic.  A transport interruption is not compact
capacity evidence and cannot trigger PX13 fallback on that basis.

## Decision thresholds

Passing requires all hard correctness invariants above, complete B4 roundtrip
at ceilings 53, 64, 128, 256, 512, 1024, 1500, and 4096 bytes, maximum lawful
B2-message transport at a small B4 ceiling, and canonical equivalence with the
closed Unix datagram path.  Byte and syscall counts are diagnostic only.

## Kill criteria

Stop before introducing durable connection/parser/progress state if correctness
requires it.  If the existing B4 header cannot safely delimit a frame, classify
`ADDITIONAL_STREAM_FRAMING_REQUIRED` before adding the smallest possible
extension.  Any partial native mutation is a stream-boundary atomicity failure.

## Explicit exclusions

No TCP/IP, UDP/IP, Internet/LAN/RF transport, routing, discovery,
authentication, encryption, ACK/NACK, reconnect policy, retransmission
protocol, long-lived daemon, stable-wire commitment, PNF1, or changes to
PX3--PX16 semantics.
