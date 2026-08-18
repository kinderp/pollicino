# PILOT-013 — Cheap Admission Before Neural Compute

PILOT-012 established that 512-byte block resets are valuable on mixed-domain streams, but its regret router still starts a neural probe in every block. PILOT-013 asks whether cheap-only causal evidence can decide which blocks are worth waking the neural path for while enforcing a hard 50% neural budget.

## Mechanism

`CheapCodelengthAdmissionBlockCDFProvider` resets the cheap path at deterministic 512-byte boundaries, codes a short cheap-only probe, accumulates exact quantized likelihood, and instantiates the neural specialist only when the frozen integer codelength band admits the block and the remaining stream budget can pay for it. No floating-point route decision and no selector side stream are required.

The primary compute metric is actual uncached PyTorch model forward evaluations per source byte, not wrapper calls.

## Frozen policy and provenance

Run `31988642119` completed development selection and froze the policy before fresh-holdout access:

- block: 512 bytes;
- probe: 16 bytes;
- cheap probe codelength band: 88–128 bits (5.5–8.0 bpb);
- maximum admitted bytes: 2048 (50%).

That first run then stopped on incorrect preregistered Git-blob annotations before any holdout metric was produced. `run_frozen.py` fixes only the Go/Node provenance identifiers, reruns development, and refuses fresh-source access unless it reproduces the exact frozen policy. The policy was not retuned.

Final successful run: `31989172942`, scientific head `ba6eb338d47ceaac170358c1f26ba6c5d5f4b4ff`, **76 tests passed**. Artifact `9274906515`, digest `sha256:c5d66b042ff04c5285c252b4088def77b45595f1aab80979883811ccc8d128a0`.

## Fresh holdout

Fresh external sources, opened only after freeze verification:

- Go `src/net/http/server.go`, tag `go1.22.12`, Git blob `23a603a83dd7135077fa1363ceb8255ff345ac06`;
- Node.js `lib/internal/modules/cjs/loader.js`, tag `v20.19.1`, Git blob `ebccdb28256314e7cd8ac8d7e3dec670286022d2`.

Six deterministic 4096-byte mixed streams combine those bytes with JSON, DNA, random, repetition, compressed and English-like controls.

## Final result

PILOT-013 is a **technical success but a negative result for the preregistered scientific hypothesis**.

| Method | Mean payload (bpb) | Mean actual neural eval fraction |
|---|---:|---:|
| cheap reset | 4.88997 | 0 |
| neural reset | 4.50500 | ~0.945 |
| PILOT-012 max | 4.53141 | 0.80835 |
| PILOT-013 admission | 4.74414 | 0.45610 |
| diagnostic 50% oracle | 4.63615 | ~0.50 budget |
| zlib | 4.18034 | n/a |
| zstd-19 | 4.05436 | n/a |

PILOT-013 stays below the hard budget on every stream (`max = 0.49902`), admits 50% of bytes on average, and beats cheap reset on 6/6 streams. But it retains only **36.86%** of the mean cheap-reset → neural-reset gain, below the frozen 50% success threshold, and beats PILOT-012 max on 0/6 streams.

## Interpretation

The mechanism works; the one-dimensional signal does not work well enough. Cheap probe codelength alone is a poor predictor of which blocks deserve neural compute. The diagnostic 50%-budget oracle reaches 4.63615 bpb, leaving a meaningful selection gap at the same nominal budget.

The next pilot should improve the *selection signal*, not silently increase neural compute: richer causal/integer cheap-only features, followed by a tiny deterministic decision tree or quantized linear scorer trained only on already-consumed streams.

## Persisted evidence

- `results.json` — aggregate protocol/result record;
- `holdout.csv` — per-stream fresh-holdout outcomes;
- `holdout-manifest.json` — exact source and stream provenance;
- `run-metadata.json` — successful run, artifact digest, frozen-policy provenance and checkpoint identity.

The complete raw development/block tables remain in the GitHub Actions artifact identified above; its SHA-256 digest is the canonical checksum for that bundle.

## Limits

- The holdout is a deterministic mixed-domain mechanism benchmark, not a universal compression corpus.
- The admission feature is intentionally one-dimensional.
- The 50% diagnostic oracle is non-causal and uses independently coded block sums.
- The frozen neural checkpoint is assumed shared whenever the neural path is admitted.
- Future pilots should share the exact deployed integer decision helper between search/screening and codec evaluation so boundary behavior cannot diverge.
