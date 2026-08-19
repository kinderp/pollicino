# ADR — Transport backends, node roles and FreakWAN integration

Status: **accepted for research roadmap**  
Date: 2026-08-19

This ADR records two decisions made after HW-001 and before physical HW-002 validation.

## 1. Reference embedded backend

The **reference PollicinoNet radio firmware remains C++/Arduino + RadioLib**.

Reasons:

- HW-001 has already been physically validated bidirectionally on the two LILYGO T3 V1.6.1 / SX1276 boards;
- HW-002 software/build validation is already green on the same stack;
- lower runtime overhead and more predictable timing are useful for RTT/jitter/airtime experiments;
- RadioLib exposes the radio operations and time-on-air accounting needed by the measurement line;
- the reference firmware must remain small, reproducible and independent from application frameworks.

This is a **reference implementation choice**, not a claim that C++ is universally superior.

## 2. MicroPython backend

MicroPython is added to the roadmap as a **second experimental and educational backend**.

Primary uses:

- fast protocol prototyping;
- REPL-driven labs;
- teaching direct SX1276 register access;
- reproducing selected FreakWAN behaviors;
- backend-parity experiments against C++/RadioLib.

A future parity lab should run the same measurement contract on the same hardware:

```text
same H2-like measurement semantics
          |
          +-- C++ / RadioLib
          |
          +-- MicroPython / direct SX1276 driver
          |
          v
same LILYGO / SX1276 hardware
```

Compare at least:

- RTT;
- RTT jitter;
- packet success rate;
- RSSI/SNR equality where hardware conditions are controlled;
- RAM/flash usage;
- host interaction latency;
- CPU/runtime overhead;
- development complexity.

MicroPython must not become a dependency of `pollicino.net` core.

## 3. Three separate axes

PollicinoNet must not collapse information semantics, transport technology and node role into one `mode` field.

### 3.1 Information contract

What result is required?

```text
DISCOVERY
EXACT
SEMANTIC
```

### 3.2 Transport

How can bytes or rendezvous information move?

```text
native_lora
freakwan_mesh
ble
wifi
internet
lorawan
future transports
```

### 3.3 Node role

What is this node doing in the network?

```text
peer
relay
gateway
```

### 3.4 Path policy

Which permitted path should be preferred?

```text
lora_only
offline_only
prefer_rich_link
auto
```

This separation prevents names such as `LoRa+WiFi` from becoming architectural types. A peer can have several transports, a gateway can expose several transports, and the path planner chooses among them according to policy and application constraints.

## 4. Native LoRa remains mandatory

PollicinoNet keeps a native bare-LoRa path under its own control.

Purpose:

- deterministic research baseline;
- direct peer-to-peer operation;
- exact accounting of framing/retry/FEC/ACK decisions;
- operation without external mesh or gateway infrastructure;
- comparison target for other networking stacks.

HW-001 and HW-002 belong to this line.

## 5. FreakWANTransport

FreakWAN is added to the roadmap as an **optional transport adapter / networking substrate**.

Conceptual dependency direction:

```text
PollicinoNet application/service
          |
          v
FreakWANTransport adapter
          |
          v
FreakWAN message / relay network
          |
          v
bare LoRa
```

The adapter may use FreakWAN for functions such as:

- multi-hop relay;
- TTL propagation;
- duplicate suppression;
- randomized retransmission;
- first-hop acknowledgement;
- HELLO/neighbor discovery;
- store-and-forward behavior.

PollicinoNet remains responsible for:

- PND1/coordinates;
- manifests;
- content-addressed identity;
- chunk/cache logic;
- exact reconstruction;
- end-to-end cryptographic verification;
- TRC accounting;
- privacy/application authorization contracts.

A FreakWAN delivery acknowledgement must **never** be interpreted as proof that a Pollicino object was reconstructed and verified.

## 6. FreakWANGateway

A future node may act as a bridge between a FreakWAN LoRa mesh and richer PollicinoNet paths.

```text
FreakWAN nodes / relays
        |
      LoRa
        |
        v
+---------------------------+
| FreakWANGateway           |
|                           |
| FreakWAN adapter          |
| PollicinoNet resolver     |
| PollicinoStore/cache      |
| authorization boundary    |
+---------------------------+
        |
   +----+---------+
   |              |
 Wi-Fi          Internet
   |              |
   +-------> PollicinoNet / providers
```

Example DISCOVERY flow:

```text
remote node
  -> compact PND1 / scoped coordinate
  -> FreakWAN relays
  -> FreakWANGateway
  -> resolver over Wi-Fi/Internet
  -> full manifest
  -> rich-link retrieval
  -> full cryptographic verification
```

The gateway can also cache manifests/chunks so later peers may resolve or retrieve objects with less upstream traffic.

## 7. LoRaWAN remains another optional adapter

LoRaWAN is neither replaced by nor conflated with FreakWAN.

Future transports can coexist:

```text
              PollicinoNet
                   |
       +-----------+-----------+
       |           |           |
 native LoRa   FreakWAN     LoRaWAN
   peer/P2P      mesh        gateway/
                           network server
```

The architecture should allow one object/experiment to be delivered through each path and compare the complete cost.

## 8. Research comparison

A future experiment should send the **same PollicinoNet object/descriptor** through multiple paths:

```text
native bare LoRa
vs
FreakWAN mesh
vs
LoRaWAN
vs
LoRa discovery + Wi-Fi handover
```

Measure:

- useful bytes;
- radio bytes;
- relay bytes;
- ACK/retry bytes;
- airtime per node;
- total network airtime;
- RTT / completion latency;
- packet success / reconstruction success;
- energy proxy;
- final exact verification;
- TRC;
- infrastructure dependency.

This comparison is more useful than declaring one stack globally better.

## 9. Planned sequence

### HW-002 — native LoRa measurement baseline

Finish the already implemented C++/RadioLib measurement line:

- firmware-level ping/pong;
- RTT;
- bidirectional RSSI/SNR;
- time-on-air;
- packet-size matrix;
- packet-loss measurements;
- distance/environment protocol.

### HW-MPY-001 — MicroPython parity lab

Implement the same narrow measurement semantics with MicroPython/direct SX1276 control and compare against the C++ reference.

### HW-FW-001 — FreakWAN interoperability baseline

Run FreakWAN on compatible hardware and establish:

- direct peer connectivity;
- HELLO discovery;
- ping/pong;
- relay behavior;
- observed message overhead;
- duty/airtime accounting.

### HW-FW-002 — FreakWANTransport

Carry an opaque PollicinoNet descriptor through FreakWAN without making FreakWAN parse PollicinoNet semantics.

First success criterion:

```text
PND1 bytes before FreakWAN transport
==
PND1 bytes after FreakWAN transport
```

### HW-GW-001 — FreakWANGateway

Resolve a PollicinoNet coordinate received through a FreakWAN mesh and retrieve the exact object over Wi-Fi/Internet.

Success criterion:

```text
mesh-carried coordinate
  -> gateway resolver
  -> rich retrieval
  -> SHA256(expected) == SHA256(reconstructed)
```

### HW-COMPARE-001 — transport comparison

Compare native LoRa, FreakWAN and richer-link handover under a preregistered experiment protocol using TRC and airtime metrics.

## 10. Architectural invariants

1. `pollicino.net` core does not import FreakWAN, RadioLib, Arduino or MicroPython.
2. C++/RadioLib remains the reference measurement backend until a later experiment justifies changing it.
3. MicroPython is a peer experimental backend, not a replacement forced into the core.
4. FreakWAN is optional: PollicinoNet must continue to operate without it.
5. FreakWAN relay success is hop/network success, not end-to-end object verification.
6. Gateways are roles, not transports.
7. DISCOVERY/EXACT/SEMANTIC are information contracts, not transport modes.
8. Native LoRa, FreakWAN, LoRaWAN, BLE, Wi-Fi and Internet remain replaceable/combposable adapters.
9. TRC must count every radio byte/airtime contribution, including relay/retry overhead.
10. Security/privacy boundaries are defined by PollicinoNet/application contracts, not inherited implicitly from a transport.
