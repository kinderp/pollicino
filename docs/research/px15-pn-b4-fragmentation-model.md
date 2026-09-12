# PX15 B4 fragmentation model

PX15 inserts one experimental layer below a complete B2-family envelope. The
upper message remains the sole semantic unit. The B4 layer never invokes D2 or
D3 and emits upward only after byte-exact reassembly and inherited B2 envelope
validation.

The selected frame is `PB4F` version 1, type 1, with a 52-byte header:

```text
magic:4 | version:1 | type:1 | message-sha256:32 |
total-length:4 | index:2 | count:2 | payload-length:2 | crc32:4
```

The encoding is `pollicino.experimental-b4-fragment.v1`; it is not a stable
wire commitment. The full-message SHA-256 prevents cross-message mixing. CRC32
provides early fragment corruption detection, not authentication. The existing
B2-family body digest remains mandatory after reassembly.

Reassembly is bounded, unordered, and duplicate-safe. One incomplete message
per direction is allowed. An identical fragment is a no-op, including a delayed
duplicate immediately following completion. A conflicting duplicate or another
message arriving while one is incomplete fails closed. A later message is
accepted after the completed-message duplicate window advances.

All fragment state is volatile. Loss, EOF, disconnect, or crash before full
native commit makes the current message semantically absent. A fresh contact
recomputes work from durable D2/D3 state and may send the whole message again.
No fragment ACK, retransmission, cursor, journal, custody, or persistent
reassembly state exists.

The PX14 ordered stream carries concatenated B4 frames and its incremental B4
reader handles partial frame headers/bodies. This is stream reassembly around a
protocol fragmentation envelope; it does not use PNF1.

