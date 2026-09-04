# PX10-PN-B2 scientific report

## Question

Can independently instantiated endpoints reconcile persistent D2/D3 state
using only bounded serialized messages crossing an unreliable B1 boundary?

The baseline was exact PX9 closure
`c8b8ebcec4414849fc8d72011c45771224caeb3d`. Before implementation, all 29
PX9 focused tests passed, the declared suite passed 318 with 5 skips, and
compileall passed.

## Method

The experiment introduced one additive production module. Each endpoint
encapsulates only its local catalog and query/result store. It sends canonical
experimental advertisement, request, reference-selection, and complete-record
bytes. The contact driver passes those bytes through a deterministic lossy
complete-message adapter and never reads endpoint stores.

The matrix exercised control and record loss, duplicate control and records,
disconnect, direction-specific failure, sender uncertainty, stale metadata,
request-before-advertisement reordering, accidental corruption, truncation,
unknown envelope fields, conflicts, native quota failure, subprocess state,
restart, pagination, and a semantic-blind three-node mule.

## Results

Direct remote-store reads in the production contact driver are zero. The
lossless representative two-way query/result/reference contact used 14 control
messages (1,034 encoded bytes), 6 record messages (426 encoded bytes, 168 PX8
logical bytes), and 20 bearer attempts for 6 durable commits.

The 105-query/105-result proof converged after restart between three contacts:

| Contact | Outcome | Commits | Control messages/bytes | Record messages/bytes | Attempts |
|---:|---|---:|---:|---:|---:|
| 1 | budget exhausted | 98 | 2 / 4,490 | 98 / 6,860 | 100 |
| 2 | budget exhausted | 92 | 8 / 13,982 | 92 / 6,185 | 100 |
| 3 | no more planned work | 20 | 10 / 17,910 | 20 / 1,340 | 30 |

Sender uncertainty committed at the receiver, then destroyed all ephemeral
contact state. Reopened endpoints exchanged advertisements but zero record
messages for that identity. Permanent control or record loss returned a finite
partial outcome and made no false convergence claim.

The mule transferred a query A–C–B despite initial metadata loss and a C
restart. A result returned B–C–A despite sender uncertainty and another C
restart. A selected reference survived a disconnected selection contact, was
explicitly selected again B–C, survived restart, and was explicitly selected
again C–A. Result arrival never selected the reference automatically.

## Interpretation

The “telepathy” shortcut was removed for the registered experiment. Endpoint
planning uses only local durable state plus decoded peer claims. Those claims
cannot establish possession: only a structurally decoded record accepted by a
native store can do so. No persistent ACK/session state, custody state, direct
peer store read, retry loop, fragmentation, or application-specific branch was
needed.

The result is still a synchronous local protocol simulation. Exact identities
and digests leak through the control plane. SHA-256 detects accidental change
but provides no authentication. Fresh full scans are linear and lack proven
fairness at maximum page counts. These findings make bounded fair/efficient
reconciliation and disclosure reduction the next experimental frontier before
physical transport work.
