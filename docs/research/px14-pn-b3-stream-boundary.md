# PX14 stream boundary

The existing experimental B2, B2F, and B2C envelopes all begin with the same
42-byte layout:

```text
4-byte magic | 1-byte version | 1-byte type | 4-byte body length |
32-byte SHA-256 body digest | body
```

That length is sufficient to delimit ordered streams. PX14 adds zero encoded
bytes and does not nest another frame. The bounded incremental reader buffers
at most one inherited message (`MAX_B2_MESSAGE_BYTES`, currently 29,245 bytes),
checks the magic-specific body limit as soon as the header is complete, and
only then accepts body bytes. Native B2/B2F/B2C decoders remain structural and
integrity authorities.

The tests cover one-byte reads, partial headers and bodies, header/body splits,
prime-sized and fixed-seed segmentation, concatenated messages, a boundary in
the middle of one read, clean EOF, mid-header EOF, mid-body EOF, corrupt bodies,
unknown magic/version/type, and oversized declared length. No native apply is
called for an incomplete or structurally invalid envelope.

This is stream reassembly. It is not PNF1, MTU fragmentation, fragment ACK, or
retransmission. The experimental encoding remains explicitly unfrozen.
