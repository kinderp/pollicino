# PX15 decision

```text
GATE: PX15-PN-B4
IDENTIFIER_PROVENANCE: repository-owner candidate derived from PX14 recommendation
CLASSIFICATION: POLLICINO_BOUNDED_FRAGMENTATION_READY_WITH_LIMITS
CONFIDENCE: HIGH
```

Bounded ephemeral reassembly is sufficient for the registered fragmentation
boundary. A fragment is not progress; only a complete B2-family message that
passes inherited decoding and native durable apply is progress. Losing any
fragment is therefore equivalent to losing the whole current message.

The selected B4 contract is a new clean experimental frame layer. Legacy PNF1
remains unchanged and may be useful only behind a future compatibility adapter.
Neither PNF1 nor `transmit_exact()` entered B4. No fragment retransmission,
ACK, FEC, persistent reassembly, per-peer fragment cursor, or custody authority
is required for correctness.

PX3, PX5, PX6, PX8, PX9, PX10, PX11, PX12, PX13, and PX14 remain valid within
their documented limits. PX12's historical 128/64-bit preregistration wording
versus 64/32-bit executable behavior remains recorded, not rewritten.

The experiment does not prove a production fragmentation format, real bearer,
reliable delivery, security, or RF behavior. The largest new pressure is
tiny-MTU overhead: a 52-byte header leaves only 12 payload bytes at MTU 64.
This is an efficiency limit, not a correctness failure.

A reliability/ARQ gate is not required before testing real I/O: loss already
fails safely and fresh reconciliation provides bounded later opportunities.
The architecture is ready for a first real transport-adapter experiment without
reopening D2/D3/D4/B2 semantics. The smallest next falsification boundary is a
local Unix-domain datagram adapter carrying complete B4 frames, with bounded
receive sizes and deterministic loss/interruption. It should keep B2 and B4
experimental and must not add reliability, authentication, or routing.

