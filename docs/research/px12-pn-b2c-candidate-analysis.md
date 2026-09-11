# PX12-PN-B2C candidate analysis

PX11 exact B2F remains the correctness oracle and bounded fallback.

| Candidate | Admission result | Reason |
|---|---|---|
| PX11 exact page/range | Oracle/fallback | Exact, fair, already validated; metadata-heavy at high overlap. |
| Deterministic range/prefix summaries | Analysis only | This is substantially the existing B2F design; reshaping pages does not remove exact prefix disclosure. |
| Bloom membership | Rejected as authority | False positives can hide lawful missing records. Safe use would still require an exact verification path. |
| IBLT-style set difference | Implemented | Bounded, deterministic, detects peel failure, and can reveal a small symmetric difference without all identities. |
| Minisketch/BCH | Rejected before implementation | A correct finite-field decoder or a new native dependency adds disproportionate complexity before IBLT evidence establishes the useful regime. |

The admitted IBLT binds a 64-bit experimental fingerprint to record kind,
canonical identity, and the native 32-byte record digest. The fingerprint is
never a native identity. A full set digest detects equality and residual
ambiguity. Identity reveal and the unchanged B2 request/record path lead to
native validation and durable apply.

Capacity is a tuning claim, not known fact about a peer. Undersizing can fail
detectably; oversizing spends extra bytes. PX12 deliberately does not add an
automatic selector.
