# POLLICINO Roadmap

The roadmap is intentionally ordered from things we can prove and measure to the more speculative research hypothesis.

## Phase 0 — Foundations and scientific invariants

- [x] Define the project question and exact-lossless criterion.
- [x] Establish the uniform 256-byte baseline: 8 bits/byte.
- [x] Establish SHA-256 round-trip verification.
- [x] Define reproducibility metadata.
- [ ] Define benchmark corpus policy and train/validation/test separation.
- [ ] Implement experiment manifest generation.

**Theory:** bits, probability, self-information, entropy, cross-entropy, KL divergence, pigeonhole principle, hashes, MDL and Kolmogorov complexity.

## Phase 1 — Classical and statistical compression

- [ ] Empirical byte-frequency predictor.
- [ ] Bigram predictor.
- [ ] General n-gram / Markov predictor.
- [ ] RLE teaching implementation.
- [ ] Huffman teaching implementation.
- [ ] Arithmetic/range coder with exact integer frequency tables.
- [ ] Benchmark harness for gzip, bzip2, xz and zstd.

**Exit criterion:** theoretical log loss and realized coded size agree within the expected finite-coder overhead.

## Phase 2 — Neural foundations

- [ ] Scalar neuron and manual gradient descent.
- [ ] Tensor/vector formulation.
- [ ] MLP next-byte predictor.
- [ ] Autograd and backpropagation experiments.
- [ ] RNN/GRU baseline.
- [ ] Overfitting, regularization and validation experiments.

**Exit criterion:** a learned predictor beats simple statistical baselines on at least one controlled domain without leakage.

## Phase 3 — Byte Transformer / PyTorch

- [ ] Byte embedding, vocabulary size 256.
- [ ] RMSNorm.
- [ ] RoPE.
- [ ] Causal self-attention.
- [ ] Transformer block.
- [ ] Next-byte softmax head.
- [ ] Transparent training loop with AdamW.
- [ ] Checkpointing, validation and metrics.
- [ ] Controlled scaling: tiny -> small -> medium only when justified.

**Exit criterion:** a from-scratch PyTorch Transformer trains reproducibly and reports validation bits/byte.

## Phase 4 — MLX parity

- [ ] Mirror the PyTorch architecture in MLX.
- [ ] Verify tensor shapes and parameter-count parity.
- [ ] Compare initialization policy and numerical precision.
- [ ] Compare learning curves on the same byte corpus.
- [ ] Benchmark Apple unified-memory throughput and peak memory.

**Exit criterion:** the same YAML model spec drives equivalent PyTorch and MLX experiments.

## Phase 5 — Neural lossless codec

- [ ] Convert model probabilities to deterministic integer frequencies.
- [ ] Guarantee encoder/decoder probability parity.
- [ ] Integrate range/arithmetic coding.
- [ ] Add stream header/version/model identity.
- [ ] Add independent round-trip tests.
- [ ] Verify every reconstructed file with SHA-256.

**Exit criterion:** real `.pol` payloads decode bit-perfectly using the shared model.

## Phase 6 — Scientific benchmark

Domains:

- [ ] text,
- [ ] source code,
- [ ] JSON/XML/CSV,
- [ ] raw/uncompressed binary and media,
- [ ] already-compressed formats,
- [ ] cryptographically random bytes as negative control.

Metrics:

- [ ] theoretical bits/byte,
- [ ] realized bits/byte,
- [ ] payload bytes,
- [ ] checkpoint bytes,
- [ ] amortized description length,
- [ ] encode/decode throughput,
- [ ] memory,
- [ ] training cost proxy,
- [ ] exact round-trip result.

## Phase 7 — Hybrid POLLICINO

At chunk level choose among:

```text
content-address reference
learned entropy coding
classical compression
raw/residual fallback
```

- [ ] Content-defined chunking experiment.
- [ ] Shared chunk-store accounting.
- [ ] Policy for choosing encoding mode.
- [ ] End-to-end container format experiment.

## Phase 8 — Generative Identification Compression

- [ ] Define model-ranked candidate spaces.
- [ ] Define exact fingerprint semantics.
- [ ] Add progressively sized fingerprints.
- [ ] Enumerate/search candidates deterministically where possible.
- [ ] Verify the final candidate with a full cryptographic hash.
- [ ] Measure candidate count and reconstruction compute.

**Core question:** can side information learned by a shared model make `short fingerprint + search` competitive with ordinary entropy coding in any useful regime?

## Phase 9 — Bandwidth / compute frontier

- [ ] Sweep fingerprint/residual sizes.
- [ ] Measure decoder search effort.
- [ ] Construct Pareto frontiers.
- [ ] Study domain dependence.
- [ ] Compare against pure entropy coding at equal model cost.

## Phase 10 — Scale and publication

Scale only when earlier experiments demonstrate a stable trend.

- [ ] Decide whether local NVIDIA/CUDA hardware is justified.
- [ ] Reproduce key results on a second machine/backend.
- [ ] Freeze benchmark version.
- [ ] Write educational release.
- [ ] Write technical report.
- [ ] Prepare a research manuscript only if the evidence supports a novel claim.

---

# Parallel research track — PollicinoNet

PollicinoNet applies the POLLICINO information-minimization idea to scarce and intermittent networks. The first target is LoRa, but the contracts remain transport-independent.

Core modes:

```text
DISCOVERY -> transmit enough to locate/rendezvous
EXACT     -> reconstruct the exact original bytes
SEMANTIC  -> reconstruct a perceptually equivalent realtime signal
```

Detailed architecture: [`docs/research/pollicinonet.md`](docs/research/pollicinonet.md).

## PN-001 — Compact DNA Trace

- [ ] Use `kinderp/dna` `DNATrace v0.1` as the first real application payload.
- [ ] Compare JSON, CBOR/MessagePack, schema-aware binary encoding and generic compression.
- [ ] Include authentication/integrity overhead in on-air byte counts.
- [ ] Preserve rotating identifiers, TTL and anti-replay semantics.

**Exit criterion:** deterministic round-trip plus measured radio-byte reduction without weakening the DNA privacy contract.

## PN-002 — Scarce-link simulator

- [ ] Add payload/bitrate/airtime budgets.
- [ ] Simulate loss, duplication, reorder and intermittent gateways.
- [ ] Add deduplication, TTL, hop limits and resumable exchange.
- [ ] Measure radio bytes, retransmissions and time-to-reconstruction.

## PN-003 — Discovery coordinate -> rich-network retrieval

- [ ] Define compact PollicinoNet short coordinates as rendezvous keys, not proof of identity.
- [ ] Resolve full manifests over Internet/local P2P.
- [ ] Support content identities for Pollicino P2P, IPFS-like CIDs, BitTorrent-like hashes and HTTP resources.
- [ ] Verify the final object with its full cryptographic identity.

**Exit criterion:** arbitrary external content can be discovered using a very small scarce-link advertisement and retrieved exactly through a richer path.

## PN-004 — DNAFragment exact transport

- [ ] Integrate after DNA consent/rendezvous, never as a replacement for DNA policy.
- [ ] Treat authoritative DNA fragments as EXACT data.
- [ ] Prefer Internet/Wi-Fi/P2P, using LoRa only when a richer path is unavailable.
- [ ] Test expiry, revocation-aware cache policy and exact reconstruction.

## PN-005 — P2P chunk store and reconstruction

- [ ] Content-defined or deterministic chunking.
- [ ] Content-addressed local `PollicinoStore`.
- [ ] Exchange compact availability summaries.
- [ ] Reference known chunks instead of retransmitting them.
- [ ] Delta/patch against previous versions.
- [ ] Store-and-forward between intermittent peers.

**Primary metric:** Transmission Reconstruction Cost (TRC): all discovery, rendezvous, manifest, payload, FEC, acknowledgement and retransmission bits required to obtain a verified object.

## PN-006 — Travel DNA integration

- [ ] `DNATrace` discovery over a simulated LoRa adapter.
- [ ] GeoRoom/group rendezvous through a compact coordinate.
- [ ] Advertise route, POI, guide and Cartolina content by reference when possible.
- [ ] Hand over rich payloads to Internet/Wi-Fi/local P2P.
- [ ] Test offline/store-and-forward behavior.
- [ ] Keep radio/link details outside Travel DNA domain entities.

## PN-007 — Real LoRa hardware pilot

Only after the simulator produces stable protocol results:

- [ ] select a radio/module;
- [ ] implement a LoRa transport adapter;
- [ ] repeat PN-001..006 with measured airtime and energy;
- [ ] compare discovery-only, exact fallback and opportunistic handover modes.

## PN-008 — Semantic realtime branch

Separate from authoritative/exact DNA data:

- [ ] ultra-low-bitrate speech baseline;
- [ ] semantic/latent speech residual experiment;
- [ ] facial landmarks / avatar state;
- [ ] explicit perceptual quality and latency metrics;
- [ ] never represent SEMANTIC output as exact DNA state or signed content.
