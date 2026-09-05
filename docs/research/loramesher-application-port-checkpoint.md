# LoRaMesher application-port checkpoint

Status: host-side integration checkpoint, 2026-08-29

## Goal

Move from lifecycle-only LoRaMesher integration toward a real Pollicino data plane without pretending that the existing host runtime is already using the radio.

## Upstream API verified

Current upstream `LoRaMesher/LoRaMesher` exposes an application-oriented byte surface suitable for a Pollicino bearer bridge:

- `IsReadyToSend(destination)`;
- `Send(destination, std::vector<uint8_t>)`;
- `SetDataCallback(DataReceivedCallback)` where the callback receives source address plus byte vector;
- network/queue diagnostics separately.

This means LoRaMesher can remain below PollicinoNet and carry Pollicino wire/application bytes opaquely. LoRaMesher does not need to understand PND1, PNF1, PCM1, PNB1, PNC1, DNA or PortableReference semantics.

## Implemented host contract

`src/pollicino/integrations/loramesher_transport.py` adds a narrow research port mirroring only the required application boundary:

```text
local_address
ready_to_send(destination)
send(destination, bytes)
set_receive_callback(source, bytes)
```

The in-memory implementation is deliberately **not** a mesh or radio simulator. It proves only:

- source address is preserved;
- payload bytes are preserved exactly;
- PortableReference bytes remain opaque;
- PND1 bytes remain opaque;
- missing destinations and self-send fail closed;
- API queue acceptance is not treated as Pollicino delivery acknowledgement or RF evidence.

Validation: GitHub Actions `33258271704` — full suite PASS plus targeted application-port tests PASS.

## Important boundary discovered

The existing exact-session injection point is not yet suitable for a real bidirectional bearer bridge.

`sync_missing_chunks_step()` currently accepts one generic `transmitter` callable for all scarce-link exchanges. However the protocol roles differ:

```text
sender -> receiver
  PCM1 manifest
  chunk packets

receiver -> sender
  PNA availability
```

A host simulator can hide this direction because both stores exist in one process. A real LoRaMesher bridge cannot: source/destination addresses and ingress ownership must be explicit.

Therefore wrapping current `receive_governed_from()` or the current single transmitter in `LoRaMesher.Send()` would create a false integration: the Python process would still possess both endpoints' state and only cosmetically pass bytes through a bus.

## Next required refactor

Before a governed LoRaMesher data-plane adapter is valid, split the exact-session transport injection into explicit directional channels while preserving the current default behavior and PNF1 format:

```text
sender_to_receiver_transmitter
receiver_to_sender_transmitter
```

Expected mapping:

- manifest: sender -> receiver;
- availability: receiver -> sender;
- chunks: sender -> receiver;
- PNF1 acknowledgement/accounting remains authoritative at the transaction layer.

Requirements:

1. no H2/PNF1 wire-format change;
2. existing deterministic and RF-replay tests remain byte/accounting compatible;
3. both directions must retain non-overlapping TRC accounting;
4. a LoRaMesher application-port implementation may then bind each direction to `Send(destination, bytes)` / callback ingress;
5. LoRaMesher `Send()` acceptance must not be promoted to Pollicino ACK success;
6. no capacity, loss, range or energy is inferred from LoRaMesher readiness or host delivery.

## Gate decision

**Application-port boundary: PROTOTYPE / PASS.**

**Governed LoRaMesher data plane: PROTOTYPE / NEXT**, blocked only by the directional session-ingress refactor, not by physical hardware.

A real radio-performance claim remains behind **GATE PROVE FISICHE HW-006**.
