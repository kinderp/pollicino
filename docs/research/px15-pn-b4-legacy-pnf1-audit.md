# PX15 legacy PNF1 preregistration audit

1. PNF1 encodes sequence/count, payload length, and CRC32, but does not bind a
   full content-derived message identity or declared total length to the current
   B2 maximum.
2. Its pure `FragmentFrame`, `fragment_payload()`, and `reassemble_frames()` can
   be called without `transmit_exact()` and are useful reference behavior.
3. `transmit_exact()` adds stop-and-wait retry, ACK-loss behavior, and a delivery
   report. Those semantics are not required by B4 and must not enter it.
4. The pure codec is generic, while `ScarceLinkProfile` adds bitrate, loss,
   retry, and ACK policy outside the minimal fragmentation boundary.
5. Reassembly tolerates reordering and identical duplicates and rejects a
   conflicting duplicate, but it is batch-oriented rather than a bounded
   incremental one-in-flight receiver.
6. Frame payload length is bounded to 16 bits, but receiver allocation is not
   tied to the inherited B2-family maximum and transfer ID is caller-supplied.
7. Legacy functionality can and should coexist unchanged.
8. B4 should remain a clean layer derived from current B2 bounds.
9. A future compatibility adapter could translate complete B4/B2 messages into
   PNF1 experiments, but that is not required for PX15.
10. No current evidence justifies promoting PNF1 to a stable protocol.
