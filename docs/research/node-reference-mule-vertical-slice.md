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

This checkpoint does **not** claim a LoRaMesher integration, automatic physical bearer detection, measured RF performance or a production BitTorrent/NAS adapter.

## New prototype pieces

### `PortableReference`

`pollicino.integrations.reference_mule.PortableReference` is an application object carried as ordinary Pollicino EXACT bytes.

It contains:

- opaque `provider_id`;
- opaque locator bytes;
- optional human label;
- small string metadata.

Examples of provider IDs can include `magnet`, `http`, `filesystem`, `cid` or future application-specific resolvers. The Pollicino network core does not interpret or execute the locator.

A magnet URI therefore is not a new Pollicino wire protocol. It is simply the payload of a small exact object.

### `HomeReferenceResolver`

The home resolver is an explicit application-layer dispatcher. It invokes only handlers deliberately registered by the caller and performs no hidden networking itself.

This keeps external side effects such as NAS access, HTTP retrieval or an authorized BitTorrent client outside PollicinoNet core.

### `PollicinoNodeRuntime`

The host-side node runtime persists:

- a crash-safe `DirectoryPollicinoStore`;
- verified PCM1 manifest registry;
- partial or complete chunk state;
- immutable PNB1 bundle identity;
- node-local PNC1 custody records;
- contact IDs originated by this node for persistent replay suppression;
- current lifecycle mode.

Prototype modes:

```text
DISCOVERING
CONNECTED_MESH
OPPORTUNISTIC_DTN
RICH_HOME
```

Changing mode never rewrites object identity, manifest, bundle identity, custody hop or chunk bytes.

The runtime reuses existing `forward_contact()` and `governed_forward_contact()` implementations rather than creating another network protocol.

## Validated exact reference-mule flow

Actions `33188000071` — PASS.

The first test performs:

1. student A and student B enter `CONNECTED_MESH`;
2. A creates an authorized demo portable reference and seeds it as a normal PCM1 exact object;
3. A -> B executes a deterministic scarce-link store-forward contact;
4. B reconstructs and verifies the exact reference;
5. B transitions to `OPPORTUNISTIC_DTN`;
6. B is destroyed/re-created from the same persistent directory, proving mode + verified object state survive restart;
7. B -> HOME executes another scarce-link contact;
8. HOME transitions to `RICH_HOME`;
9. HOME reconstructs the portable reference and explicitly dispatches it to a registered `magnet` test handler;
10. both network contacts report non-zero modeled wire traffic.

A second test interrupts the object after one chunk, changes mode, restarts the mule, and later completes the object. Already verified PCM1/chunk state survives and is reused.

## Validated node-local governed custody

Actions `33188310500` — PASS.

The governed vertical test extends the same daily carry with PNB1/PNC1 semantics:

```text
student A
  PNC1 custody hop 0
        |
        | school governed contact
        v
student B
  PNC1 custody hop 1
        |
        | mode change + restart
        | territorial governed contact
        v
home gateway
  PNC1 custody hop 2
```

Each runtime persists only its own custody observations. During a directional encounter, a temporary ledger is assembled from the minimum source/target records required by the existing governance implementation. The whole network custody graph is not copied into either node.

Validated properties:

- source custody hop 0 survives publication;
- student mule obtains hop 1 and bundle identity;
- mule restart preserves exact payload, PCM1 manifest, PNB1 identity and its own PNC1 record;
- restarted mule can act as authoritative source of the second hop;
- HOME receives hop 2;
- replaying the same source-originated `contact_id` after another restart is `duplicate_suppressed` with **0 wire bytes**;
- `hop_limit=1` permits the first hop and rejects the second hop with **0 wire bytes**.

This removes the earlier campaign-global custody limitation from the vertical slice without introducing a global routing oracle.

## What this proves

At host/model scope, the following architecture is executable rather than only documented:

```text
one Pollicino EXACT object / bundle
        |
        +-- school connected context
        |
        +-- node-local custody
        |
        +-- persistent carry/restart
        |
        +-- afternoon DTN context
        |
        +-- home rich-network resolution
```

The application reference can be tiny even when the content resolved later is large. Pollicino transports the minimum reference object; a rich-network application decides explicitly what to do with it later.

## Current limitations / next gates

### 1. Bearer runtime — ACTIVE

`NodeMode` now has a generic lifecycle controller under validation. The required behavior is:

- positively detected richer context can be entered immediately;
- a single lost mesh/status observation must not cause flapping;
- repeated loss confirmation permits fallback;
- mode transitions must preserve exact object, PNB1 identity and PNC1 custody.

No real LoRaMesher dependency or radio-quality inference belongs in this controller.

### 2. LoRaMesher / FreakWAN adapters

Not physically integrated in this checkpoint.

- LoRaMesher remains a connected-school bearer candidate.
- raw Pollicino remains the DTN/evidence baseline.
- FreakWAN remains a practical off-grid field baseline.

The first LoRaMesher adapter should map its own runtime readiness/status into the generic bearer controller. It must not invent contact capacity from synchronization status.

### 3. Real home adapters

No qBittorrent, filesystem/NAS or HTTP side effect is performed. Add those only as explicit opt-in application adapters with authorization/policy tests.

### 4. DNA full application layer

The existing DNATrace adapter is not yet the full Topic/Subscription/Geo/expiry/provenance vertical. That should reuse this node runtime after bearer lifecycle is stable.

### 5. Physical evidence

All contact bytes in this slice are deterministic model execution.

Real LoRa contact capacity, range, NLOS performance and radio-driven mode-selection claims remain behind **GATE PROVE FISICHE HW-006**.

## Gate decision

**PROTOTYPE / CONTINUE.**

The reference-mule use case now has executable exact transfer, persistence, node-local bundle governance/custody and rich-home application resolution. The next justified layer is bearer lifecycle/adapters. This does not justify a new wire format, automatic LoRaMesher adoption or physical deployment claims.
