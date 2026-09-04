# PX9-PN-B1 existing `link.py` audit

1. **Can PNF1 implement B1 later?** Potentially, through a separately tested
   adapter that transports a chosen complete-record serialization and exposes
   the B1 attempt result. This gate does not prove that adapter.
2. **Does B1 need PNF1 now?** No. Complete bounded record units are sufficient
   for every registered loss and restart scenario.
3. **Does `ScarceLinkProfile` match B1?** No. It models bitrate, fragment size,
   fragment duplication, data/ACK loss, retry limits, and attempt delays for
   exact reconstruction. B1 needs only deterministic complete-unit outcomes.
4. **Would `transmit_exact()` add deferred semantics?** Yes. It performs PNF1
   fragmentation/reassembly and stop-and-wait retry with ACK behavior. Reusing
   it would make a larger B2/B3 decision inside B1.
5. **Can both modules coexist?** Yes. PX9 adds `bearer.py` and neither imports
   nor edits `link.py`; existing exact-content users and tests are unchanged.
6. **Should compatibility be tested later?** Yes, after a serialization and
   fragmentation/loss boundary is explicitly gated. It should be adapter
   conformance, not implicit B1 behavior.

Decision: leave `link.py` unchanged. `PNF1`, `FragmentFrame`,
`fragment_payload()`, `reassemble_frames()`, `ScarceLinkProfile`, and
`transmit_exact()` do not enter B1.
