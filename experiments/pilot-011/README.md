# PILOT-011 — Regret-Aware Bit-Credit Routing

PILOT-010 showed that route-classification accuracy is not the right compression objective: a false negative can cost far more compression bits than a nearly neutral false-positive neural activation. PILOT-011 therefore tunes the router directly on **oracle regret under an explicit deterministic neural-compute budget**.

## Router

For the observed probe prefix define conceptually:

```text
R = P_neural(prefix) / P_cheap(prefix)
credit_bits = log2(R)
```

No logarithm or floating point is used by the codec. `credit_bits > A` is implemented exactly as `R > 2^A` using integer CDF likelihood products; rejection is `R < 2^-B`. Activation and rejection credits are independent, so the policy can price false positives and false negatives asymmetrically.

The route remains causal, deterministic and zero-selector-bit. Bytes are coded by cheap while probing; after neural activation the neural gate is used for the remainder; after cheap rejection the specialist is never evaluated again.

## Development protocol

Only previously consumed benchmark streams are used for tuning:

- 6 Silesia streams from PILOT-007;
- 3 Large Corpus streams from PILOT-008;
- 5 Pizza&Chili pseudo-real streams from PILOT-009;
- 6 Silesia streams from PILOT-010.

Total: **20 development streams**. The first 256 bytes rebuild exact quantized CDF evidence. The previously frozen cheap/neural payload bpb values define:

```text
oracle_bpb = min(cheap_bpb, neural_bpb)
regret_bpb = selected_bpb - oracle_bpb
```

Candidate grid: **735 policies**.

- `min_observations`: 4, 8, 16;
- `max_probe_bytes`: 16, 32, 64, 128, 256;
- `activation_credit_bits`: 0, 2, 4, 6, 8, 10, 12;
- `rejection_credit_bits`: 2, 4, 6, 8, 10, 12, 16.

The deterministic compute proxy is specialist calls divided by stream bytes. Wall-clock time is reported but never used to choose a route or policy.

## Predeclared modes and feasibility

The requested modes were:

- **max**: minimum mean oracle regret, budget `<= 1.00`;
- **balanced**: minimum mean oracle regret, budget `<= 0.50`;
- **fast**: minimum mean oracle regret, budget `<= 0.20`.

The development sweep found that the **lowest compute fraction attainable anywhere in the frozen grid is 0.25245**. Therefore `fast <= 0.20` is **infeasible**. The budget was not relaxed after seeing development data, and `fast` was not evaluated on the fresh holdout. Cheap-only remains the explicit zero-neural endpoint.

Selected feasible policies:

| mode | min obs | max probe | activate credit | reject credit | dev mean regret | dev compute |
|---|---:|---:|---:|---:|---:|---:|
| max | 4 | 32 | +0 bit | -12 bit | 0.000085 bpb | 0.9508 |
| balanced | 4 | 16 | +8 bit | -6 bit | 0.022205 bpb | 0.4521 |

The full 735-policy table and the **42-point Pareto frontier** are committed as `candidate-policies.csv` and `pareto.csv`.

## Fresh holdout

The holdout is a fixed six-collection subset of the official Pizza&Chili **real repetitive corpus**, not used by earlier POLLICINO pilots:

- `cere` — yeast DNA;
- `para` — yeast DNA;
- `influenza` — DNA sequence collection;
- `coreutils` — source-code versions;
- `kernel` — Linux kernel source versions;
- `world_leaders` — document collection converted to text.

Archive and full extracted SHA-256 values are recorded in `holdout-manifest.json`. Only the first **4096 bytes** of each collection are entropy-coded in this pilot.

### Aggregate payload results

| method | mean payload bpb | mean oracle regret bpb | mean specialist fraction |
|---|---:|---:|---:|
| oracle min(cheap, neural) | **2.68949** | 0 | — |
| always neural | 2.68974 | 0.00024 vs oracle mean gap | 1.000 |
| PILOT-011 max | **2.69014** | **0.000651** | 0.6693 |
| PILOT-011 balanced | **2.69137** | **0.001872** | 0.5006 |
| PILOT-009 sequential | 2.69169 | 0.002197 | ~0.5055 |
| cheap | 2.79419 | — | 0 |
| zlib | 2.48503 | — | — |
| zstd-19 | **2.35547** | — | — |

The routing result is positive, but this is **not** a claim of universal compression superiority: zlib and especially zstd remain better on average on this holdout.

Relative to PILOT-009 on the same fresh holdout:

- `balanced` reduces mean oracle regret by about **14.8%** while using essentially the same/slightly lower neural-call fraction (`0.5006` vs `~0.5055`);
- `max` reduces mean oracle regret by about **70.4%**, at the cost of raising neural-call fraction to `0.6693`;
- maximum regret falls from `0.003906` bpb for PILOT-009 to `0.002686` for balanced and `0.001953` for max.

### Per-domain behavior

`cere` is strongly repetitive and both P11 modes quickly choose cheap. `coreutils`, `kernel` and `world_leaders` activate neural. `influenza` exposes the value of the regret objective: `max` activates neural and lands within `0.000244` bpb of its oracle, while `balanced` chooses cheap and pays `0.002686` bpb. `para` remains a small false-negative case for all tested routers.

## Regression controls

On the 4096-byte controls:

- self-v2: both P11 modes activate neural at byte 4 and produce `1.79199` bpb vs always-neural `1.78979`;
- `aaa.txt`: max and balanced choose cheap, with balanced rejecting after only 5 bytes;
- random-64: both choose cheap and avoid persistent neural compute.

## Reproducibility

Successful scientific run:

- GitHub Actions run: `31964824563`;
- run head: `9504a76f2348760a7a79cb3c567378a9fa03fc80`;
- **60 tests passed in 4.28 s** before the benchmark;
- artifact: `9268295583`;
- artifact digest: `sha256:fa5d8f14a500200a85eabdefb0d5348d12b6b1edc8656831d93be75f148966a6`;
- exact PILOT-003 checkpoint and canonical tensor fingerprint are verified before evaluation.

The canonical final entrypoint is `run_feasible.py`, which adds retrying buffered I/O for slow historical mirrors and records the predeclared `fast` budget as infeasible rather than relaxing it. `run.py` contains the frozen scientific core.

Earlier attempts failed before the fresh holdout was opened: one on historical-mirror I/O, one when the predeclared fast budget was discovered infeasible, and one on another development mirror connection. None changed the grid, budgets or fresh holdout.

## Conclusion

**Direct regret optimization fixes the main objective-function mistake exposed by PILOT-010.** It produces a real quality/compute Pareto frontier: balanced slightly improves compression quality at roughly the same neural compute as PILOT-009, while max buys substantially lower regret with more compute.

This is enough evidence to stop adding file-level confidence thresholds. The next experiment should add the architectural dimension deliberately deferred here: **block-local regret routing**, so heterogeneous files can switch cheap/neural decisions between blocks rather than making one irreversible choice for the entire stream.
