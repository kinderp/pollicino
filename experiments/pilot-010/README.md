# PILOT-010 — Stability-Aware Value Routing

PILOT-010 tests a stricter specialist router after PILOT-009 showed that a short burst of strong evidence can trigger a neural specialist even when its eventual compression gain is negligible.

## Question

Can POLLICINO require **persistent recent evidence** and a deterministic **future-value floor** before activating the neural specialist, reducing unnecessary neural compute without sacrificing useful neural routes?

The answer is mixed and scientifically important: **the router controls compute well, but it is too conservative to replace PILOT-009 as the default compression policy.**

## Router

`StabilityValueSpecialistRouterCDFProvider` adds four conditions to neural activation:

1. cumulative neural/cheap likelihood exceeds the frozen `256:1` PILOT-009 threshold;
2. a recent window exceeds a minimum neural advantage;
3. that recent condition persists for several consecutive decoded bytes;
4. a deterministic lower bound on future recoverable bits exceeds a policy margin.

The value floor is integer-only:

```text
projected_gain_bits = floor(remaining_bytes / recent_window) * recent_gain_bits
```

No wall-clock timing, CPU identity, floating-point log, randomness, or selector side-stream affects the route. Encoder and decoder reconstruct the same decision from the same decoded prefix.

## Frozen model provenance

The neural specialist is the exact PILOT-003 checkpoint, not a retraining:

- artifact ID: `9243314314`;
- artifact ZIP SHA-256: `72a2f5c06088401f64d06f2aaead014a55015715b5dc1abb1b787567750d11b5`;
- checkpoint: `winner.pt`, 600,933 bytes;
- checkpoint SHA-256: `713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7`;
- canonical model fingerprint: `354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`.

## Development-only calibration

The policy is selected using 14 **already consumed** files only:

- six Silesia files from PILOT-007;
- three Large Corpus files from PILOT-008;
- five Pizza&Chili pseudo-real files from PILOT-009.

A neural route is labelled useful only when its measured gain is at least `0.05 bpb`.

Frozen from PILOT-009:

```text
min observations       8
cumulative activate    256:1
cumulative reject      1:256
```

Grid searched:

```text
max probe               64 / 96 / 128
recent window            4 / 8 / 16 / 32
persistence              2 / 4 / 8
recent gain floor        1 / 2 / 3 / 4 bits
projected gain floor     0 / 32 / 64 / 128 / 256 bits
```

The predeclared ranking maximized route classification accuracy first, then minimized false-positive neural activations, false negatives, oracle regret, and decision latency.

### Selected policy

```text
max_probe_bytes             64
recent_window                 4
persistence_observations      8
recent_gain_bits              4
min_projected_gain_bits       0
```

Development result:

```text
12 / 14 correct
0 false positives
2 false negatives
mean decision byte 36.36
```

The two false negatives are `xml` and `sources-mut`.

A useful negative finding: `min_projected_gain_bits=0/32/64/128/256` all tie for the best result with the selected remaining parameters. **The future-value floor did not drive the selected policy on this development set; persistence/recent evidence did.**

## New holdout

The holdout contains the six individual Silesia files not evaluated in previous POLLICINO pilots:

- `mozilla` — mixed executable/application tar;
- `mr` — MRI/DICOM;
- `nci` — chemical structure database;
- `samba` — source-project tar;
- `sao` — astronomical binary database;
- `webster` — English dictionary/HTML.

Raw sizes and official MD5 values are checked after download; SHA-256 values are recorded in `holdout-manifest.json`. Only the first 4096 bytes of each file are entropy-coded in this pilot.

### Aggregate result

| Method | Mean payload bpb |
|---|---:|
| Oracle `min(cheap, neural)` | **3.7113** |
| Always neural | 3.7116 |
| PILOT-009 sequential | **3.7139** |
| PILOT-010 stability/value | 3.7776 |
| Cheap gate | 3.8120 |
| zlib | 3.3893 |
| zstd-19 | **3.3066** |

PILOT-010 improves categorical route accuracy from **3/6 to 4/6**, and reduces neural routes from **6/6 to 1/6**. However that is not enough: mean regret relative to the better of cheap/neural worsens sharply:

```text
PILOT-009 oracle regret     0.00260 bpb
PILOT-010 oracle regret     0.06628 bpb
```

That is the central result of this pilot.

## Why route accuracy is the wrong objective

The errors have asymmetric cost.

`mr`, `nci`, and `sao` are cases where rejecting neural is reasonable or almost harmless. But two missed specialists are expensive:

```text
mozilla
cheap       2.62964 bpb
neural      2.57666
PILOT-009   2.57886  neural @ 8
PILOT-010   2.62964  cheap @ 15
lost        ~0.05298 bpb

samba
cheap       3.69360 bpb
neural      3.37231
PILOT-009   3.37476  neural @ 8
PILOT-010   3.69360  cheap @ 64
lost        ~0.32129 bpb
```

Conversely, some PILOT-009 false-positive neural routes cost only a few thousandths of a bit per byte. Treating every false positive and false negative as one classification error therefore optimizes the wrong quantity.

`webster` is the successful stability case: neural remains clearly useful and PILOT-010 activates it at byte 16.

## Compute control

PILOT-010 does achieve its secondary goal very strongly on this runner:

```text
                         PILOT-009      PILOT-010
mean specialist calls      4096          727.8
mean encode seconds        7.09           3.47
neural routes               6/6            1/6
```

The encode-time values are environment-specific and are reported only as measurements; they never enter the routing decision.

## Regression controls

On the 4096-byte controls:

```text
self-v2
always neural     1.78979 bpb
PILOT-009         1.79834  neural @ 8
PILOT-010         1.81079  neural @ 15

repetition aaa
cheap/P9/P10      0.01270  cheap @ 64

random64
cheap/P9/P10      6.26245  cheap @ 64
```

So stability gating preserves the in-domain specialist but pays extra probe tax, while keeping obvious repetition/random controls on the cheap route.

## Conclusion

**PILOT-010 is a negative result for hard stability gating as the default compression policy, but a positive result for compute control.**

It demonstrates that the next routing objective should not be categorical `cheap` vs `neural` accuracy. It should minimize the actual cost of the decision, especially:

```text
oracle regret = selected_payload_bpb - min(cheap_bpb, neural_bpb)
```

possibly under an explicit compute budget.

The next experiment should therefore be **regret-aware rather than threshold-aware**: track deterministic bit credit/debt and optimize asymmetric decision cost, rather than adding another stricter confidence threshold.

## Reproducibility

Scientific run:

- GitHub Actions run: `31961700260`;
- run head: `69582d8f6dbc22baf326be446459fd857a06e0b6`;
- tests before benchmark: **55 passed in 4.24s**;
- result artifact: `9267494975`;
- artifact digest: `sha256:03e21b1f9f5374d7f3c051de93d81e577e0c240a4fd200626a40ac1ac51fc51d`.

The checkpoint, downloaded corpus archives, workflow trigger, and one-shot workflow are not part of the permanent experiment record. The repository retains the implementation, tests, protocol, result tables, provenance hashes, and aggregate conclusions.
