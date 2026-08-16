# PILOT-009 — Confidence-Aware Sequential Routing

PILOT-009 replaces PILOT-008's fixed 256-byte probe with a deterministic sequential decision. While routing is undecided, bytes are coded by the cheap gate and the exact quantized likelihood of cheap versus neural is accumulated. The router can activate the neural specialist early, reject it early, or default to cheap when evidence remains ambiguous.

## Architecture

`SequentialSpecialistRouterCDFProvider` lives in `src/pollicino/compression/sequential_routing.py`.

For byte `i`, the decision uses only bytes `< i`:

```text
cheap universal path ----\
                         exact likelihood evidence
neural specialist -------/          |
                                    / \
                         strong neural  strong cheap
                              |             |
                         neural lock     cheap lock
                              |             |
                         keep neural     stop neural compute
```

There is no selector side stream. Encoder and decoder reconstruct the same decision from the same already-decoded prefix. Once cheap is locked, the neural specialist is no longer evaluated.

## Frozen model provenance

PILOT-009 does **not** retrain the neural model. An early execution attempt exposed that retraining with a newer PyTorch build does not reproduce the historical tensor fingerprint exactly. The final experiment therefore loads the immutable `winner.pt` from the successful PILOT-003 artifact:

- historical artifact id: `9243314314`;
- artifact ZIP SHA-256: `72a2f5c06088401f64d06f2aaead014a55015715b5dc1abb1b787567750d11b5`;
- checkpoint: `winner.pt`, 600,933 bytes;
- checkpoint SHA-256: `713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7`;
- canonical tensor/model fingerprint: `354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`.

`run_exact.py` is the canonical experiment entrypoint. It replaces the old retraining helper with `exact_checkpoint.py` and refuses to proceed if provenance checks fail.

## Development policy selection

No new holdout data is used to choose the policy. Development consists only of already-consumed PILOT-007 Silesia streams and the PILOT-008 Large Corpus subset.

A neural route is labelled worthwhile when the previously measured neural payload improves the cheap payload by at least **0.05 bpb**. This is an explicit engineering policy choice, not an information-theoretic constant.

The search grid is:

- minimum observations: `8 / 16 / 32`;
- maximum undecided probe: `64 / 128 / 256` bytes;
- symmetric likelihood margins: `2:1`, `4:1`, `16:1`, `256:1` and reciprocals.

Selection prioritizes: classification accuracy, then fewer false-positive neural activations, then fewer false negatives, then earlier decisions.

Selected policy:

```text
min_observations = 8
max_probe_bytes  = 64
activate neural  if P_neural / P_cheap > 256
reject neural    if P_neural / P_cheap < 1/256
otherwise        cheap at byte 64
```

On the nine development streams it classifies 7/9 correctly, with one false positive and one false negative, and a mean simulated decision point of 22.78 bytes.

## Correctness

Final GitHub Actions run `31946290055` executed the deterministic compression suite before any benchmark:

**48 tests passed**.

It then completed calibration, the new holdout, independent encode/decode round-trips, and artifact upload.

Artifact: `9263447642`  
Artifact digest: `sha256:7af61734487b1292a45bf992144d125701208b1274432bdbb63c0b08ba459a6f`

Several earlier one-shot runs failed before calibration/holdout because of checkpoint provenance or artifact-download plumbing. They did not change the policy grid, development labels, or holdout definition.

## New holdout — Pizza&Chili pseudo-real subset

The frozen holdout contains five 100 MiB pseudo-real repetitive files spanning XML, DNA, English, proteins, and source code. Only the first 4,096 bytes are entropy-coded in this pilot; full-file and sample SHA-256 values are frozen in `holdout-manifest.json`.

| file | cheap bpb | neural bpb | fixed-256 router | sequential | route | decision |
|---|---:|---:|---:|---:|---|---:|
| `xml-mut` | 3.8276 | **3.7717** | 3.8203 | **3.7739** | neural | 9 |
| `dna-mut` | **1.9792** | 1.9746 | 1.9761 | **1.9792** | cheap | 64 |
| `english-mut` | 3.9636 | **3.7061** | 3.7751 | **3.7078** | neural | 12 |
| `proteins-mut` | **4.3289** | 4.3279 | **4.3289** | 4.3301 | neural | 18 |
| `sources-mut` | 3.9580 | **3.8262** | 3.8760 | **3.8284** | neural | 9 |

Mean payload:

| method | mean bpb |
|---|---:|
| cheap gate | 3.6115 |
| always neural | **3.5213** |
| PILOT-008 fixed router | 3.5553 |
| **PILOT-009 sequential router** | **3.5239** |
| zlib | 2.9770 |
| zstd-19 | **2.8301** |

The sequential router is only about **0.0026 bpb** behind always-neural on this holdout while improving the fixed router by about **0.0314 bpb**. It decides after **22.4 bytes on average**, rather than waiting for a fixed 256-byte probe.

The result is not universal compression superiority: zlib and zstd still win on average here. The result is about **routing efficiency and specialist control**.

## Compute behavior

The useful case is `dna-mut`: the sequential router keeps cheap after 64 bytes and evaluates the neural specialist only 64 times. Its encode time is about 2.55 s versus 6.61 s for always-neural on the same runner, while producing exactly the cheap payload.

When neural wins strongly, the router activates rapidly:

- XML: byte 9;
- English: byte 12;
- source code: byte 9.

Because the current neural path is still expensive, an early neural activation can be slightly slower than always-neural due to the initial dual evaluation. Future work should optimize the probe/evidence path rather than interpreting these prototype timings as production throughput.

## Regression controls

On 4,096-byte reporting slices:

| control | sequential | route / decision | cheap | neural |
|---|---:|---|---:|---:|
| `self-v2-test` | **1.7983** | neural @ 8 | 3.8987 | **1.7898** |
| `aaa.txt` | **0.0127** | cheap @ 64 | **0.0127** | 0.0139 |
| `random.txt` | 6.2625 | cheap @ 64 | 6.2625 | **6.2617** |

This is a major routing improvement over PILOT-008: the domain specialist is recognized almost immediately, while obvious repetition and effectively random mismatch stop paying neural compute after the bounded evidence phase.

## Remaining failure mode

`proteins-mut` is a false-positive activation. Cheap and neural differ by only about 0.001 bpb, but early evidence crosses the strong 256:1 threshold and the router commits neural at byte 18. The routing mechanism therefore works, and the fixed-probe tax is largely removed, but a single cumulative likelihood threshold is not yet a complete notion of **expected downstream value**.

The next research question should include persistence/stability of evidence or an explicit estimate of recoverable future bits, rather than simply making the likelihood margin even larger after observing this holdout.

## Reproducibility files

- `run.py`: core experiment and frozen policy search;
- `run_exact.py`: canonical entrypoint using the immutable checkpoint;
- `exact_checkpoint.py`: historical artifact retrieval and integrity checks;
- `results.json`: aggregate and per-file result record;
- `candidate-policies.csv`: complete policy search table;
- `holdout.csv`: per-file holdout measurements;
- `holdout-manifest.json`: external file provenance;
- `controls.csv`: regression controls.

## Limits

- Pizza&Chili pseudo-real data is deliberately repetitive and is not a general real-world benchmark;
- only 4 KiB prefixes are entropy-coded in this pilot;
- the 0.05 bpb development label threshold is an engineering policy choice;
- neural payload accounting assumes the specialist checkpoint is already shared;
- no claim of universal superiority over zlib/zstd is supported.
