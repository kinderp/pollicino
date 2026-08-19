# PollicinoNet transport modes

PollicinoNet is transport-independent. `DISCOVERY`, `EXACT` and `SEMANTIC`
describe the **information contract**; LoRa, BLE, Wi-Fi, Internet and a future
LoRaWAN adapter describe **how bytes are moved**.

The core must never require one specific radio technology.

## LoRa is not LoRaWAN

The current HW-001/HW-002 adapter uses **bare LoRa peer-to-peer**. Two SX1276
radios exchange packets directly. There is no LoRaWAN gateway, Network Server,
Join Server or Application Server in the path.

LoRaWAN is a higher-layer networking protocol normally organized around
end-devices communicating by LoRa/FSK with gateways, while gateways forward
to a Network Server over IP. That infrastructure is useful for many sensor and
telemetry deployments, but it is a different topology from the direct peer
experiments PollicinoNet is currently studying.

A future LoRaWAN transport adapter is allowed; LoRaWAN must not leak into
`pollicino.net` core wire formats or become a prerequisite for PollicinoNet.

## Mode matrix

| Mode | Scarce/control plane | Rich/data plane | Internet required | Main use |
|---|---|---|---:|---|
| `LORA_ONLY` | bare LoRa | bare LoRa | no | fully disconnected discovery, small exact data, emergency/store-and-forward experiments |
| `LORA_BLE` | LoRa | BLE when peers become nearby | no | long-range discovery followed by local control/session exchange |
| `LORA_WIFI` | LoRa | Wi-Fi Direct/LAN or Internet | optional | preferred discovery→handover path for manifests, files and missing chunks |
| `AUTO` | any permitted scarce link | best permitted available link | optional | capability/policy-driven adaptive delivery |
| `LORAWAN_GATEWAY` *(future adapter)* | LoRaWAN uplink/downlink | gateway/IP backend | normally yes for backend path | interoperability with deployed LPWAN gateway/network-server infrastructure |

## `LORA_ONLY`

```text
peer A <================ bare LoRa ================> peer B
        discovery + manifests + missing exact bytes
```

Use when no richer path exists. This is the hardest case and therefore an
important PollicinoNet research baseline. Bulk transfer is intentionally a
last resort because airtime is scarce.

Useful features:

- PND1 discovery;
- exact PNF1 fallback;
- compact inventory reconciliation;
- resumable chunks;
- store-and-forward;
- TTL/hop/duplicate suppression;
- selective ACK/FEC experiments;
- strict airtime accounting.

## `LORA_BLE`

```text
far away:      A ---- LoRa discovery ----> B
nearby later:  A <======= BLE ==========> B
```

BLE is not automatically a bulk-data replacement for Wi-Fi. It is useful for
nearby rendezvous, configuration, control, authentication/key agreement and
small local exchanges. A node can discover another node at long range, then
switch to BLE when physical proximity makes it available.

## `LORA_WIFI`

```text
LoRa:    compact coordinate / rendezvous / capability hint
                         |
                         v
Wi-Fi/Internet: manifest, file, chunks, model/dictionary, rich session
```

This is the preferred PollicinoNet pattern whenever a rich link exists:
**do not spend LoRa airtime moving bytes that can be retrieved more cheaply
elsewhere**.

Wi-Fi may mean:

- same LAN;
- peer-to-peer/direct local link;
- access point + Internet;
- local server/NAS;
- a later Pollicino P2P overlay.

## `AUTO`

`AUTO` is a policy decision, not a new PHY.

Conceptually:

```text
requirements + authorization + peer capabilities + current links
                              |
                              v
                    path-selection policy
                              |
        +---------------------+--------------------+
        |                     |                    |
        v                     v                    v
    LoRa only             LoRa + BLE          LoRa + Wi-Fi
        |                     |                    |
        +---------------------+--------------------+
                              |
                              v
                         exact result
```

Selection inputs should include:

- exact vs semantic contract;
- authorization/consent;
- object size and priority;
- cache/shared-state availability;
- link availability and measured quality;
- airtime/budget cost;
- latency target;
- energy constraints;
- privacy/metadata policy.

## Future `LORAWAN_GATEWAY`

LoRaWAN is valuable when the objective changes from **peer-to-peer** to
**end-device ↔ infrastructure**.

Possible PollicinoNet use cases:

- sensor/telemetry ingress through existing gateways;
- compact discovery coordinates delivered to an Internet backend;
- remote status or manifest hints;
- integration with an existing public/private LoRaWAN deployment.

It is not the preferred transport for our direct P2P research because the
canonical architecture inserts gateways and a Network Server between the
end-device and backend application.

## Architectural invariant

Allowed:

```text
PollicinoNet core
      |
      v
Transport port
      |
      +-- bare LoRa adapter
      +-- BLE adapter
      +-- Wi-Fi/IP adapter
      +-- future LoRaWAN adapter
```

Forbidden:

```text
PollicinoNet core -> RadioLib
PollicinoNet core -> LoRaWAN SDK
PollicinoNet core -> BLE SDK
PollicinoNet core -> Wi-Fi SDK
```

The hardware/network adapters can evolve independently while PND1/PNF1,
resolver, store and reconstruction contracts remain reusable.
