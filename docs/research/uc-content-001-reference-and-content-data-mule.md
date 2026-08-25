# UC-CONTENT-001 — Reference and content data mule

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Summary

A portable Pollicino node opportunistically exchanges compact references, manifests, availability information and, when justified, small content chunks while the user is away from a rich network. Later, when the node reaches home Wi-Fi/Internet/NAS/local storage, it resolves those references and retrieves or reconstructs the complete authorized content.

The core use case is deliberately broader than BitTorrent. Candidate objects include:

- BitTorrent magnet URI / info-hash for content the user is authorized to retrieve;
- HTTP/HTTPS URL;
- content ID / CID / object hash;
- Pollicino manifest or short rendezvous coordinate;
- provider/source hints;
- files already present on a personal HDD/NAS/PC;
- music, documents, books, images, video, software, datasets and backups the user is authorized to possess/share;
- small content chunks when the scarce contact budget makes actual transfer worthwhile.

The scarce/off-grid network should not move a large object merely because it can. It should move the smallest information that will allow the receiving node to obtain or reconstruct the object later.

## Personal daily example

Morning / school or mobile encounter:

```text
peer A has or knows content X
        |
        +-- magnet/info-hash
        +-- URL/CID
        +-- Pollicino manifest
        +-- provider hint
        +-- availability state
        |
        v
portable Pollicino node B
```

Afternoon / home:

```text
portable node B
      |
      v
home Wi-Fi / Internet / NAS / HDD
      |
      +-- resolve magnet through an authorized BitTorrent client
      +-- fetch URL/CID
      +-- retrieve from personal NAS/HDD/peer
      +-- reconcile chunks already present locally
      |
      v
exact object verification
```

## Three mule modes

### Reference mule

Carry only a compact reference when later resolution is possible.

Examples:

```text
magnet / info-hash
URL
CID
object hash
Pollicino rendezvous coordinate
provider identifier
```

This is the preferred case for very large content when a rich retrieval path is expected later.

### Manifest mule

Carry enough structured information to identify, verify, plan or reconcile the object without carrying the complete payload.

Examples:

```text
object identity/hash
size/type
PCM1 or equivalent manifest
availability summary
provider/source hints
expiry/provenance where applicable
```

### Content mule

Carry actual chunks when this is cheaper or necessary, for example:

- object is small;
- no later provider is expected;
- receiver already possesses most chunks;
- a richer local bearer becomes available;
- a long physical carry can bridge otherwise disconnected networks.

## Wanted-list variant

The portable node may also carry requests rather than only references:

```text
WANTED
- object X
- album/document/dataset Y
- manifest Z
```

On encounter, another peer can answer:

```text
X -> I have the exact object
Y -> I know an authorized provider/reference
Z -> I have only some chunks
```

PollicinoNet can then decide whether to exchange a reference, manifest, reconciliation state or payload chunks.

This makes the node a mule for **demand, availability and references**, not only for content bytes.

## Why this is a PollicinoNet use case

The central hypothesis is:

> If a compact reference or receiver-specific residual is sufficient to obtain a large object later, carrying that small information across the scarce network is more valuable than attempting bulk transfer immediately.

The use case exercises several existing PollicinoNet ideas together:

- short rendezvous coordinates;
- content-addressed identity;
- manifests/chunks;
- PNA availability/reconciliation;
- store-carry-forward;
- bearer handover;
- exact SHA-256 reconstruction;
- source/provider hints;
- persistent requests and custody.

## Use-case gate

### Actor

A person carrying a portable Pollicino node between a dense contact environment and a home/local rich network.

### Situation

The user encounters peers while only a scarce or intermittent link is available, then later obtains Wi-Fi/Internet/NAS/local-disk access.

### Problem

Large objects are too costly or slow to transfer over LoRa/off-grid contacts, even though a few bytes or a small manifest may be enough to retrieve them later. Conversely, some objects are private/local and may require carrying a provider hint or selected chunks because no public Internet reference exists.

### Simplest baselines

Compare at least:

1. send nothing until both peers have Internet;
2. send a textual URL/magnet/reference as-is;
3. send a compact typed reference;
4. send a Pollicino manifest/provider hint;
5. send complete small content;
6. send only missing chunks when receiver state is known.

Do not add a new generic reference protocol if URI/magnet/CID/existing Pollicino coordinate already expresses the use case adequately.

## Reference classes

The experiment should treat reference syntax as payload, not bake every external ecosystem into the core.

Candidate typed reference classes:

```text
URI_REFERENCE
BITTORRENT_MAGNET
CONTENT_ID
POLLICINO_COORDINATE
POLLICINO_MANIFEST
LOCAL_PROVIDER_HINT
```

A future typed abstraction passes the architecture gate only if at least two independent reference ecosystems need common behavior beyond carrying opaque bytes.

## Authorization and safety boundary

This use case is intended for content the user has the right to possess, retrieve or share: personal files, public-domain/openly licensed material, authorized downloads, personal backups, licensed media where sharing/retrieval is permitted, project datasets and similar lawful content.

PollicinoNet should remain content-neutral at the transport layer while application/user policy determines whether a particular source or retrieval action is authorized.

## Measurable hypotheses

H1. Reference-mule mode reduces scarce-link bytes by orders of magnitude when large content can be resolved later through a rich path.

H2. Manifest/reconciliation mode reduces scarce-link bytes relative to full-object transfer when the receiver already owns substantial content state.

H3. Carrying requests plus provider hints increases eventual retrieval probability in disconnected networks compared with waiting for direct source-destination connectivity.

H4. The same object identity can survive transitions from LoRa/off-grid discovery to Wi-Fi/Internet/NAS retrieval without weakening exact verification.

## Metrics

Track separately:

- reference bytes;
- manifest bytes;
- reconciliation bytes;
- actual content bytes transferred on scarce links;
- total TRC/wire bytes;
- number of references resolved successfully later;
- time from discovery/request to complete retrieval;
- exact SHA-256 verification success;
- provider/source availability at resolution time;
- cache hit ratio and reused chunks;
- request duplication/suppression;
- per-bearer traffic;
- storage consumed by pending references/requests/manifests;
- expired/unresolvable references;
- metadata/privacy exposure.

Do not count rich-path payload bytes as scarce-link savings without reporting them separately. Reference mode moves cost in time/path; it does not make the payload cease to exist.

## Minimal synthetic experiment

Create nodes with a mixture of:

- locally owned exact objects;
- externally resolvable references;
- partial chunk stores;
- wanted lists;
- intermittent home/gateway contacts.

Compare:

```text
full-transfer attempt
vs
opaque reference mule
vs
manifest mule
vs
reference + reconciliation
vs
content chunks when no later provider exists
```

Object classes should span small messages through large synthetic files. External retrieval is simulated first; no unauthorized content or third-party download is required for the experiment.

## Success criteria

Continue toward implementation when there is a clearly defined regime where a reference/manifest strategy materially reduces scarce-link traffic while preserving eventual exact retrieval and without adding disproportionate protocol complexity.

A compact typed-reference layer should only be adopted if it measurably improves over carrying existing references as opaque authenticated payloads.

## Kill/defer criteria

Defer complexity if:

- ordinary URL/magnet/CID strings are already small enough for the target contact budget;
- a new reference envelope adds more wire overhead than it saves;
- provider hints cannot be resolved reliably enough to beat waiting for a rich connection;
- privacy/security metadata needed for a generic resolver becomes excessive;
- the object is small enough that direct exact transfer is simpler and cheaper;
- the proposed feature requires a new wire version without a measurable use-case benefit.

## Relationship with UC-DNA-001

The two use cases are independent but composable.

`UC-DNA-001` moves topic-scoped semantic micro-information through school mixing and territorial data mules.

`UC-CONTENT-001` moves references, requests, manifests and optionally chunks for arbitrary authorized content.

Together they are the second independent justification for studying a shared bearer/runtime abstraction that preserves Pollicino object state across connected-mesh, opportunistic-DTN and rich home-network phases.

## Physical evidence boundary

Reference/manifest selection and eventual-resolution behavior can be tested synthetically now.

Real claims about how many references/chunks fit into an actual LoRa encounter, practical airtime, loss, range, simultaneous school nodes or energy remain blocked by **HW-006** and subsequent measured campaigns.

## Decision

**Status: PRIMARY USE CASE / PROTOTYPE-DRIVING.**

It justifies experiments on opaque/typed references, wanted-state, provider hints, reconciliation and rich-link handover. It does not automatically justify implementing BitTorrent, IPFS or any other external distribution protocol inside PollicinoNet; those remain external resolvers/adapters unless a separate use case demonstrates otherwise.
