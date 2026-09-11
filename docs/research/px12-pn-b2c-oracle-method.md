# PX12-PN-B2C oracle method

For every differential case, the oracle is the exact set of canonical
identity/digest pairs implied by PX11 B2F. A successful compact peel must reveal
exactly the source-only fingerprints, which must resolve to exactly one full
canonical identity and native digest at the source. The receiver then uses the
unchanged B2 advertisement, request, complete-record, and native apply path.

The test matrix contains 81 deterministic state-pair comparisons: fixed
high-overlap sizes, prefix/suffix/alternating/sparse/block shapes, 64 seeded
random cases, a symmetric two-way case in both directions, and equal-cardinality
different-state detection. Oracle mismatches and undetected false negatives are
both zero.

An undecodable peel, residual cells, root-only mismatch, absent fingerprint, or
ambiguous fingerprint is not equality. It is a detected need for PX11 fallback
or an explicit non-converged/error outcome.
