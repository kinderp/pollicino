# POLLICINO

**Learned lossless compression, generative file identification, and information-minimized networking.**

> *Lasciare meno briciole possibili, ma abbastanza da ritrovare esattamente la strada.*

POLLICINO is a research-and-teaching project around one question:

> **How few bits must be transmitted to reconstruct information exactly when encoder and decoder share useful prior knowledge?**

The repository contains teaching, compression-research and PollicinoNet networking tracks. PollicinoNet now includes deterministic discovery/exact transfer, RF evidence replay, durable resumable sessions, intermittent store-and-forward, TTL/hop governance, custody receipts, explicit-contact duplicate suppression and non-overlapping end-to-end TRC accounting.

## Physical hardware gate

HW-001 through HW-005 have physical validation at their documented scope. HW-006 is software/build ready and remains physically pending for distance/NLOS characterization. The frozen starting point is still 42-byte frames at 2 dBm with the H2/PHY contract unchanged.

Further protocol work does **not** require the boards yet. Physical HW-006 measurements become necessary before PollicinoNet uses measured LoRa behavior for real contact availability/duration, bytes-per-contact capacity, distance/NLOS loss/retry calibration, radio-derived TTL/contact budgets, measured bearer selection, actual PNB1/PNC1/control-frame replay, or any PHY change.

See `ROADMAP.md` and `docs/research/bundle-governance.md` for the detailed status and hardware evidence gate.
