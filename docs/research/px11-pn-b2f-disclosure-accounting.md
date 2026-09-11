# PX11-PN-B2F disclosure accounting

B2F deliberately uses exact reconciliation so fairness can be tested without
probabilistic summaries. A directory reveals each page's first and last exact
identity, item count, page shape/order, and SHA-256 digest. Requested pages then
reveal the existing B2 exact identities and per-record digests. Missing-ID
requests reveal the chosen identities. Explicit reference policy remains local,
but requesting reference ranges leaks interest in those ranges.

These digests provide accidental integrity and comparison only. They provide
neither secrecy nor authentication.

## Measured 1,000-query overlap matrix

| Overlap | New records | Contacts | Control bytes | Record bytes | Repeated control bytes | Identity occurrences disclosed | Digests | Control/new record |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0% | 1,000 | 11 | 97,950 | 54,000 | 2,980 | 3,815 | 2,165 | 97.95 |
| 50% | 500 | 6 | 49,030 | 27,000 | 2,340 | 1,845 | 1,105 | 98.06 |
| 90% | 100 | 2 | 10,566 | 5,400 | 964 | 387 | 239 | 105.66 |
| 99% | 10 | 1 | 5,051 | 540 | 505 | 152 | 120 | 505.10 |
| 99.9% | 1 | 1 | 4,997 | 54 | 505 | 143 | 120 | 4,997.00 |

At 99.9% overlap, the strategy is correct but discloses 143 identity field
occurrences and spends 4,997 control bytes to commit one 54-byte encoded record
message. The repeated-control-byte metric counts wholly redundant delivered
control envelopes, so it is conservative; partially redundant directory and
advertisement fields are not charged as repeated bytes.

For the 10,000-record late suffix, 1,000 records required 190,785 control bytes,
54,000 record bytes, 7,895 disclosed identity occurrences, and 4,145 digests.
The repeated-control ratio was 39.24% by the conservative definition.

## Interpretation

Correctness wins this gate: no record starved. The high-overlap numbers provide
positive evidence for a later compact reconciliation/disclosure experiment.
They do not select Bloom, IBLT, Minisketch, Merkle, or PSI in advance. Target
privacy and transport budgets are not yet specified, so no production capacity
claim is made.
