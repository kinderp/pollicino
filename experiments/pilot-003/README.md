# PILOT-003 — Crossing the line

Goal: measure model capacity, integer-CDF precision, and container overhead at fixed context_length=32.

The first one-shot run found that the split hashes recorded by PILOT-001/002 are not reconstructible from a clean checkout of the merged Git tree. PILOT-003 therefore creates `pollicino-self-v2-clean-git` from the clean checkout, records its hashes, and treats the PILOT-002 winner architecture (`d_model=48`, 2 layers, context 32) as an internal control. This is an explicit methodological correction, not a silent dataset substitution.

Protocol:
- quick sweep: control plus five larger models, selected by validation bpb;
- confirmation: top two models, three seeds, 300 steps;
- final winner: seed 1337, 500 steps;
- precision sweep: 12–18 bits on 2048 bytes;
- size sweep: 512, 1024, 2048, 4096 and 8192 bytes.

POL1 remains the production experiment format. Two research-only shared-model header variants are measured: P2S1 (61 bytes, full data SHA-256 + 128-bit model fingerprint) and P2T1 (45 bytes, truncated 128-bit data/model fingerprints).

Model selection uses validation only. Test data is reserved for reporting and codec evaluation.
