# RAPID one-selection deadline kernel

Status: validated prototype component, not yet an end-to-end routing strategy

## Purpose

The current Pollicino routing strategy interface filters bundles, while the shared scheduler later orders selected work using application priority, transport expiry, completion preference and object size. RAPID, instead, needs to rank replication opportunities by:

```text
marginal deadline utility / replication bytes
```

Changing the global scheduler only for this experiment would violate the Use-Case Justification Gate. The smallest falsifiable step is therefore a **one-selection kernel**: given already-computed RAPID inference reports for the same encounter, select at most one bundle. With one selected candidate the downstream common scheduler cannot reorder competing RAPID choices.

Module: `pollicino.net.rapid_selection`

## Selection rule

For each inference:

1. discard incomplete knowledge;
2. discard bundles already delivered;
3. discard a candidate that already has a complete replica;
4. discard passed-deadline or zero-benefit replications;
5. rank the remaining candidates by descending `marginal_utility_per_byte`.

Deterministic tie-break order:

```text
earlier application deadline
smaller replication transfer
bundle ID
```

The kernel requires every inference to describe the same candidate, destination and encounter time and rejects duplicate bundle IDs.

## Important distinction

The kernel does **not** overload `BundlePriority` to encode RAPID utility. Application priority and RAPID resource-allocation utility remain separate concepts.

It also does not yet:

- update encounter/control state;
- compute candidate queue knowledge;
- perform a transfer;
- observe transfer completion;
- publish a new replica advertisement;
- account control bytes;
- replace the common scheduling policy.

Those responsibilities belong to a later encounter strategy/integration experiment.

## Validated property

A test deliberately compares two candidates:

```text
candidate A:
  marginal utility = 0.4
  replication cost = 100 bytes
  score = 0.004 / byte

candidate B:
  marginal utility = 0.3
  replication cost = 50 bytes
  score = 0.006 / byte
```

The kernel selects B even though A has the larger absolute benefit, because B yields more deadline-delivery benefit per scarce byte.

The suite also validates:

- deterministic tie-breaking;
- incomplete inference is not rankable;
- zero marginal benefit is not rankable;
- delivered/already-replicated/passed-deadline candidates are excluded;
- mixed encounter contexts fail closed;
- duplicate bundle candidates fail closed.

## Numerical test correction

The first validation run exposed an error in the **test fixture**, not in the kernel. The intended equal-score tie was constructed through subtraction from a non-zero floating baseline, producing tiny binary floating-point differences between theoretically equal ratios.

The fixture was corrected to construct the synthetic marginal utilities from a zero baseline. The selection logic was not relaxed or changed to force the expected result.

## Validation

GitHub Actions run `33066796847` — PASS:

- complete project test suite — PASS;
- RAPID utility / meeting / replica / queue / inference / selection targeted tests — PASS.

The temporary validation workflow was removed after the green run.

## Next gate

The next implementation should not immediately add a global ranking hook. First build a one-selection-per-encounter RAPID integration that can:

```text
current contact
  -> exchange/update local control knowledge
  -> obtain candidate queue estimate
  -> build inference reports
  -> run this selection kernel
  -> return at most one non-destination replication
```

Direct delivery to a final destination remains a separate first-priority rule.

Only if this experiment demonstrates value and another independent use case needs strategy-controlled multi-bundle ordering should a general scheduler/ranking abstraction be proposed.

## Evidence boundary

All results remain `MODEL_SYNTHETIC`.

No physical routing or deadline-performance claim is permitted before **GATE PROVE FISICHE HW-006**.
