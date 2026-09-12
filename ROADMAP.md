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

## PN-005 — P2P chunk store, durable restart, intermittent forwarding and bundle governance

**DONE at deterministic governed store-and-forward scope**

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
- tested fresh-process reconstruction of sender/receiver stores plus session state, with no retransmission of already verified chunks;
- finite directional peer contacts that transfer the PCM1 manifest only when absent, advertise verified PNA1 availability and forward at most an explicit number of source-owned missing chunks;
- multi-hop `origin -> relay -> destination` exact reconstruction without any permanent origin-to-destination path;
- durable relay restart between encounters;
- corrupt relay chunks are neither advertised nor forwarded;
- deterministic contact schedules with per-contact PNF1 transfer-id ranges and non-overlapping wire accounting;
- PNB1 forwarding envelopes bind PCM1 identity to the originating PND1 discovery and carry explicit hop position;
- PNC1 custody receipts record peer, acquisition time, hop count, verified chunk count and partial/complete state;
- PND1 `ttl_seconds` and `hop_limit` are enforced before data forwarding;
- TTL-expired and hop-exhausted encounters are rejected before consuming route wire bytes;
- explicit `contact_id` replay is zero-wire idempotent while genuinely new contacts continue to use PNA1 content-level deduplication;
- custody observations and processed contact IDs can be atomically persisted and checksum-validated across restart;
- governed multi-hop schedules preserve exact reconstruction and include PNB1/PNC1 traffic in end-to-end TRC.

See [`docs/research/store-and-forward.md`](docs/research/store-and-forward.md) and [`docs/research/bundle-governance.md`](docs/research/bundle-governance.md).

**NEXT**

- define relay storage quotas, retention and garbage collection;
- add bearer identity/cost dimensions to TRC for LoRa/BLE/Wi-Fi/Internet;
- add synthetic multi-relay routing policy comparisons while keeping measured-vs-modeled evidence explicit;
- delta/patch experiments against prior versions;
- opportunistic routing optimization only after deterministic policy primitives and evidence boundaries are stable.

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
- HW-003 — **DONE:** event-driven FreeRTOS responder;
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

## RF-003 — Replay/session/store-and-forward/governance accounting

**DONE at deterministic governed store-and-forward scope**

Implemented:

```text
RF trace / deterministic link
 -> PNF1 retry
 -> resumable chunk session
 -> durable chunk store + atomic session checkpoint
 -> intermittent verified relay custody
 -> PNB1 TTL/hop governance + PNC1 custody receipts
 -> destination exact reconstruction
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
- a process restart reloads store + session state and sends only the remaining verified-missing chunks;
- store-and-forward contacts transfer only material the source peer can verify;
- TTL/hop-blocked and duplicate-suppressed contacts are explicitly counted as dispositions and use zero route bytes when rejected from already-known local state;
- governed end-to-end TRC can include explicit PND1 discovery copies, PNM1 rendezvous copies, PNB1 bundle control, PNC1 custody receipts, PCM1/PNA1 traffic, chunk payload, ACKs, retries and future explicit FEC bytes without overlap.

See [`docs/research/trc-accounting.md`](docs/research/trc-accounting.md), [`docs/research/store-and-forward.md`](docs/research/store-and-forward.md) and [`docs/research/bundle-governance.md`](docs/research/bundle-governance.md).

**NEXT**

- per-bearer TRC for mixed LoRa/BLE/Wi-Fi/Internet routes;
- relay quota/retention/garbage-collection experiments;
- synthetic multi-relay policy experiments with clear evidence labels;
- replay-driven multi-relay calibration once measured frame-size/contact-window evidence exists.

## RF-004 — HW-006 calibration set

**BLOCKED ONLY BY TEMPORARY HARDWARE ACCESS**

When the boards are available, record controlled same-room/distance/NLOS checkpoints with explicit geometry, antenna orientation, frame size, TX power, airtime budget and occupancy pacing.

Current 42-byte physical traces cannot be silently reused for differently sized session/governance control frames. The replay layer deliberately exposes this measurement gap rather than hiding it through automatic extrapolation.

Do not infer a deployment packet-loss probability from a small checkpoint sample.

---

# Hardware evidence gate

**Physical tests are not required yet** for further protocol/software work such as:

- bearer abstraction and per-bearer accounting schemas;
- relay quotas/retention/garbage collection;
- deterministic multi-relay scheduling;
- synthetic routing-policy comparisons;
- delta/patch experiments;
- correctness, idempotency and exact-reconstruction tests.

**Physical HW-006 tests become necessary before** we claim or use measured LoRa values for:

1. contact availability at distance/NLOS;
2. usable contact-window duration;
3. realistic chunks/bytes deliverable per encounter;
4. loss/retry behavior in the transition region;
5. TTL/contact budgets derived from the radio rather than chosen synthetically;
6. automatic bearer/routing selection justified by real LoRa performance;
7. calibration of differently sized PNB1/PNC1/session-control frames;
8. any decision to change the frozen PHY.

The first required physical campaign remains the frozen HW-006 progression at **42 bytes / 2 dBm**. Once a transition region is observed, add controlled measurements for the actual governance/control frame sizes before using those frames as physical replay evidence.

---

# Immediate implementation order

Completed in this software round:

1. **RF evidence catalog + deterministic trace replay.**
2. **Roadmap/status synchronization.**
3. **Resumable EXACT session state above unchanged PNF1 retry.**
4. **RF-replay-driven PNF1/session tests with explicit evidence semantics.**
5. **Non-overlapping exact-session TRC wire accounting.**
6. **Durable content-addressed store + atomic restartable session checkpoint.**
7. **Deterministic intermittent store-and-forward routing + end-to-end DISCOVERY-to-reconstruction TRC.**
8. **PNB1 TTL/hop governance + PNC1 custody + persistent explicit contact-id duplicate suppression.**

Next software work while hardware is unavailable:

9. **Per-bearer TRC schema and bearer-neutral routing inputs.**
10. **Relay quotas/retention/garbage collection + synthetic multi-relay policy experiments.**
11. **Delta/patch experiments against prior versions.**

When hardware access returns and measured radio behavior is needed:

12. **HW-006 controlled same-room/distance/NLOS checkpoint campaign.**
13. **Measure the actual control/data frame sizes used by governed store-and-forward.**
14. **Calibrate contact capacity/loss and only then enable measured LoRa-aware routing decisions.**
15. **Only then choose whether PHY/radio changes or the next compression pilot are justified.**
