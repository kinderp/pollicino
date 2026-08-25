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

PollicinoNet generalizes the same principle to delivery:

```text
scarce-link bits <----> shared state / cache / resolver / reconstruction compute
```

The network rule is:

> **Do not transmit the content when transmitting enough information to locate, derive or reconstruct it costs fewer bits.**

## PollicinoNet software status

Implemented:

- PN-001 compact PND1 discovery;
- PN-002 deterministic scarce-link/PFN1 exact transfer, RF replay and resumable sessions;
- PN-003 rendezvous resolver/full-hash retrieval;
- PN-004 authorization-gated adaptive exact delivery;
- PN-005 durable content-addressed store, restartable exact sessions, intermittent store-and-forward, TTL/hop governance, PNC1 custody receipts and explicit-contact duplicate suppression;
- PN-006 optional reversible DNA trace integration.

## Physical LoRa status

HW-001 through HW-005 have physical validation at their documented scope. HW-006 is software/build ready; controlled distance/NLOS checkpoints remain physically pending. The frozen starting point remains 42-byte frames at 2 dBm with the existing H2/PHY contract unchanged.

## Bundle governance

Store-and-forward has a deterministic governance layer:

- PNB1 binds bundle identity to PND1 discovery and PCM1 manifest;
- PND1 TTL and hop limits are enforced before forwarding;
- origin custody starts at hop 0;
- PNC1 receipts record peer, acquisition time, hop count, verified chunk count and partial/complete custody;
- custody ledger/contact IDs can persist atomically across restart;
- replaying the same explicit contact ID is zero-wire;
- new encounters still use PNA1 to avoid retransmitting verified chunks;
- governed end-to-end TRC includes discovery, rendezvous, PNB1, PNC1, PCM1, PNA1, payload, ACKs and retries without overlap.

See `docs/research/bundle-governance.md`, `docs/research/store-and-forward.md`, and `ROADMAP.md`.

## When physical tests are required

Software work can continue without the boards for bearer abstractions, per-bearer accounting, relay quotas/retention, deterministic multi-relay schedules, synthetic policy comparisons, garbage collection and delta/patch experiments.

HW-006 physical tests become necessary before using measured LoRa behavior for claims or routing decisions: real contact availability/window duration, realistic bytes per encounter, distance/NLOS loss/retry behavior, radio-derived TTL/contact budgets, measured bearer selection, physical replay of actual governance/control frame sizes, or any PHY change.

When that gate is reached, resume the frozen HW-006 sequence: same-room -> wall -> multi-wall/floor -> outdoor. After finding the transition region, measure actual governed control/data frame sizes before calibrating LoRa-aware routing.
