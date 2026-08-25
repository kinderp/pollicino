# POLLICINO Roadmap

This roadmap is ordered from claims we can prove to claims that require progressively more assumptions, compute or physical evidence.

Status vocabulary:

- **DONE** — implemented and validated at the stated scope;
- **ACTIVE** — implementation exists or the next experiment is defined, but a required validation is still pending;
- **PENDING** — not yet established;
- **DEFERRED** — deliberately postponed until an earlier dependency produces evidence.

## Track A — Compression and generative identification

### A0 — Scientific foundations

**DONE**

- exact-lossless criterion;
- 8 bits/byte uniform 256-symbol baseline;
- SHA-256 round-trip verification;
- reproducibility metadata and immutable experiment records.

**PENDING / hardening**

- one canonical benchmark-corpus policy across all future model families;
- one unified experiment-manifest generator covering all backends and pilots.

### A1 — Executable pilot line

**DONE through PILOT-013.**

The repository contains a sequence of reproducible compression/routing experiments through **PILOT-013 — cheap admission routing**. PILOT-013 is retained as a negative/qualified result: the hard neural-compute cap succeeded, while the preregistered retained-gain target did not.

**NEXT CANDIDATE**

- define PILOT-014 only after choosing the exact next hypothesis and preregistered gate;
- do not label a PILOT-014 result until code, provenance and measured output are merged.

### A2 — Statistical/classical ladder

Target learning sequence:

```text
uniform
 -> empirical byte frequency
 -> bigram
 -> n-gram / Markov
 -> RLE / Huffman teaching implementations
 -> arithmetic/range coding
 -> gzip / bzip2 / xz / zstd baselines
```

**Exit criterion:** theoretical log loss and realized coded size agree within expected finite-coder overhead.

### A3 — Neural foundations

Target learning sequence:

```text
scalar neuron
 -> manual gradient descent
 -> tensor/vector form
 -> MLP next-byte predictor
 -> autograd/backprop
 -> RNN/GRU baseline
```

**Exit criterion:** a learned predictor beats simple statistical baselines on a controlled holdout without leakage.

### A4 — Byte Transformer / PyTorch

- byte vocabulary 256;
- embeddings;
- RMSNorm;
- RoPE;
- causal self-attention;
- Transformer block;
- next-byte head;
- transparent AdamW loop;
- checkpointing and validation;
- controlled tiny -> small -> medium scaling only when justified.

### A5 — MLX parity

- same model specification;
- shape and parameter-count parity;
- initialization/precision comparison;
- learning-curve comparison;
- Apple unified-memory throughput and peak-memory benchmark.

### A6 — Deterministic neural lossless codec

- deterministic probability -> integer-frequency conversion;
- encoder/decoder probability parity;
- arithmetic/range coder integration;
- stream version/model identity;
- independent round-trip tests;
- SHA-256 verification of every reconstruction.

### A7 — Scientific benchmark

Domains:

- text;
- source code;
- JSON/XML/CSV;
- raw/uncompressed binary/media;
- already-compressed formats;
- cryptographically random negative control.

Metrics:

- theoretical and realized bits/byte;
- payload/checkpoint/model-description bytes;
- encode/decode throughput;
- memory;
- training-cost proxy;
- exact round-trip result.

### A8 — Hybrid POLLICINO

Per chunk, compare:

```text
content-address reference
learned entropy coding
classical compression
raw/residual fallback
```

Add content-defined/deterministic chunking, shared-store accounting and a deterministic routing policy.

### A9 — Generative identification

Study:

```text
shared model
 + fingerprint/residual bits
 + deterministic candidate search
 -> full-hash verified exact object
```

Primary question: can shared learned side information make `short fingerprint + search` competitive with ordinary entropy coding in any useful regime?

### A10 — Bandwidth / compute frontier and publication

- sweep residual/fingerprint sizes;
- measure decoder search effort;
- construct Pareto frontiers;
- reproduce key results on a second backend/machine;
- freeze benchmark versions;
- publish educational and technical reports only at the claim level supported by evidence.

---

# Track B — PollicinoNet software

Core contracts:

```text
DISCOVERY -> transmit enough to locate/rendezvous
EXACT     -> reconstruct byte-identical authoritative data
SEMANTIC  -> perceptual/realtime reconstruction, explicitly lossy
```

Primary accounting metric:

```text
TRC =
    discovery bits
  + rendezvous bits
  + manifest bits
  + payload/reference/residual bits
  + FEC bits
  + acknowledgement bits
  + retransmission bits
```

## PN-001 — Compact standalone discovery

**DONE**

- deterministic PND1 wire descriptor;
- compact discovery/rendezvous semantics;
- transport-independent core.

## PN-002 — Scarce-link simulator and exact framing

**DONE**

- deterministic impairment model;
- PNF1 fragmentation/reassembly;
- stop-and-wait retries;
- duplicate handling;
- ACK accounting;
- deterministic byte/TRC-relevant measurements.

**NEXT**

- consume physical RF replay traces in addition to synthetic loss probabilities;
- add explicit interruption/resume state above frame retry.

## PN-003 — Coordinate -> rich-network retrieval

**DONE**

- opaque rotating/scoped rendezvous coordinate;
- PNM1 full manifest;
- resolver/provider ports;
- final full-hash verification.

## PN-004 — Adaptive exact delivery

**DONE**

- application-independent authorization gate;
- rich-path preference;
- scarce-link fallback;
- honest accounting when a rich-path attempt fails.

## PN-005 — P2P chunk store and reconstruction

**DONE**

- SHA-256 content-addressed chunks;
- PCM1 manifests;
- PNA1 availability summaries;
- missing-chunk synchronization;
- measured cache/traffic curve.

**NEXT**

- resumable multi-session synchronization;
- delta/patch experiments against prior versions;
- store-and-forward scheduling across intermittent peers.

## PN-006 — Optional DNA integration

**DONE**

- reversible `DNATrace v0.1` adapter;
- inline/reference selection;
- standalone PollicinoNet core remains independent of DNA.

**DEFERRED EXPANSION**

- broader Travel DNA field prototype after exact-session/resume behavior is stable.

## PN-007 — Real scarce-link hardware pilot

**ACTIVE**

The first target is LoRa on two LILYGO/TTGO LoRa32 V1.6.1 / SX1276 boards.

Physical progression:

- HW-001 — **DONE:** bidirectional byte-exact PND1/PNF1 transport;
- HW-002 — **DONE:** RSSI/SNR, RTT and airtime instrumentation;
- HW-002T — **DONE:** polling/timing characterization;
- HW-003 — **DONE:** event-driven FreeRTOS receive path;
- HW-004 — **DONE:** 48-attempt CRC/direction/frame-size matrix, 48/48 success, 0 CRC events;
- HW-005 — **DONE:** 10/8/6/4/2 dBm staircase, 20/20 success;
- HW-006 — **ACTIVE:** untethered responder software/build validated; distance/NLOS physical evidence pending.

Frozen HW-006 checkpoint order:

```text
tethered preflight
 -> same-room one-port
 -> greater same-room separation
 -> one wall
 -> multiple walls
 -> another floor
 -> outdoor distance
```

Keep 42-byte frames and 2 dBm initially. Do not change PHY parameters until a real transition region appears.

## PN-008 — Semantic realtime branch

**PENDING**

Separate from authoritative EXACT data:

- ultra-low-bitrate speech baseline;
- semantic/latent speech residual experiment;
- facial landmarks/avatar state;
- explicit perceptual quality and latency metrics.

Never represent SEMANTIC output as exact DNA state, signatures, consent or cryptographic material.

---

# Track C — RF evidence and simulator calibration

## RF-001 — Evidence catalog

**ACTIVE / implementation added**

Normalize supported physical records without silently combining overlapping raw and derived summaries.

Required outputs:

- lab/schema coverage;
- frame-size and TX-power coverage;
- checkpoint names;
- normalized success/failure counts per evidence record;
- RSSI/SNR/RTT/IRQ metrics when actually present;
- provenance links where recorded.

## RF-002 — Deterministic physical trace replay

**ACTIVE / implementation added**

- extract ordered samples from raw HW-002 benchmarks;
- accept future executed HW-006 checkpoint records;
- preserve ambiguous untethered timeouts;
- never impute remote RSSI/SNR for failed HW-006 attempts;
- fail if replay requests more physical samples than recorded unless explicit synthetic repetition is enabled.

## RF-003 — Replay-driven exact-session testing

**NEXT**

Feed physical outcome traces into:

- PNF1 retry tests;
- resumable transfer/session logic;
- P2P missing-chunk synchronization;
- TRC accounting.

The trace is evidence, not a universal channel model.

## RF-004 — HW-006 calibration set

**BLOCKED ONLY BY TEMPORARY HARDWARE ACCESS**

When the boards are available, record controlled same-room/distance/NLOS checkpoints with explicit geometry, antenna orientation, frame size, TX power, airtime budget and occupancy pacing.

Do not infer a deployment packet-loss probability from a small checkpoint sample.

---

# Immediate implementation order

1. **RF evidence catalog + deterministic trace replay.**
2. **Roadmap/status synchronization.**
3. **Resumable EXACT session state above the existing PNF1 retry layer.**
4. **Replay-driven interruption/recovery tests and TRC accounting.**
5. **HW-006 physical checkpoint campaign when hardware access returns.**
6. **Calibrate the synthetic scarce-link model from measured evidence.**
7. **Only then choose whether PHY/radio changes or the next compression pilot are justified.**
