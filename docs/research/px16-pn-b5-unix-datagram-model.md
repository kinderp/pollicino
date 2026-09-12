# PX16 Unix-domain datagram model

PX16 uses filesystem-path `AF_UNIX/SOCK_DGRAM` on macOS. It provides real
kernel send/receive calls, independent process address spaces, message
boundaries, finite kernel buffers, and explicit local addresses without IP,
routing, RF, or external hardware.

Each adapter owns one socket path inside an explicitly declared directory and
writes a sidecar containing PID, path, and an instance token. Normal close
removes only matching owned resources. Opt-in stale recovery removes only a
socket with a matching sidecar whose process no longer exists. Active address
collisions and unowned filesystem entries fail closed. Socket mode 0600 is
local OS access control, not Pollicino authentication.

The gate-level worker opens only its own durable root and socket. Two distinct
interpreters execute reconciliation. A third relay interpreter, where used,
forwards opaque datagrams and applies deterministic impairment actions without
B2/B4 interpretation.

The observed macOS socket buffers were 2,048-byte send and 4,096-byte receive
buffers. Backpressure can terminate a burst; it is transport failure, not
protocol evidence. Fresh durable-state reconciliation provides the next
opportunity.

