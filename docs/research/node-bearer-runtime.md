# Pollicino Node bearer runtime

Status: host-side lifecycle prototype, 2026-08-28

## Purpose

The node bearer runtime answers one deliberately small question:

> Which connectivity context is usable now without changing the identity or persistent state of Pollicino objects/bundles?

It is **not** a routing algorithm and it does not infer physical contact capacity.

The current node lifecycle contexts are:

```text
DISCOVERING
    |
    +--> CONNECTED_MESH
    |
    +--> OPPORTUNISTIC_DTN
    |
    +--> RICH_HOME
```

`PollicinoNodeRuntime` owns the persistent object/bundle state. Bearer adapters only report local readiness.

## Generic controller

`NodeBearerController` consumes `BearerObservation` values from small `BearerProbe` adapters.

Default context priority:

```text
RICH_HOME
    > CONNECTED_MESH
    > OPPORTUNISTIC_DTN
    > DISCOVERING
```

This is a lifecycle priority, not a universal routing/cost preference.

### Entry and loss behavior

Positive observation of a higher-priority usable context is accepted immediately.

Loss of the current context is different: fallback requires repeated confirmation. The initial prototype uses two consecutive loss observations by default.

Example:

```text
OPPORTUNISTIC_DTN
      |
      | school mesh positively ready
      v
CONNECTED_MESH
      |
      | one failed status probe
      |    -> remain CONNECTED_MESH
      |
      | mesh recovered
      |    -> clear pending fallback
      |
      | two consecutive losses
      v
OPPORTUNISTIC_DTN
```

The hysteresis is intentionally observation-count based at this stage. It is not derived from a physical timeout or LoRa loss model.

## State invariant

A mode change must not alter:

- PCM1 manifest identity;
- verified chunks;
- PNB1 bundle identity;
- PNC1 custody record/hop count;
- application exact payload;
- persistent replay/idempotency state.

The controller delegates mode transitions to `PollicinoNodeRuntime.transition()` and never copies or transforms object data.

## LoRaMesher boundary

The current upstream LoRaMesher 1.0 API provides the diagnostics needed for a connected-mesh readiness adapter:

- `GetNetworkStatus()` including `current_state`, `connected_nodes`, `is_synchronized`, and `time_since_last_sync_ms`;
- `IsReadyToSend()` for protocol synchronization/TX-slot readiness;
- `GetTxQueueSize()` / `GetRxQueueSize()` for diagnostics if later justified.

The first Pollicino adapter uses only:

```text
running
is_synchronized
IsReadyToSend result
connected_nodes > 0
```

to decide whether `CONNECTED_MESH` is locally usable.

It does **not** expose or infer:

```text
contact capacity
LoRa throughput
RSSI/SNR quality score
range
packet-loss probability
future route availability
```

Those require separate evidence and, where physical, remain behind HW-006.

### LoRaMesher lifecycle constraint

The upstream 1.0 README documents:

- `Start()` returns a checked `Result`;
- `Stop()` halts protocol tasks and releases resources;
- there is no `resume`; the LoRaMesher instance should be rebuilt to restart.

Therefore a future embedded Pollicino adapter should treat re-entering `CONNECTED_MESH` after a real stop as **rebuild + Start**, not as a hidden resume call.

Pollicino bundle/cache/custody state must remain outside that LoRaMesher instance so the mesh can be destroyed/rebuilt without losing data-mule state.

Upstream reference checked 2026-08-28:
`https://github.com/LoRaMesher/LoRaMesher`

## Current hardware compatibility boundary

LoRaMesher advertises RadioLib support for SX1276-family radios, but that is not by itself proof that the user's exact LILYGO/TTGO T3 V1.6.1 pin/radio configuration works with current LoRaMesher 1.0.

Do not claim exact-board compatibility until the configuration is built and later exercised on the actual hardware.

## FreakWAN role

FreakWAN remains a practical off-grid/flooding field baseline, not the implementation behind `OPPORTUNISTIC_DTN` in this prototype.

The architecture remains:

```text
                 Pollicino Node state
          exact / cache / bundle / custody
                       |
              bearer lifecycle
              /       |       \
             /        |        \
     LoRaMesher   raw/off-grid   rich home
       school         DTN        Wi-Fi/etc.
             \
              \
          FreakWAN as
          field baseline
```

## Gate decision

The bearer-runtime abstraction passes the architecture gate because at least two materially different primary use cases require the same state to survive network-context changes:

- UC-DNA-001 — school topic mixing -> territorial data mule;
- UC-CONTENT-001/002 — reference/content discovery -> physical carry -> home resolution.

**Decision: PROTOTYPE / CONTINUE.**

Production adoption still requires adapter comparison, security design, embedded resource measurements and later physical evidence.

## Physical boundary

The bearer controller may be tested on host/synthetic snapshots now.

Any claim that LoRaMesher is actually reachable, stable, faster, more energy efficient or preferable on the real student network remains behind:

**GATE PROVE FISICHE HW-006**
