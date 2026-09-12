# PX17-PN-B6 stream transport contract

## Status and provenance

`PX17-PN-B6` remains the repository-owner candidate name derived directly
from the PX16 closure recommendation.  No authoritative replacement name was
present at baseline `21f8f64f630f743ed5e31dcba90732b543f3b82b`.

The executable adapter is explicitly experimental:
`pollicino.experimental-unix-stream.v1`.  It does not freeze B4 or any B2
encoding as a public protocol.

## Contract

The selected transport is pathname-based `AF_UNIX/SOCK_STREAM` on macOS
Darwin.  `UnixStreamListener` owns bind/listen/accept and filesystem cleanup.
`UnixStreamAdapter` owns a connected stream and exposes:

```text
connect(path, bounds)
send_frame(complete_b4_frame)
receive_frame() -> complete_b4_frame
shutdown_write()
close()
```

One listener/connection is used for one finite contact opportunity.  A
connection, successful `send`, or complete local write is never possession
evidence.  Only durable receiver D2/D3 state affects later reconciliation.

## Framing

No transport envelope is added.  The adapter composes the closed PX15
`BoundedFragmentStreamReader`:

```text
read 52-byte B4 header
validate generic bounds
derive payload length
read exactly that payload
validate complete B4 frame
emit one frame
```

Thus:

```text
STREAM_TRANSPORT_EXTRA_FRAMING_BYTES = 0
```

The adapter does not reassemble B2 messages.  `EphemeralFragmentReassembler`
remains the B4 owner of frames-to-message reconstruction.

## Bounds

- B4 frame ceiling: configured from 53 through 4096 bytes;
- socket read: 1 through 4096 bytes;
- write chunk: 1 through the configured frame ceiling;
- default maximum live adapter bound: frame ceiling plus read ceiling, at most
  8192 bytes;
- complete frames/contact: inherited B4 limit;
- every connect, accept, read, and frame write has a finite timeout;
- no user-space outbound queue and no resynchronization scan.

A header declaring a payload beyond the configured B4 ceiling is rejected
after only the fixed header is buffered.  An invalid frame poisons the current
receive opportunity; subsequent reads fail immediately.  Recovery is a fresh
contact, never magic scanning.

## Partial writes and blocking

`send_frame` may invoke multiple OS writes to finish the current frame within
one deadline.  This handles legitimate short writes; it is not retransmission.
If the deadline, peer, or connection fails, the write side becomes terminal.
No unwritten suffix is silently discarded or queued indefinitely.

## Address lifecycle

The listener creates a mode-0600 pathname and a local ownership marker.
Normal close removes only the owned path.  Stale recovery requires a socket,
matching marker, and proof that the recorded process is dead.  Active or
unowned paths fail closed.  The pathname is a transport address, not peer,
trust, or application identity.

## Generic adapter finding

Both closed real transports honestly support the minimal semantic surface:

```text
max_frame_bytes
send_frame(bytes)
receive_frame()
close()
```

Datagram transport preserves a frame boundary in the kernel; stream transport
reconstructs it internally.  No upper layer needs to know this difference.
A larger capability hierarchy is not yet justified.
