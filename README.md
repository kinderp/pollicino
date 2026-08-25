# POLLICINO

**Learned lossless compression, generative file identification, and information-minimized networking.**

> *Lasciare meno briciole possibili, ma abbastanza da ritrovare esattamente la strada.*

POLLICINO is a research-and-teaching project around one question:

> **How few bits must be transmitted to reconstruct information exactly when encoder and decoder share useful prior knowledge?**

See `ROADMAP.md` for the full status. PollicinoNet currently includes deterministic discovery/exact transfer, RF evidence replay, durable resumable sessions, intermittent store-and-forward, PNB1 TTL/hop governance, PNC1 custody, persistent explicit-contact duplicate suppression, and end-to-end TRC accounting.

## Hardware evidence gate

Further protocol work does not require the boards yet. HW-006 physical tests become necessary before using measured LoRa behavior for distance/NLOS contact availability, real contact-window capacity, measured loss/retry, radio-derived TTL/contact budgets, measured bearer selection, calibration of the actual governance/control frame sizes, or any PHY change.

The physical campaign remains frozen at 42-byte frames / 2 dBm and should proceed same-room -> separation -> wall -> multi-wall/floor -> outdoor before governed-control frame calibration.
