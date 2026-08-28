# Pollicino Node reference-mule vertical slice

Status: host-side prototype checkpoint, 2026-08-28

## Goal

Turn the existing PollicinoNet exact/store-forward primitives into the first complete software slice of the daily student data-mule workflow:

```text
school / CONNECTED_MESH
        |
        v
portable student node
        |
        | physical carry + runtime restart
        v
OPPORTUNISTIC_DTN
        |
        v
home node
        |
        v
RICH_HOME -> application resolver
```

This checkpoint does **not** claim a LoRaMesher integration, automatic bearer detection, physical RF performance or a production BitTorrent/NAS adapter.

## New prototype pieces

### `PortableReference`

`pollicino.integrations.reference_mule.PortableReference` is an application object carried as ordinary Pollicino EXACT bytes.

It contains:

- opaque `provider_id`;
- opaque locator bytes;
- optional human label;
- small string metadata.

Examples of provider IDs can include `magnet`, `http`, `filesystem`, `cid` or future application-specific resolvers. The Pollicino network core does not interpret or execute the locator.

This means a magnet URI is not a new Pollicino wire protocol. It is simply the payload of a small exact object.

### `HomeReferenceResolver`

The home resolver is an explicit application-layer dispatcher. It invokes only handlers deliberately registered by the caller and performs no hidden networking itself.

This keeps external side effects such as NAS access, HTTP retrieval or an authorized BitTorrent client outside PollicinoNet core.

### `PollicinoNodeRuntime`

The first host-side node runtime persists:

- a crash-safe `DirectoryPollicinoStore`;
- the verified PCM1 manifests the node knows;
- partial or complete chunk state in the existing store;
- the current lifecycle mode.

Prototype modes:

```text
DISCOVERING
CONNECTED_MESH
OPPORTUNISTIC_DTN
RICH_HOME
```

Changing mode never rewrites object identity, manifests or chunk bytes.

The runtime reuses the existing `forward_contact()` implementation rather than creating another transfer protocol.

## Validated vertical flow

Actions `33188000071` — PASS.

The test performs:

1. student A and student B enter `CONNECTED_MESH`;
2. A creates an authorized demo portable reference and seeds it as a normal PCM1 exact object;
3. A -> B executes a real deterministic scarce-link store-forward contact;
4. B reconstructs and verifies the exact reference;
5. B transitions to `OPPORTUNISTIC_DTN`;
6. B is destroyed/re-created from the same persistent directory, proving mode + verified object state survive restart;
7. B -> HOME executes another scarce-link contact;
8. HOME transitions to `RICH_HOME`;
9. HOME reconstructs the portable reference and explicitly dispatches it to a registered `magnet` test handler;
10. both network contacts report non-zero modeled wire traffic.

A second test interrupts the object after only one chunk, changes mode, restarts the mule, and later completes the object. The already verified PCM1/chunk state survives and is reused.

## What this proves

At host/model scope, the following architecture is now executable rather than only documented:

```text
one Pollicino object identity
        |
        +-- school connected context
        |
        +-- persistent carry/restart
        |
        +-- afternoon DTN context
        |
        +-- home rich-network resolution
```

The application reference can be tiny even when the content resolved later is large. Pollicino transports the minimum reference object; a rich-network application decides what to do with it later.

## Current limitations / next gates

### 1. Node-local governed custody

The first runtime deliberately uses the already proven PCM1/PNA1 `forward_contact()` path. It does not silently recreate PNB1/PNC1 ownership inside the runtime.

Existing PNB1/PNC1 governance and durable `CustodyLedger` remain available in `pollicino.net.bundle`, but their current deterministic API uses a campaign ledger shared by the experiment.

Next gate: determine the smallest honest way to persist and exchange **node-local** custody/contact state without turning a local node runtime into a hidden global oracle.

### 2. Bearer runtime

`NodeMode` is currently explicit lifecycle context. No automatic mesh detection or hysteresis is implemented yet.

Next bearer work should expose a small adapter contract and prove the same object state survives adapter changes. Do not make LoRaMesher a dependency before the host adapter comparison passes.

### 3. LoRaMesher / FreakWAN

Not integrated in this checkpoint.

- LoRaMesher remains a connected-school bearer candidate.
- raw Pollicino remains the DTN/evidence baseline.
- FreakWAN remains a practical off-grid field baseline.

### 4. Real home adapters

No qBittorrent, filesystem/NAS or HTTP side effect is performed. Add those only as explicit opt-in application adapters with authorization/policy tests.

### 5. Physical evidence

All contact bytes in this slice are deterministic model execution.

Real LoRa contact capacity, range, NLOS performance and mode-selection claims remain behind **GATE PROVE FISICHE HW-006**.

## Gate decision

**PROTOTYPE / CONTINUE.**

The reference-mule use case now has an executable end-to-end host slice. This justifies continuing toward node-local governance and a bearer adapter contract; it does not justify a new wire format, automatic LoRaMesher adoption or physical deployment claims.
