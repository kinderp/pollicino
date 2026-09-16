# Fair anti-starvation scheduling per bearer

## Goal

PollicinoNet already supports local bundle priority (`BULK`, `NORMAL`, `HIGH`, `EMERGENCY`) and a logical source-byte budget for one intermittent contact. Pure strict priority, however, can starve low-priority work forever if new high-priority bundles keep arriving.

This layer adds bounded, persistent starvation protection and explicit scheduling policy per bearer without pretending that a synthetic logical budget is measured radio capacity.

## Simple mental model

Normal order remains:

```text
priority
 -> sooner expiry
 -> can finish target
 -> smaller remaining object
 -> stable bundle-id tie break
```

Fairness adds one bounded step before that queue:

```text
has a transferable bundle waited too long?
  yes -> rescue a small amount of it
  no  -> normal priority queue
```

A default experiment may choose, for example, to rescue at most one starved bundle and at most one chunk from it before normal priority scheduling resumes. The exact thresholds are policy inputs, not protocol constants.

## Persistent waiting age

`FairSchedulerState` records, per locally eligible bundle:

- when it first became eligible for useful transfer;
- when it was last observed;
- when it was last served;
- number of useful services;
- number of deferrals.

The state also stores processed encounter IDs. Replaying the same encounter ID is a zero-wire no-op and does not artificially age or reset a bundle.

The state can be stored through an atomic checksummed checkpoint. A relay restart therefore does not erase waiting age and cannot make an old low-priority bundle look new again.

The checkpoint checksum detects accidental corruption; it is not authentication against a hostile writer.

## Rescue semantics

A bundle enters the rescue queue once:

```text
now - eligible_since >= starvation_seconds
```

Starved bundles are ordered by longest waiting time, then earliest eligibility, then stable bundle ID. Rescue is bounded by:

- `max_rescue_bundles`;
- `rescue_chunks_per_bundle`;
- the same explicit logical source-byte budget used by the ordinary scheduler.

A rescue never overshoots the logical budget. If the next chunk does not fit, it is not sent.

After useful service, that bundle's waiting age resets. It may become starved again later if it remains incomplete and receives no further service.

## What fairness can and cannot guarantee

Fairness can guarantee eventual progress only under an important condition:

> At least one future encounter must have enough logical budget to fit at least one transferable chunk of the starved bundle.

If every future contact budget is 32 bytes while the smallest transferable chunk is 64 bytes, the scheduler cannot create capacity that does not exist. A future design may introduce different chunking or measured contact-window adaptation, but it must not silently overshoot the budget.

## Per-bearer policy

`BearerSchedulingPolicy` binds one explicit scheduling policy to one explicit `BearerProfile`.

This allows experiments such as:

```text
lab-lora:
  logical budget = 64 source bytes
  starvation rescue after 60 s

lab-wifi:
  logical budget = 4096 source bytes
  starvation rescue after 10 s
```

These numbers are experiment inputs. PollicinoNet provides no built-in LoRa/BLE/Wi-Fi/Internet scheduling-capacity defaults.

## Evidence boundary

Three concepts remain separate:

1. **Bearer profile evidence** — synthetic or measured parameters used by the link model.
2. **Scheduling policy budget** — the logical source-byte allowance supplied to this scheduler.
3. **Execution evidence** — deterministic model execution or physical RF replay.

A measured bearer profile does **not** turn a manually chosen scheduling budget into measured contact capacity. `BearerSchedulingReport.logical_budget_is_measured_capacity` therefore remains false in this layer.

Only a future adapter backed by physical contact-window evidence may justify a mapping such as:

```text
measured 27 s LoRa contact under checkpoint X
 -> supported scheduling source-byte budget Y
```

That mapping requires HW-006 or later physical evidence for the actual frame sizes and geometry being claimed.

## Physical-test gate

No hardware is required to validate:

- starvation-state persistence;
- rescue ordering;
- duplicate encounter idempotency;
- different synthetic policies for LoRa/BLE/Wi-Fi/Internet;
- logical-budget enforcement;
- policy comparison in deterministic multi-relay simulations.

Physical tests become necessary before contact duration, geometry, loss/retry behaviour or bearer choice is converted into a measured scheduling budget.

The first LoRa gate remains the frozen HW-006 campaign: 42-byte frames, 2 dBm, same-room through distance/NLOS progression. Actual PNB1/PNC1/PCM1/PNA1/data frame sizes must then be measured before LoRa-aware scheduling is presented as calibrated to reality.
