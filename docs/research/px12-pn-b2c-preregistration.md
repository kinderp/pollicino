# PX12-PN-B2C preregistration

`PX12-PN-B2C` is the provisional identifier recommended by the exact PX11
closure. No later authoritative identifier exists in that tree.

## Baseline

- PX11 closure: `945039462d851f9773e4d9678cdc37b7e7b4f908`
- declared suite: 414 passed, 5 skipped
- focused PX11 suite: 46 passed
- compileall: pass
- worktree: clean

## Hypothesis

For important high-overlap Pollicino workloads, a bounded compact
reconciliation strategy can reduce control bytes and/or exact metadata
disclosures relative to PX11 exact B2F while preserving eventual exact
reconciliation.

## Correctness and promotion thresholds

```text
UNDETECTED_FALSE_NEGATIVES = 0
ORACLE_MISSING_SET_MISMATCHES = 0
STATIC_FAIRNESS_REGRESSION = 0
PERSISTENT_PEER_STATE_REQUIRED = NO

and, in the high-overlap target regime:

CONTROL_BYTE_REDUCTION_VS_PX11 >= 50%
or
EXACT_IDENTITY_DISCLOSURE_REDUCTION_VS_PX11 >= 50%
```

Decode uncertainty, capacity overflow, fingerprint ambiguity, corruption, or
post-transfer root mismatch must be explicit. They may trigger at most one
bounded PX11 exact fallback per experiment invocation; they may never establish
equality or possession.

## Candidate admission analysis

1. **PX11 exact page ranges** — correctness oracle and fallback. Linear exact
   disclosure; no probabilistic failure.
2. **Deterministic range/prefix summaries** — already represented by PX11's
   page digests. Recursive refinement could reduce high-overlap disclosure but
   adds rounds and remains distribution-sensitive; analyze, do not duplicate
   PX11 deeply in this gate.
3. **Bloom membership** — false positives can hide lawful records. Admit only
   as a non-authoritative hint followed by exact verification; reject as a
   standalone reconciler.
4. **IBLT-style set difference** — bounded cells can peel small symmetric
   differences; failure is detectable and can fall back. Admit for
   implementation using deterministic pure-Python cells.
5. **Minisketch/BCH** — strong small-difference properties, but a correct
   implementation or dependency introduces substantially more algebraic and
   maintenance complexity. Analyze and reject before implementation unless
   IBLT evidence exposes a need.

## Registered IBLT model

- 128-bit SHA-256-derived fingerprints are reconciliation metadata only.
- Full canonical identities remain native authority.
- Each cell contains signed count, XOR fingerprint, and 64-bit checksum.
- Three deterministic cell indexes are used.
- Summary includes full-set SHA-256 and cardinality.
- Equality is accepted only when cardinality and full-set digest match.
- A decoded fingerprint must map uniquely at the source before identity reveal.
- Any ambiguity or decode residue triggers exact fallback.
- Capacities 1, 10, 32, 100, and 1,000 are bounded and tested.
- Strategy tuning is experiment-controlled; automatic policy is out of scope.

## Kill criteria

Stop promotion if compact reconciliation creates an undetected missing record,
requires persistent peer/sketch/session state, regresses PX11 static fairness,
or writes native state without the existing B2 request/record and native apply
path.
