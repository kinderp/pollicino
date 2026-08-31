# POLLICINO

**Learned lossless compression, generative file identification, and information-minimized networking.**

> *Lasciare meno briciole possibili, ma abbastanza da ritrovare esattamente la strada.*

POLLICINO is a research-and-teaching project around one question:

> **How few bits must be transmitted to reconstruct information exactly when encoder and decoder share useful prior knowledge?**

See `ROADMAP.md` for the full status. PollicinoNet currently includes deterministic discovery/exact transfer, RF evidence replay, durable resumable sessions, intermittent store-and-forward, PNB1 TTL/hop governance, PNC1 custody, persistent explicit-contact duplicate suppression, and end-to-end TRC accounting.

## PollicinoNet as a shared substrate

PollicinoNet is being tested as an **application-independent distributed information substrate**, not as a DNA-specific or LoRa-specific application layer.

Current independent consumers/conformance cases include:

- **DNA / Travel DNA** — intent, consent, subscriptions, privacy-sensitive micro-information and carried-node workflows;
- **FARO** — signed scientific knowledge packages whose package identity, publisher authenticity, evidence grade, trust, applicability and local-validation state remain application-owned while Pollicino provides exact content/store/provider primitives;
- **Raiatea and other future integrations** — candidates that may reuse the same generic transport/content primitives through application-owned adapters.

The boundary is intentional:

```text
application semantics
        |
        v
application-owned adapter
        |
        v
PollicinoNet
exact content / references / store / resolver / reconciliation / DTN / bearers
```

Pollicino core must not acquire application-specific branches merely to support FARO, DNA or another consumer. New reusable abstractions remain governed by the Use-Case Justification Gate and the Independent Consumer Generality Gate.

See:

- `docs/research/substrate-generality-gate.md`;
- `docs/research/uc-faro-001-distributed-scientific-knowledge-package-exchange.md`;
- `docs/research/pollicinonet-use-case-index.md`.

FARO cross-project gate RG2-PX0 classified the current direction as `POLLICINO_SUBSTRATE_REUSE_READY_WITH_BOUNDARIES` with HIGH confidence. This is evidence for the boundary, not a declaration that the research-only PR #52 persistence/DTN/custody/bearer surfaces are stable external APIs.

## Hardware evidence gate

Further protocol work does not require the boards yet. HW-006 physical tests become necessary before using measured LoRa behavior for distance/NLOS contact availability, real contact-window capacity, measured loss/retry, radio-derived TTL/contact budgets, measured bearer selection, calibration of the actual governance/control frame sizes, or any PHY change.

The physical campaign remains frozen at 42-byte frames / 2 dBm and should proceed same-room -> separation -> wall -> multi-wall/floor -> outdoor before governed-control frame calibration.
