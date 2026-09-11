# PX14 scientific report

## Question and result

PX14 asked whether validated endpoint messages survive a genuine interpreter
and OS byte-stream boundary. They do for the registered local-pipe experiment.
Separate workers know only their own durable roots and received bytes. Stream
segmentation does not affect state, and incomplete or invalid messages never
reach native mutation.

The key adaptive falsification attempt exposed an in-process convenience: the
compact receiver's decode result had previously been visible as a local return
value. PX14 removed that convenience without a new message type. A responder
whose first summary is equal or undecodable returns its own existing B2C
summary. The initiator uses those received bytes to establish equality or to
start the exact B2F fallback. Missing records continue over normal B2 requests
and records. Transport failure produces no peer summary and therefore never
becomes false capacity evidence.

The experiment observed zero canonical mismatches, zero partial-message native
mutations, zero undetected false negatives, and zero retransfers of a committed
record as missing in the registered uncertainty/restart case. The 105-query and
105-result restore/reconciliation regression passed through repeated fresh
workers. Capacity-10 behavior at 10,000 identities was checked for differences
0, 1, 10, 100, 1,000, and 10,000.

## Scope and limits

Evidence is local POSIX/macOS subprocess-pipe evidence with one writer per
direction and coordinator-enforced process timeouts. Pipes preserve byte order.
Backpressure received a bounded sanity test, not production flow control.
There is no daemon, multiplexing, real network, MTU validation, fragmentation,
retry protocol, authentication, encryption, or stable-wire commitment.

The compact executable remains the closed PX12 implementation: 64-bit
fingerprints and 32-bit checksums. The historical preregistration text that said
128/64 is left unchanged and remains a documented discrepancy.

The process boundary adds no stream framing bytes. It does add a symmetric B2C
summary exchange where an independent initiator needs byte-visible equality or
decode-failure evidence; this is existing experimental B2C data, not a new
stable envelope or ACK.
