# PILOT-004 — Cross-domain generalization

PILOT-004 asks whether the `m80-l2/context32` model that crossed zlib on `pollicino-self-v2-clean-git` in PILOT-003 generalizes **without fine-tuning** to unrelated data.

## External benchmark

The primary benchmark is the fixed Canterbury Corpus (`cantrbry.zip`), a classic lossless-compression corpus containing 11 files across English text, Shakespeare, HTML, C, LISP, Excel spreadsheet, technical writing, poetry, fax data, a SPARC executable and a GNU manual page.

Source: `https://corpus.canterbury.ac.nz/resources/cantrbry.zip`

Archive SHA-256: `c44b686dfc137e74aba4db0540e5d6568cb09e270ba8f8411d2f9df24f39a1a6`.

The Artificial Corpus is used only as a control for pathological inputs (`aaa.txt`, periodic alphabet, random 64-symbol text and a one-byte file).

Source: `https://corpus.canterbury.ac.nz/resources/artificl.zip`

Archive SHA-256: `6d02ab02183a4cdbc39afb812b9fd038b44c97a2276b6d7afa79516ee69645f3`.

Individual file sizes and SHA-256 values are frozen in `external-manifest.json`.

## Model and protocol

- training data: **only** `pollicino-self-v2-clean-git`;
- no Canterbury/Artificial fine-tuning;
- architecture: `m80-l2`, context 32, 148,096 parameters;
- 500 deterministic AdamW steps, seed 1337;
- canonical tensor/model fingerprint: `354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117`;
- this fingerprint matches the PILOT-003 winner;
- the raw `torch.save` archive SHA is recorded but is not treated as the canonical model identity because serialization containers can differ while tensors are identical;
- zero-shot evaluation uses exact sliding context on at most the first 65,536 bytes of each file;
- real `POL1` round-trips use the first 2,048 bytes of representative files at 18-bit CDF precision.

## Main result: PILOT-003 does not generalize zero-shot

Weighted over the Canterbury evaluation prefixes:

| method | bpb |
|---|---:|
| POLLICINO `m80-l2` zero-shot | **8.759** |
| zlib | 2.465 |
| gzip | 2.467 |
| zstd-19 | **2.220** |

POLLICINO beats zlib on **0/11 Canterbury files** in zero-shot model bpb and on **0** representative files after real range coding plus the `POL1` container.

### By broad domain

| group | POLLICINO | zlib | zstd-19 |
|---|---:|---:|---:|
| text | 5.160 | 3.125 | 2.956 |
| source / markup | 6.953 | 2.488 | 2.420 |
| binary / structured | 14.842 | 1.421 | 1.014 |

Text transfers partially—the model is typically around 4.8–5.6 bpb—but binary domains expose severe overconfidence: spreadsheet, fax and executable data reach roughly 11–16 bpb. A probabilistic model is allowed to exceed 8 bpb when it assigns very low probability to the observed byte.

## Real lossless coding checks

Representative 2,048-byte slices all round-trip byte-perfect. Examples:

| file | category | payload bpb | POL1 bpb | zlib bpb |
|---|---|---:|---:|---:|
| alice29.txt | English text | 4.865 | 5.227 | 4.070 |
| fields.c | C source | 6.065 | 6.426 | 3.512 |
| kennedy.xls | spreadsheet | 15.125 | 15.488 | 3.480 |
| ptt5 | fax | 16.001 | 16.363 | 0.090 |
| sum | executable | 14.594 | 14.957 | 2.871 |

The shared-model numbers above **do not transmit the checkpoint**. The checkpoint is about 603,141 bytes. If it had to be sent with every 2 KiB file, the effective rate would exceed 2,300 bpb. Even amortized once over the complete 2.81 MB Canterbury corpus, the checkpoint alone costs about 1.717 bpb.

## Artificial controls

The controls reinforce the same conclusion. A model trained on project source does not automatically adapt to an unseen repetition regime: `aaa.txt` is about 10.37 bpb for the frozen neural model while zlib is near zero. The random 64-symbol file is about 11.64 bpb versus roughly 6.06 bpb for zlib.

This is not a bug in arithmetic coding; it is a **model mismatch** result.

## Interpretation

PILOT-003 demonstrated strong **domain-specific learned compression**. PILOT-004 shows that the same frozen predictor is not universal and is often confidently wrong out of distribution. The next research step should therefore not be another blind capacity increase on the self-corpus.

Promising directions are:

1. mixed-domain pretraining with a strictly held-out external test corpus;
2. causal/online adaptation that encoder and decoder can reproduce without transmitting updated weights;
3. domain routing or mixture-of-experts with explicit model-selection cost;
4. calibration/fallback mechanisms that avoid catastrophic >8 bpb predictions on unfamiliar bytes;
5. only after that, renewed scaling experiments.

## Reproducibility

GitHub Actions run: `31874725115`  
Artifact: `9244449511`  
Artifact digest: `sha256:6ed76e8b4f2f53d4b9294df9dad773c16e9c49f79cf6c3d7b781af805761c3c7`

The one-shot workflow used to obtain an independent runner was removed before merge. The checkpoint and downloaded corpus archives are not committed; their hashes and sizes are recorded.
