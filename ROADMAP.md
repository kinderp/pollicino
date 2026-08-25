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
  + manifest/control bits
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
- deterministic byte/TRC-relevant measurements;
- physical RF outcome replay as an alternative transaction oracle;
- resumable exact-session state above unchanged PNF1 framing.

Physical replay keeps failed untethered transactions observationally unresolved and reports return/ACK bytes as a lower bound rather than pretending the remote path was observed.

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

**DONE at durable/session scope**

- SHA-256 content-addressed chunks;
- PCM1 manifests;
- PNA1 availability summaries;
- missing-chunk synchronization;
- measured cache/traffic curve;
- chunk-boundary resumability: later steps advertise receiver availability and skip already verified chunks;
- serializable session coordination state;
- crash-safe on-disk `DirectoryPollicinoStore` with SHA-256 verification before advertising availability;
- corrupt ordinary chunk files are treated as unavailable and may be repaired by verified re-transfer;
- atomic checksummed exact-session checkpoints using same-directory temporary files, file fsync and `os.replace`;
- tested fresh-process reconstruction of sender/receiver stores plus session state, with no retransmission of already verified chunks.

**NEXT**

- delta/patch experiments against prior versions;
- store-and-forward scheduling across intermittent peers;
- define lifecycle/garbage-collection policy for durable chunk stores.

## PN-006 — Optional DNA integration

**DONE**

- reversible `DNATrace v0.1` adapter;
- inline/reference selection;
- standalone PollicinoNet core remains independent of DNA.

**DEFERRED EXPANSION**

- broader Travel DNA field prototype after exact-session/store-and-forward behavior is stable.

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

**DONE at current schema coverage**

- normalize supported HW-001..HW-006 evidence without combining overlapping raw/derived summaries;
- report lab/schema/frame-size/TX-power/checkpoint coverage;
- preserve source-level success/failure and telemetry only when actually recorded;
- CLI smoke-tested against the repository physical-validation archive.

## RF-002 — Deterministic physical trace replay

**DONE at current raw-trace scope**

- extract ordered samples from raw HW-002 benchmarks;
- accept future executed HW-006 checkpoint records;
- preserve ambiguous untethered timeouts;
- never impute remote RSSI/SNR for failed HW-006 attempts;
- reject silent replay beyond the number of recorded samples;
- drive PNF1 retry behavior from physical transaction outcomes;
- enforce recorded frame-size compatibility by default.

Explicit `repeat=True` or disabled frame-size checking are synthetic/extrapolation modes and must not be cited as additional physical evidence.

## RF-003 — Replay-driven exact-session testing

**DONE at durable exact-session scope**

Implemented:

```text
RF trace
 -> physical success/failure oracle
 -> PNF1 retry
 -> resumable chunk session
 -> durable chunk store + atomic session checkpoint
 -> fresh-process restart
 -> final exact reconstruction
```

Accounting and persistence safeguards:

- local replayed TX bytes are exact;
- remote ACK/response bytes on failed untethered attempts remain unknown and are reported as a lower bound;
- exact deterministic-simulator accounting and lower-bound physical-replay accounting cannot be mixed in one resumed session;
- primary data, primary ACK, retry data and retry ACK bytes are non-overlapping;
- logical manifest + availability + chunk bytes are cross-checked against the physical primary/retry breakdown;
- durable chunks are verified against their content address before being advertised;
- checkpoint contents are schema-validated and SHA-256 protected;
- a failed atomic checkpoint replace leaves the previously committed state readable;
- a process restart reloads store + session state and sends only the remaining verified-missing chunks.

See [`docs/research/trc-accounting.md`](docs/research/trc-accounting.md).

**NEXT**

- extend TRC to discovery/rendezvous and future FEC without double counting;
- replay-driven store-and-forward scenarios;
- durable-store retention/garbage-collection experiments.

## RF-004 — HW-006 calibration set

**BLOCKED ONLY BY TEMPORARY HARDWARE ACCESS**

When the boards are available, record controlled same-room/distance/NLOS checkpoints with explicit geometry, antenna orientation, frame size, TX power, airtime budget and occupancy pacing.

Current 42-byte physical traces cannot be silently reused for differently sized session-control frames. The replay layer deliberately exposes this measurement gap rather than hiding it through automatic extrapolation.

Do not infer a deployment packet-loss probability from a small checkpoint sample.

---

# Immediate implementation order

Completed in this software round:

1. **RF evidence catalog + deterministic trace replay.**
2. **Roadmap/status synchronization.**
3. **Resumable EXACT session state above unchanged PNF1 retry.**
4. **RF-replay-driven PNF1/session tests with explicit evidence semantics.**
5. **Non-overlapping exact-session TRC wire accounting.**
6. **Durable content-addressed store + atomic restartable session checkpoint.**

Next software work while hardware is unavailable:

7. **Extend TRC across discovery/rendezvous and add replay-driven store-and-forward tests.**
8. **Define durable-store retention/garbage collection and delta/patch experiments.**

When hardware access returns:

9. **HW-006 controlled same-room/distance/NLOS checkpoint campaign.**
10. **Calibrate the synthetic scarce-link model from measured evidence.**
11. **Only then choose whether PHY/radio changes or the next compression pilot are justified.**
