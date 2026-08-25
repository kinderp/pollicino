# POLLICINO

**Learned lossless compression, generative file identification, and information-minimized networking.**

> *Lasciare meno briciole possibili, ma abbastanza da ritrovare esattamente la strada.*

POLLICINO is a research-and-teaching project around one question:

> **How few bits must be transmitted to reconstruct information exactly when encoder and decoder share useful prior knowledge?**

The repository has three connected tracks: the fourth-year teaching path, reproducible compression research with PyTorch/MLX parity, and PollicinoNet for information-minimized networking.

## Scientific invariants

- Lossless means byte-for-byte exact.
- SHA-256 verifies; it does not reconstruct.
- Model/checkpoint cost is separated from payload cost.
- Discovery is not proof of identity.
- SEMANTIC output is separate from authoritative EXACT state.
- Physical RF evidence is never silently extrapolated into deployment reliability claims.

## PollicinoNet status

Implemented software layers include:

- **PN-001:** compact deterministic PND1 discovery;
- **PN-002:** deterministic scarce-link simulator, PNF1 exact framing/retry, RF replay and resumable sessions;
- **PN-003:** rendezvous resolver and full-hash retrieval;
- **PN-004:** authorization-gated adaptive exact delivery;
- **PN-005:** content-addressed chunks, durable stores, restartable sessions, intermittent store-and-forward, PNB1 TTL/hop governance, PNC1 custody receipts, persistent contact-id duplicate suppression and governed end-to-end TRC;
- **PN-006:** optional reversible DNA trace adapter.

## Physical LoRa status

Target hardware is two LILYGO/TTGO LoRa32 V1.6.1 / SX1276 boards. HW-001 through HW-005 have physical validation at their documented scope. HW-006 is software/build ready; controlled distance/NLOS evidence is still pending.

The HW-006 baseline remains frozen at **42-byte frames / 2 dBm** with the established H2/PHY contract unchanged.

## Durable exact sessions and store-and-forward

Verified chunks can persist in `DirectoryPollicinoStore`, session/checkpoint state can survive process restart, and later contacts send only still-missing verified chunks. Store-and-forward can reconstruct an exact object through intermittent relays without a permanent origin-to-destination path. Corrupt local chunks are not advertised or forwarded.

The governance layer adds:

- stable PNB1 bundle identity bound to PND1 discovery and PCM1 content identity;
- TTL and hop-limit enforcement before forwarding;
- PNC1 partial/full custody receipts;
- atomically persistent custody/contact ledger;
- zero-wire suppression when the same explicit contact ID is replayed;
- PNA1 content-level deduplication for genuinely new encounters;
- non-overlapping TRC covering discovery, rendezvous, PNB1, PNC1, PCM1, PNA1, payload, ACKs, retries and explicit future FEC.

See:

- `docs/research/rf-evidence-replay.md`
- `docs/research/durable-exact-session.md`
- `docs/research/store-and-forward.md`
- `docs/research/bundle-governance.md`
- `docs/research/trc-accounting.md`
- `ROADMAP.md`

## When physical tests are required

The next software work can continue **without the boards**: bearer abstractions/per-bearer accounting, relay quotas and retention, deterministic multi-relay scheduling, synthetic routing-policy comparisons, garbage collection and delta/patch experiments.

HW-006 physical tests become necessary before PollicinoNet uses **measured LoRa behavior** for claims or decisions, specifically before relying on:

- real contact availability or contact-window duration at distance/NLOS;
- realistic bytes/chunks deliverable per encounter;
- measured loss/retry behavior in the transition region;
- TTL/contact budgets derived from radio observations instead of synthetic inputs;
- automatic bearer/routing choices justified by measured LoRa performance;
- physical replay/calibration of the actual PNB1/PNC1/session-control frame sizes;
- any decision to change the frozen PHY.

When that gate is reached, resume HW-006 in this order:

```text
same-room
 -> greater separation
 -> one wall
 -> multiple walls
 -> another floor
 -> outdoor distance
```

First find the transition region using the frozen 42-byte / 2 dBm baseline. Then measure the actual governed control/data frame sizes before calibrating LoRa-aware routing.

## Immediate next software work

1. per-bearer TRC schema for LoRa/BLE/Wi-Fi/Internet with evidence labels separating synthetic from measured inputs;
2. relay quotas, retention and garbage collection;
3. deterministic synthetic multi-relay policy experiments;
4. delta/patch experiments against prior versions.
