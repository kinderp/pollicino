# PX14 decision

```text
GATE: PX14-PN-B3
IDENTIFIER_PROVENANCE: repository-owner candidate derived from PX13 recommendation
CLASSIFICATION: POLLICINO_INDEPENDENT_PROCESS_BYTE_IO_READY_WITH_LIMITS
CONFIDENCE: HIGH
```

Selected model: bounded fresh-interpreter workers over binary subprocess pipes,
with the existing envelope length as the stream delimiter and native decoders as
the apply gate.

No existing production module from D2 through B2A changed. PX14 adds only the
process-I/O reader and worker. It introduces no persistent session state, peer
progress state, adaptive policy state, PNF1 dependency, fragmentation, retry,
ACK ledger, network transport, application semantics, or extra framing bytes.

The hypothesis survived the registered loss, corruption, segmentation, crash,
restart, sender-uncertainty, adaptive-fallback, and mule experiments. PX3, PX5,
PX6, PX8, PX9, PX10, PX11, PX12, and PX13 remain valid within their documented
limits.

The dominant new frontier is now realistic bounded-unit size. Existing framing
is clean on an ordered stream, while valid B2 messages can approach 29,245 bytes.
The smallest evidence-justified next experiment is therefore an MTU and
fragmentation-boundary experiment over the still-local byte/process model. It
must remain separate from selection of a real radio or network transport.
