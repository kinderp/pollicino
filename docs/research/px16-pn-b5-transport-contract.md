# PX16 transport contract

The adapter contract is `send_frame(bytes)` and `receive_frame()`. One lawful
B4 frame is one Unix datagram in each direction. There is no outer header,
length prefix, delimiter, ACK, retry, routing field, peer identity, or semantic
inspection. A successful `sendto()` records only local kernel acceptance.

The configured ceiling is 53 through 4096 bytes and must equal the B4 frame
ceiling used by the caller. Receive requests ceiling plus one byte, making an
oversized datagram observable and rejectable. Empty and oversized frames are
transport errors; short nonempty frames are returned as opaque candidates and
then rejected by B4. Source pathname filtering is contact configuration, not
authentication.

Blocking sockets with a finite timeout were selected over an event loop. A
timeout ends the current opportunity without asserting record absence,
capacity failure, or convergence. No user-space queue exists.

