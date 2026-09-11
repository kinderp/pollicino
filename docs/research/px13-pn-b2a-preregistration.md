# PX13-PN-B2A preregistration

`PX13-PN-B2A` is the candidate identifier derived from the exact PX12 closure.
No later authoritative identifier was found in the baseline tree.

## Exact baseline

- PX12 closure: `816d3c2d26df4d6115f299cbce6803b324cc1443`
- full suite: 461 passed, 5 skipped
- combined focused PX11/PX12: 93 passed
- compileall: pass
- worktree: clean

The PX12 preregistration text says 128-bit fingerprints and 64-bit checksums,
while the closed implementation and complexity evidence use 64-bit fingerprints
and 32-bit peel checksums. PX13 does not rewrite that historical document and
uses the executable implementation as authority. This documentation discrepancy
does not change native identity or digest authority.

## Hypotheses

A bounded policy can select compact reconciliation, escalate finitely, or use
PX11 exact fallback without knowing the true peer difference. Correctness,
fairness, and durable-state authority remain unchanged.

For small high-overlap differences the selected policy should retain most of
PX12's savings. For large differences its total control cost should remain
bounded near PX11 exact rather than repeatedly sending large sketches.

## Registered policies

1. `EXACT_ALWAYS`.
2. `FIXED_COMPACT_THEN_EXACT` at capacities 1, 10, and 100.
3. conservative ladder `1, 10, 100, exact`.
4. aggressive ladder `10, 1000, exact`.
5. selected cost-aware ladder `10, 100, exact` with at most two probes,
   maximum 5,000 compact control bytes, an 8-attempt exact-progress reserve,
   and capacity 100 admitted only when local state has at least 5,000 records.

The local-size threshold is an experimental heuristic derived from PX12's
100/1,000/10,000 matrix, not a permanent protocol constant. Capacity 1,000 is
measured as a competitor but deliberately excluded from the selected policy
because its 28,517-byte summary is near the 29,245-byte inherited B2 ceiling and
PX12 showed repeated-sketch byte loss.

## Objectives and thresholds

Primary objective: control bytes. Secondary objective: exact metadata disclosure.
Hard constraints: exact correctness, finite termination, static fairness, no
persistent peer/session/escalation state.

```text
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
UNBOUNDED_ESCALATIONS = 0
PERSISTENT_PEER_POLICY_STATE = 0
PERSISTENT_ESCALATION_STATE = 0

selected-policy median cost / oracle-best <= 1.50
selected-policy large-difference cost / PX11 exact <= 1.25
selected-policy retains >= 80% of PX12 absolute byte savings
for 10,000-state differences of 1 and 10
```

Transport loss is never evidence of insufficient compact capacity. Only a
delivered, structurally valid `FALLBACK_REQUIRED` compact result may advance the
ladder. If the contact lacks the exact-progress reserve, the policy chooses exact
immediately rather than consuming the contact with probes.

## Kill criteria

Stop promotion if the selector reads oracle difference information, silently
hides a record, loops without a fixed bound, requires persisted peer/escalation
state, or repeatedly consumes a usable contact with failed compact probes while
making no durable exact progress.
