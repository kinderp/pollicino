# PILOT-003 — Crossing the line

Goal: move from the near-tie observed in PILOT-002 to a result that separates three effects:

1. **model capacity** at fixed `context_length=32`;
2. **integer-CDF precision** (`12..18` bits);
3. **container overhead** as file size grows.

The experiment keeps `pollicino-self-v1` frozen and verifies its train/validation/test SHA-256 values before training.

## Protocol

- quick sweep: five models immediately above the PILOT-002 winner, selected by validation bpb;
- confirmation: top two models, three seeds, 300 steps;
- final winner: seed 1337, 500 steps;
- precision sweep: 12–18 bits on the frozen 2048-byte coding slice;
- size sweep: 512, 1024, 2048, 4096 and 8192 bytes.

`POL1` remains the production experiment format. Two **research-only shared-model header variants** are measured:

- `P2S1` (61 bytes): full SHA-256 for decoded data, 128-bit model fingerprint;
- `P2T1` (45 bytes): 128-bit truncated data and model fingerprints.

The variants exist to measure overhead; they are not silently substituted for `POL1`.

## Selection rule

Model selection uses **validation only**. Test data is reserved for reporting and codec evaluation.

## One-shot Actions run

The temporary workflow `.github/workflows/pilot-003.yml` is intentionally configured to execute only when the pushed commit message contains `Run PILOT-003 experiment`. It is removed after the result artifact is collected.
