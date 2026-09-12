# Per-bearer evidence and TRC

PollicinoNet treats the transport used by each contact as an explicit **bearer**.
The first supported bearer classes are:

- `lora`
- `ble`
- `wifi`
- `internet`

The core does **not** contain invented default performance numbers for any of
these technologies. Every experiment supplies a named `BearerProfile`.

## Three different ideas that must not be confused

### 1. Synthetic profile

A synthetic profile contains numbers chosen for a scenario or simulation.

Example: "pretend this LoRa contact has this bitrate and this loss".

It is useful for testing algorithms, but it is not evidence about real radio
performance.

### 2. Measured profile

A measured profile contains parameters derived from a named measurement or
physical evidence file. PollicinoNet requires explicit provenance before a
profile may be labelled `measured`.

Using those parameters inside the deterministic simulator still produces a
**model run**, not a new physical measurement.

### 3. Physical replay

A physical replay consumes an ordered physical trace through the RF replay
adapter. Its accounting retains the existing `physical_replay_lower_bound`
semantics for unobservable remote responses.

Only this third case is a replay of physical evidence.

## Per-bearer TRC

A governed route can choose a bearer separately for every contact, for example:

```text
origin --LoRa--> relay A --BLE--> relay B --Wi-Fi--> gateway --Internet--> destination
```

The per-bearer report keeps separate totals for every named bearer profile:

- primary data bytes;
- primary ACK bytes;
- retransmission data bytes;
- retransmission ACK bytes;
- unknown remote failures where physical replay cannot observe the return path;
- number of contacts;
- profile evidence basis (`synthetic` or `measured`);
- provenance for measured profiles;
- whether execution was a model run or physical replay.

A route may mix synthetic and measured profiles, but the report exposes that
fact explicitly. Measured parameters never automatically upgrade a simulated
route to physical evidence.

## Hardware gate

No physical board is required to implement or validate the bearer abstraction,
TRC separation, relay quotas, retention, garbage collection, deterministic
multi-relay scheduling or synthetic routing policies.

HW-006 becomes necessary before decisions or claims depend on **real LoRa
behaviour**, including:

- contact availability and contact-window duration at distance/NLOS;
- realistic transferable bytes/chunks per encounter;
- loss/retry behaviour in the transition region;
- radio-derived TTL/contact budgets;
- measured automatic bearer selection;
- physical replay for the actual PNB1/PNC1/PCM1/PNA1/data frame sizes;
- any change to the frozen PHY.

The first campaign remains the frozen 42-byte / 2 dBm HW-006 progression. Only
after locating a transition region should the governed control/data frame sizes
be physically measured and used to calibrate LoRa-aware routing.
