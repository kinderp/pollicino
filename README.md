# POLLICINO

**Learned lossless compression, generative file identification, and information-minimized networking.**

> *Lasciare meno briciole possibili, ma abbastanza da ritrovare esattamente la strada.*

POLLICINO is a research-and-teaching project around one question:

> **How few bits must be transmitted to reconstruct information exactly when encoder and decoder share useful prior knowledge?**

The repository now has three connected tracks:

- **`course/` — teaching track:** from bits and entropy to a tiny Transformer and a bit-perfect codec;
- **`research/` — compression track:** reproducible byte-level experiments, PyTorch/MLX parity, entropy coding and model-assisted identification;
- **PollicinoNet — network track:** discovery, exact reconstruction, cache/P2P reuse and scarce-link delivery, with LoRa as the first physical target.

## Central idea

A predictive model assigns a probability to the next byte:

```text
P(x_i | x_1, ..., x_{i-1})
```

The ideal information cost is:

```text
I(x_i) = -log2 P(x_i | x_<i)
```

For a sequence:

```text
L(x) = - sum_i log2 P(x_i | x_<i)
```

The compression path is therefore:

```text
file
  -> byte model
  -> next-byte probabilities
  -> deterministic entropy coder
  -> compact .pol stream
  -> exact reconstruction
```

The exploratory identification path studies a different trade-off:

```text
shared learned model
        |
        v
ranked candidate space
        |
        +---- short fingerprint / residual "crumbs"
        |
        v
exact candidate search
        |
        v
full cryptographic verification
```

PollicinoNet generalizes the same principle to delivery:

```text
scarce-link bits <----> shared state / cache / resolver / reconstruction compute
```

The network rule is:

> **Do not transmit the content when transmitting enough information to locate, derive or reconstruct it costs fewer bits.**

## Scientific invariants

1. **Lossless means byte-for-byte exact.**
2. **SHA-256 verifies; it does not reconstruct.**
3. **Model/checkpoint cost is reported separately from payload cost.**
4. **Random data remain a negative control.**
5. **PyTorch and MLX use equivalent model specifications wherever practical.**
6. **Experiments record reproducibility metadata.**
7. **Classical compressors remain first-class baselines.**
8. **Discovery is not proof of identity.**
9. **SEMANTIC output is explicitly separate from EXACT authoritative state.**
10. **Physical RF evidence is never silently extrapolated into a deployment reliability claim.**

## Repository layout

```text
pollicino/
├── course/                  # fourth-year teaching path and student labs
├── docs/
│   ├── theory/              # information, coding, ML and wireless theory
│   ├── labs/                # reproducible practical guides
│   └── research/            # scientific protocol and PollicinoNet notes
├── hardware/                # LILYGO/SX1276 firmware, runners and physical evidence
├── configs/                 # backend-independent model specifications
├── src/pollicino/
│   ├── common/              # shared metrics and contracts
│   ├── baselines/           # classical/statistical reference models
│   ├── backends/
│   │   ├── pytorch/
│   │   └── mlx/
│   ├── compression/         # deterministic coding and routing experiments
│   └── net/                 # discovery, exact delivery, P2P store and RF evidence
├── experiments/             # immutable experiment records
├── benchmarks/              # benchmark manifests and comparison outputs
└── tests/                   # theory, parity, round-trip and network invariants
```

## Compression research status

The executable scientific line has reached **PILOT-013 — cheap admission routing**.

PILOT-013 preserved honest neural-forward accounting and met its hard compute cap, but its preregistered retained-gain target was negative. That result is retained as evidence rather than rewritten into a success. There is currently no merged **PILOT-014** result.

The longer-term compression roadmap still includes:

```text
statistical baselines
    -> neural foundations
    -> byte Transformer
    -> PyTorch / MLX parity
    -> deterministic neural codec
    -> scientific benchmark
    -> hybrid routing
    -> generative identification
    -> bandwidth / compute frontier
```

## PollicinoNet software status

The standalone network path has implemented:

- **PN-001:** compact deterministic PND1 discovery descriptor;
- **PN-002:** deterministic scarce-link simulator, PNF1 exact-transfer framing/retry, physical RF replay and resumable exact-session state;
- **PN-003:** opaque rendezvous coordinate -> manifest resolver -> full-hash retrieval;
- **PN-004:** authorization-gated adaptive exact delivery across rich/scarce paths;
- **PN-005:** content-addressed chunk reconstruction, availability summaries, durable on-disk stores and restartable session checkpoints;
- **PN-006:** optional reversible DNA `DNATrace` adapter.

The core remains transport-independent: LoRa-specific firmware and serial tooling live under `hardware/`.

## Physical LoRa status

Target hardware: two **LILYGO / TTGO LoRa32 V1.6.1** boards with ESP32-PICO-D4 and SX1276 at 868 MHz.

| Lab | Purpose | Status |
|---|---|---|
| HW-001 | byte-exact PND1/PNF1 transport in both directions | **physical PASS** |
| HW-002 | RSSI/SNR, RTT, airtime and paced measurements | **physical PASS** |
| HW-002T | timing/polling characterization | **physical PASS** |
| HW-003 | event-driven FreeRTOS responder | **physical PASS** |
| HW-004 | counterbalanced CRC/direction/frame-size matrix | **48/48 physical PASS, 0 CRC events** |
| HW-005 | controlled 10 -> 2 dBm TX-power staircase | **20/20 physical PASS** |
| HW-006 | untethered responder for distance/NLOS checkpoints | **software/build ready; physical checkpoint pending** |

HW-006 deliberately freezes the H2 PING/PONG wire format and the established PHY while moving the remote node off USB power/serial observation. A timeout in untethered mode is classified as **ambiguous**: it cannot alone distinguish a lost PING, remote decode/CRC failure, lost PONG, remote reset/power loss, or another RF failure.

## RF evidence catalog and replay

Physical measurements can now be consumed as data instead of requiring the boards to be attached during software development.

```bash
python -m pollicino.net.rf \
  hardware/lilygo-lora32-v1.6.1/physical-validation
```

After package installation:

```bash
pollicino-rf hardware/lilygo-lora32-v1.6.1/physical-validation
```

The RF tool:

- normalizes supported HW-001..HW-006 evidence records;
- extracts ordered replay traces from raw HW-002 runs and future executed HW-006 checkpoints;
- preserves RSSI/SNR/RTT/ToA observations without imputing missing telemetry;
- refuses by default to replay more physical samples than were actually recorded;
- does **not** sum all historical files into a fake packet-loss estimate, because raw runs and derived summaries can overlap.

See [`docs/research/rf-evidence-replay.md`](docs/research/rf-evidence-replay.md).

## Durable exact-session restart

Exact transfers can now survive a process restart without retransmitting already verified chunks.

```text
receive verified chunks
  -> DirectoryPollicinoStore on disk
  -> atomic checksummed session checkpoint
  X  process stops
  -> reopen stores + load checkpoint
  -> recompute actual receiver availability
  -> transmit only still-missing chunks
  -> final SHA-256-verified reconstruction
```

The durable store re-hashes a chunk before advertising it as available. Corrupt ordinary files are therefore not trusted and may be repaired by a later verified transfer. Session checkpoints are written through same-directory temporary files, `fsync` and atomic `os.replace`, and include a SHA-256 checksum over canonical state JSON.

The complete test suite includes a fresh-process-style restart test and a failure-before-replace test that preserves the previous committed checkpoint.

See [`docs/research/durable-exact-session.md`](docs/research/durable-exact-session.md).

## Where to start

- Students: [`course/README.md`](course/README.md)
- Theory map: [`docs/theory/map.md`](docs/theory/map.md)
- Wireless / LoRa / Wi-Fi / Bluetooth: [`docs/theory/wireless-lora-wifi-bluetooth-it.md`](docs/theory/wireless-lora-wifi-bluetooth-it.md)
- HW-001 practical guide (Italian): [`docs/labs/hw-001-lilygo-guida-pratica-it.md`](docs/labs/hw-001-lilygo-guida-pratica-it.md)
- Research questions: [`docs/research/questions.md`](docs/research/questions.md)
- Experimental protocol: [`docs/research/protocol.md`](docs/research/protocol.md)
- PollicinoNet architecture: [`docs/research/pollicinonet.md`](docs/research/pollicinonet.md)
- RF evidence/replay: [`docs/research/rf-evidence-replay.md`](docs/research/rf-evidence-replay.md)
- Durable exact sessions: [`docs/research/durable-exact-session.md`](docs/research/durable-exact-session.md)
- TRC accounting: [`docs/research/trc-accounting.md`](docs/research/trc-accounting.md)
- FreakWAN audit: [`docs/research/freakwan-audit.md`](docs/research/freakwan-audit.md)
- Full roadmap: [`ROADMAP.md`](ROADMAP.md)

## Immediate next steps

Completed while HW-006 physical tests are temporarily unavailable:

1. RF evidence catalog and deterministic physical replay;
2. resumable EXACT sessions above unchanged PNF1 retry;
3. RF-replay-driven retry/session testing;
4. non-overlapping TRC wire accounting;
5. durable content-addressed chunk store and atomic restartable session checkpoints.

Next software work:

1. extend TRC across discovery/rendezvous without double counting;
2. add replay-driven **store-and-forward** scenarios across intermittent peers;
3. define durable-store retention/garbage collection;
4. experiment with delta/patch transfer against prior versions.

When hardware access returns, resume the frozen HW-006 sequence: same-room -> wall -> multi-wall/floor -> outdoor, then calibrate the synthetic scarce-link model before changing PHY parameters.
