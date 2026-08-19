# POLLICINO

**Learned lossless compression and generative file identification.**

> *Lasciare meno briciole possibili, ma abbastanza da ritrovare esattamente la strada.*

POLLICINO is a research-and-teaching project about a deceptively simple question:

> **How few bits must be transmitted to reconstruct a file exactly when encoder and decoder share a learned model of the file distribution?**

The name comes from *Pollicino* (Tom Thumb): a very small trail can be sufficient to retrace a path. In this project, the “crumbs” are the bits that remain after a model has already captured as much predictable structure as possible.

POLLICINO deliberately has two synchronized tracks:

- **`course/` — school track.** A fourth-year secondary-school course that starts from bits and files and ends with a tiny Transformer and a bit-perfect neural codec.
- **`research/` — scientific track.** Reproducible byte-level experiments with equivalent PyTorch and MLX backends, entropy coding, exact reconstruction and model-assisted identification.

A parallel network research branch, **PollicinoNet**, studies the same information-minimization principle over ultra-low-bandwidth and intermittent links: discovery by compact coordinates, exact P2P reconstruction, opportunistic rich-link handover and a separate semantic realtime mode. LoRa is the first scarce-link target; DNA/Travel DNA is the first concrete application integration. See [`docs/research/pollicinonet.md`](docs/research/pollicinonet.md).

## The central idea

A predictive model does not need to memorize every possible file. It learns a probability distribution over the next byte:

```text
P(x_i | x_1, ..., x_{i-1})
```

If the correct next byte has high probability, it carries little new information. Its ideal coding cost is:

```text
I(x_i) = -log2 P(x_i | x_<i)
```

For a sequence of `N` bytes, the predictive ideal is:

```text
L(x) = - sum_i log2 P(x_i | x_<i)
```

This connects the whole project:

```text
bits -> probability -> entropy -> prediction -> learning -> Transformer
                                                   |
                                                   v
file -> byte model -> next-byte probabilities -> entropy coder -> .pol stream
                                                               |
                                                               v
                                                    exact original file
```

A second, exploratory branch studies the original POLLICINO intuition:

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
full cryptographic hash verification
```

The scientific object is therefore not only compression ratio. We also study the trade-off:

```text
transmitted bits  <---->  reconstruction compute
```

PollicinoNet broadens that trade-off to network delivery:

```text
scarce-link bits <----> shared state / cache / resolver / reconstruction compute
```

## Scientific invariants

POLLICINO experiments must obey these rules:

1. **Lossless means bit-perfect.** The reconstructed output must be byte-for-byte identical to the original.
2. **SHA-256 verifies, it does not reconstruct.** A cryptographic hash is an integrity check, never hidden side information.
3. **Model cost is reported.** Payload, checkpoint size and amortized model cost are separate metrics.
4. **Random data are a negative control.** A uniform 256-symbol source has an ideal cost of exactly 8 bits/byte.
5. **PyTorch and MLX follow the same model specification** wherever practical.
6. **Every experiment is reproducible.** Seed, dataset hash, commit, hardware, framework, precision and configuration are recorded.
7. **Classical compressors remain first-class baselines.** A neural system does not “win” merely because its model size is ignored.
8. **Discovery is not proof.** A compact PollicinoNet coordinate may locate a manifest, but exact content identity is verified with a full cryptographic identifier.
9. **Semantic is not lossless.** Perceptual/realtime reconstruction is an explicit separate contract and cannot represent authoritative exact state.

## Repository layout

```text
pollicino/
├── course/                  # fourth-year teaching path and student labs
├── docs/
│   ├── theory/              # information, coding, ML and wireless theory
│   ├── labs/                # reproducible hands-on laboratory guides
│   └── research/            # protocol, PollicinoNet and scientific notes
├── hardware/                # optional physical adapters and validated HW labs
├── configs/                 # backend-independent model specifications
├── src/pollicino/
│   ├── common/              # metrics, data and shared contracts
│   ├── baselines/           # uniform/statistical reference models
│   ├── backends/
│   │   ├── pytorch/         # reference research backend / future CUDA scaling
│   │   └── mlx/             # Apple-Silicon backend
│   └── compression/         # deterministic arithmetic/range coding
├── experiments/             # immutable experiment records
├── benchmarks/              # benchmark manifests and comparison outputs
└── tests/                   # theory, parity and round-trip invariants
```

## Milestone 0 — The eight-bit floor

Before neural networks, establish the scientific zero point.

For a model that assigns every byte equal probability:

```text
P(byte) = 1 / 256
```

therefore:

```text
-log2(1 / 256) = 8 bits/byte
```

The repository includes an executable baseline:

```bash
python -m pollicino.baselines.uniform path/to/file
```

It reports input bytes, theoretical bits-per-byte and verifies an exact reversible round trip with SHA-256.

This baseline is intentionally boring. That is its value: every later model must improve predictive code length without breaking exact reconstruction.

## Milestone 1 — Learn a file statistically

Implement and compare:

```text
uniform -> empirical byte frequencies -> bigram -> n-gram / Markov
```

Questions:

- How much does context reduce cross-entropy?
- On which file classes does it help?
- When does a more complex model overfit?
- How closely does theoretical log loss predict realized coded size?

## Milestone 2 — Build a neural predictor from first principles

```text
neuron -> MLP -> embeddings -> attention -> causal Transformer
```

No high-level pretrained-model library is required. The objective is to understand the components that make an LLM train.

## Milestone 3 — PyTorch / MLX parity

Train the same byte Transformer in both frameworks from a framework-independent YAML specification and compare:

- parameter count,
- learning curves,
- bits/byte,
- training throughput,
- peak memory,
- decode throughput,
- reproducibility.

## Milestone 4 — First real POLLICINO codec

Connect next-byte probabilities to a deterministic arithmetic/range coder:

```text
original -> model -> probability table -> coder -> compressed payload
compressed payload -> coder + same model -> original
```

Success criterion:

```text
SHA256(original) == SHA256(decoded)
```

## Milestone 5 — Generative identification

Only after the entropy-coding baseline works, explore whether a learned model can narrow a candidate space enough that a short fingerprint and additional decoder compute can identify an exact chunk or file.

The main research curve becomes:

```text
fingerprint bits -> candidates searched -> decode compute -> success probability
```

No result counts as lossless unless exact reconstruction is independently verified.

## Where to start

- Students: [`course/README.md`](course/README.md)
- Theory map: [`docs/theory/map.md`](docs/theory/map.md)
- Wireless / LoRa / Wi-Fi / Bluetooth: [`docs/theory/wireless-lora-wifi-bluetooth-it.md`](docs/theory/wireless-lora-wifi-bluetooth-it.md)
- HW-001 practical guide (Italian): [`docs/labs/hw-001-lilygo-guida-pratica-it.md`](docs/labs/hw-001-lilygo-guida-pratica-it.md)
- Research questions: [`docs/research/questions.md`](docs/research/questions.md)
- Experimental protocol: [`docs/research/protocol.md`](docs/research/protocol.md)
- PollicinoNet: [`docs/research/pollicinonet.md`](docs/research/pollicinonet.md)
- FreakWAN audit: [`docs/research/freakwan-audit.md`](docs/research/freakwan-audit.md)
- Full roadmap: [`ROADMAP.md`](ROADMAP.md)

## Status

The executable research line includes deterministic lossless routing experiments through PILOT-013. PollicinoNet now has implemented standalone discovery/exact/P2P layers, an optional DNA integration, and a physically validated HW-001 bidirectional LoRa bridge on two LILYGO T3 V1.6.1 / SX1276 boards. HW-002 is the next hardware research step: characterize packet loss, RSSI/SNR, latency/airtime and physical TRC under controlled conditions.
