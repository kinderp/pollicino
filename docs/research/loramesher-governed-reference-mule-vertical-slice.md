# LoRaMesher governed reference-mule vertical slice

Status: host/model prototype checkpoint, 2026-08-29

## Use-case gate

This prototype is justified by two already accepted primary use cases:

- `UC-DNA-001`: a carried node participates in a dense connected school mesh, then leaves school and continues as an opportunistic DTN node without losing object/custody state;
- `UC-CONTENT-001`: a small authorized reference or manifest is carried through scarce/off-grid contacts and later resolved in a rich home environment.

The purpose of this checkpoint is not to claim LoRa RF performance. It is to prove the architectural boundary:

```text
Pollicino governed object state
        |
        +-- CONNECTED_MESH / LoRaMesher application-byte port
        |
        +-- mode transition + physical carry + restart
        |
        +-- OPPORTUNISTIC_DTN / different bearer implementation
        |
        +-- RICH_HOME / explicit application resolver
```

The same PNB1 bundle identity, PCM1 content identity and PNC1 custody chain must survive every transition.

## Implemented bridge

`src/pollicino/integrations/loramesher_pnf1.py` adds a narrow host-side bridge.

### PNF1 transmitter

`LoRaMesherPnf1Transmitter`:

1. fragments an ordinary Pollicino payload using the existing PNF1 framing;
2. sends every encoded PNF1 frame through `LoRaMesherApplicationPort.send()`;
3. receives frames through the target port's registered callback;
4. decodes/reassembles the PNF1 transfer byte-exactly;
5. returns a transfer report consumable by the existing TRC classifier.

The bridge does not bypass `PNB1`, `PNC1`, `PCM1`, `PNA1` or the governed store-forward path. Those objects are ordinary Pollicino payloads and therefore traverse the same injected transmitter.

### Evidence accounting

The report label is:

```text
loramesher_host_application_bytes
```

It counts only encoded PNF1 bytes accepted by the host LoRaMesher application port.

It explicitly does **not** claim or count:

- LoRaMesher network/data headers;
- TDMA beacons or control traffic;
- route-update traffic;
- physical retries;
- RF airtime;
- RSSI/SNR;
- electrical energy;
- application delivery acknowledgement.

Because the current narrow LoRaMesher application API only reports that `Send()` accepted the payload, the host bridge requires:

```text
ack_bytes = 0
synthetic data_loss_ppm = 0
synthetic ack_loss_ppm = 0
```

Using a non-zero Pollicino ACK model here would incorrectly turn LoRaMesher queue/API acceptance into evidence of an observed Pollicino acknowledgement.

## Node-runtime plumbing

`PollicinoNodeRuntime.receive_governed_from()` now exposes the already existing optional `TransferCallable` accepted by `governed_forward_contact()`.

Default behavior is unchanged. A validated bearer adapter can provide its own transmitter without duplicating node-local custody, persistence or exact-object semantics.

This keeps the dependency direction:

```text
Pollicino runtime/governance
        |
        v
injected byte transmitter
        |
        v
LoRaMesher application API
```

rather than teaching the Pollicino core LoRaMesher routing semantics.

## Validated governed school hop

`tests/test_loramesher_governed_bearer.py` validates:

- `NodeBearerController` selects the ready LoRaMesher school context;
- `NodeBearerTransport` dispatches through `LoRaMesherGovernedBearerAdapter`;
- every governed transfer primitive crosses the byte-oriented LoRaMesher application port through PNF1;
- the target reconstructs the `PortableReference` exactly;
- PNC1 custody advances to hop 1;
- governance and inner contact accounting are both `loramesher_host_application_bytes`;
- missing address mappings fail closed;
- unobservable ACK accounting and synthetic loss are rejected.

Validation: GitHub Actions `33274807554` — PASS.

## Full school -> territory -> home vertical slice

`tests/test_node_loramesher_reference_mule_vertical_slice.py` validates the concrete daily flow:

```text
student A / school
    |
    | LoRaMesher host application port
    | PNF1 + PNB1/PNC1/PCM1/PNA1
    v
student B / school
    |
    | change to OPPORTUNISTIC_DTN
    | process/runtime restart
    | physical carry represented with zero invented wire bytes
    v
student B / territory
    |
    | different off-grid bearer model
    v
home gateway
    |
    | transition to RICH_HOME
    v
explicit authorized HomeReferenceResolver handler
```

Assertions include:

- school hop exact;
- school custody hop = 1;
- bundle and reference survive mode change/restart unchanged;
- afternoon hop exact;
- home custody hop = 2;
- home resolver receives the exact original authorized reference;
- morning and afternoon evidence labels remain distinct;
- both actual modeled contacts consume non-zero wire bytes;
- physical carry itself invents no transfer traffic.

Validation: GitHub Actions `33274843374` — PASS.

## What this proves

At host/model scope, the architectural idea is now executable:

> a Pollicino object can cross a connected LoRaMesher application-byte bearer at school, remain in a student's persistent Pollicino state while the node moves and restarts, cross a different opportunistic bearer later, and finally be resolved in a rich home environment without changing object or custody identity.

This is stronger than the earlier generic school/off-grid model because the connected-mesh hop now traverses the actual narrow LoRaMesher application-port abstraction rather than calling the deterministic transfer model directly.

## What it does not prove

This does not prove that LoRaMesher is physically superior, that its RF route converges on the LILYGO boards, or that the application bytes counted here equal radio bytes.

The next LoRaMesher implementation gates are separate:

1. native/embedded implementation of `LoRaMesherApplicationPort` on the target board/toolchain;
2. end-to-end governed transfer through that embedded port;
3. explicit LoRaMesher control/data overhead measurement where observable;
4. only after physical calibration, comparison with raw Pollicino and FreakWAN on identical hardware/PHY.

## Next product-facing vertical slice

The host reference-mule path is now sufficient to justify moving upward rather than inventing another transport abstraction:

- add explicit home resolver adapters only for concrete authorized providers/use cases;
- add DNA Topic/Subscription filtering before publishing/forwarding micro-information;
- preserve the same node/bearer runtime and governed object layer for both content-reference and DNA flows.

## Physical evidence boundary

No range, wall/floor penetration, collision, LoRaMesher airtime, energy or real contact-capacity claim is made here.

Those remain behind:

**GATE PROVE FISICHE HW-006**

The first physical campaign remains frozen at 42-byte frames / 2 dBm before any PHY or real-capacity conclusion.