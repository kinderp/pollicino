# PX12-PN-B2C decision

GATE: PX12-PN-B2C

IDENTIFIER PROVENANCE: candidate recommended by the PX11 closure; no later
authoritative replacement was present at baseline.

CLASSIFICATION: POLLICINO_COMPACT_RECONCILIATION_REGIME_SPECIFIC

CONFIDENCE: HIGH

DECISION: retain PX11 exact B2F as correctness oracle and fallback. Admit the
experimental digest-bound IBLT candidate as evidence for small/high-overlap
differences, not as a universal production selector or stable wire protocol.

The promotion threshold was met for 10,000-state differences of 1, 10, and 100.
At a 1,000 difference the compact candidate reduced exact identity disclosure
but more than doubled control bytes because the 28 KiB sketch was repeated over
11 bounded contacts. At 0% and 50% overlap with 10,000 records, capacity overflow
was detected and exact fallback remained necessary.

Failures classified during development:

- identity-only sketch equality could hide same-identity record conflicts:
  `B. COMPACT_ENCODING_IMPLEMENTATION_ERROR`; corrected before evidence runs by
  binding fingerprints/root to native record digests;
- insufficient tiny-table peel headroom: `C. CANDIDATE_PARAMETERIZATION_ERROR`;
  corrected within the preregistered bounded candidate;
- deliberate overflow: `F. DETECTED_COMPACT_DECODE_FAILURE`; safe fallback;
- Bloom-alone and large-difference IBLT: `E/H/I/J` risks or losing comparisons,
  not changes to the exact oracle.

PX3, PX5, PX6, PX8, PX9, PX10 and PX11 remain valid unchanged.

SMALLEST NEXT EXPERIMENT: a bounded adaptive reconciliation policy and escalation
gate that chooses compact capacity or exact fallback without oracle knowledge of
the peer difference. This is a candidate frontier, not implemented by PX12.
