# LoRaMesher native host gate

Status: ACTIVE host-only compatibility gate, 2026-08-28

## Use case

UC-DNA-001 and the school phase of UC-CONTENT require a contemporaneously connected multi-hop LoRa segment without asking PollicinoNet to implement its own distance-vector/TDMA mesh.

LoRaMesher is the current connected-mesh candidate, but it must earn the adapter boundary through reproducible host and later physical evidence.

## Pinned upstream

Repository:
`https://github.com/LoRaMesher/LoRaMesher`

Pinned commit:

```text
1abec4a850389afcfdcae0e41c965b58bbeb701f
```

Commit date: 2026-07-30.

Pinning is mandatory for experiments. Do not build against a moving `main` and cite the result as reproducible evidence.

## Current API contract relevant to Pollicino

At the pinned revision, upstream exposes:

- `Builder()` + configuration objects;
- `Start()`;
- `Stop()`;
- `Send(destination, std::vector<uint8_t>)`;
- `SetDataCallback(source, const std::vector<uint8_t>&)`;
- `GetNetworkStatus()`;
- `IsReadyToSend()`;
- routing table/queue diagnostics.

For Pollicino the important data-plane property is narrow:

> an opaque byte vector can enter LoRaMesher at one node and be returned byte-identical through the data callback at the target, while LoRaMesher owns connected-segment forwarding.

Pollicino does not need LoRaMesher to understand PND1/PNF1/PCM1/PNB1/PNC1.

## Lifecycle ambiguity to preserve

The current upstream documentation and test source do not tell one completely consistent story about restart:

- the README states that `Stop()` releases resources and that there is no resume, recommending rebuilding an instance to restart;
- `test/test_loramesher/test_loramesher_initialization.cpp` contains a `StartAfterStop` test that expects the same instance to start successfully again;
- an upstream 2026 issue reports restart problems.

Therefore the Pollicino design must **not depend on same-instance resume**. A future embedded adapter should be safe when implemented as:

```text
leave CONNECTED_MESH
   -> Stop / destroy LoRaMesher instance
   -> Pollicino persistent state remains alive

re-enter CONNECTED_MESH
   -> build fresh LoRaMesher instance
   -> Start
```

A cheaper same-instance restart may be adopted later only if the pinned/relevant upstream version is explicitly validated.

## Gate 1 — pinned native build/test

Before writing a Pollicino C++ bridge:

1. clone the exact upstream commit;
2. install PlatformIO in CI;
3. run the upstream `test_native` lifecycle/`LoraMesher` tests;
4. record the exact pass/fail result;
5. keep this result separate from Pollicino unit tests.

This proves only host compatibility of upstream at the pinned revision.

## Gate 2 — opaque payload bridge

Only after Gate 1 passes, add a minimal host-native experiment that demonstrates:

```text
Pollicino opaque bytes
        |
        v
LoRaMesher Send(... vector<uint8_t>)
        |
        v
host simulated connected segment
        |
        v
SetDataCallback(... vector<uint8_t>)
        |
        v
byte-identical payload
```

Metrics for this gate:

- input/output byte identity;
- LoRaMesher data/control bytes if upstream instrumentation exposes them cleanly;
- startup/join simulated time separately from data delivery;
- no Pollicino PNB1/PNC1 mutation inside the mesh bridge.

## Gate 3 — Pollicino bearer adapter

Only after opaque payload works should adapter ID `loramesher` gain a registered Pollicino data-plane implementation.

Until then:

- `LoRaMesherBearerProbe` may select the `CONNECTED_MESH` lifecycle context;
- `NodeBearerTransport` deliberately fails closed for adapter `loramesher` because no validated data bridge exists.

## Hardware boundary

No result in Gate 1 or Gate 2 proves compatibility with the user's exact LILYGO/TTGO T3 V1.6.1 pins/radio wiring or physical mesh behavior.

Exact-board build/operation, startup/join time, range, wall/floor behavior, useful contact capacity and energy remain later physical/embedded work.

**GATE PROVE FISICHE HW-006** remains required before using real LoRa values in Pollicino routing or capacity models.
