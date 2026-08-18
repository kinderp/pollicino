# PollicinoNet — discovery, reconstruction and semantic transport over scarce links

PollicinoNet is the network-level research branch of POLLICINO.

The codec asks:

> **How few bits must be transmitted to reconstruct a byte sequence exactly when encoder and decoder share useful prior information?**

PollicinoNet generalizes the objective:

> **How few transmitted bits are needed for another node to locate, derive, reconstruct or experience the requested information?**

The core rule is:

> **Do not transmit the content when transmitting enough information to locate, derive or reconstruct it costs fewer bits.**

LoRa is the first scarce-link target because long range and low bitrate make every transmitted bit expensive, but the architecture must remain transport-independent.

---

## 1. Layering

PollicinoNet must not absorb application semantics or radio-specific details into the codec.

```text
Application / domain
        |
        v
structured object / content descriptor
        |
        v
+---------------------------+
|       PollicinoNet        |
| discovery / exact /       |
| semantic / resolver / P2P |
+---------------------------+
        |
        +--------------------+
        |                    |
        v                    v
Pollicino Codec        Transport adapters
compression /          LoRa / BLE / Wi-Fi /
exact residuals        Internet / future links
```

Responsibilities:

- **application/domain:** what the information means, who may receive it, consent and business rules;
- **PollicinoNet:** whether to advertise, reference, retrieve, transfer, reconstruct, cache or relay it;
- **Pollicino Codec:** deterministic binary representation, compression, residual coding and exact reconstruction;
- **transport adapter:** physical/link delivery constraints.

---

## 2. Three modes

### 2.1 DISCOVERY

The scarce link transports only enough information to discover or rendezvous with content or a peer.

```text
LoRa beacon
   |
   v
short coordinate / rendezvous token
   |
   v
resolver when a richer network exists
   |
   +--> Pollicino P2P
   +--> IPFS/CID
   +--> BitTorrent/info-hash
   +--> HTTPS
   +--> local/LAN source
```

The short coordinate is **not** treated as proof of the content. It is a rendezvous key. The retrieved manifest carries the full cryptographic identity needed for verification.

### 2.2 EXACT

The receiver must reproduce the exact original bytes.

Possible block modes include:

```text
known-content reference
known-chunk reference
delta against known chunk
classical compression
learned entropy coding
prediction + exact residual
raw fallback
```

The contract is always:

```text
SHA256(original) == SHA256(reconstructed)
```

When Internet is absent, nodes may exchange missing chunks over a scarce link or use store-and-forward peers. When a higher-bandwidth local link becomes available, PollicinoNet should hand over the payload rather than insist on LoRa.

### 2.3 SEMANTIC

For realtime media the receiver may reconstruct an equivalent experience instead of bit-identical samples or pixels.

Examples:

- ultra-low-bitrate speech parameters;
- facial landmarks / expression state;
- avatar motion;
- semantic scene updates.

This mode is explicitly **lossy/perceptual** and must never be confused with EXACT.

Authoritative records, signatures, consent objects and cryptographic material must not silently cross from EXACT to SEMANTIC.

---

## 3. Content descriptors and coordinates

A PollicinoNet descriptor should separate a compact radio coordinate from the complete manifest.

Conceptually:

```text
ShortCoordinate
- protocol/version
- rotating or scoped rendezvous key
- object class
- expiry / hop budget
- optional capability hints
- compact authenticator
```

Resolved manifest:

```text
ContentManifest
- full content identity/hash
- media/object type
- exact vs semantic contract
- size/chunking information
- available retrieval methods
- encryption/key-agreement metadata where applicable
- provenance
- expiry/revocation information
```

A short hash prefix alone is never sufficient proof of identity because collisions increase as identifiers are shortened.

---

## 4. P2P reconstruction

The useful unit is a content-addressed chunk rather than an entire file.

```text
file
 |
 +-- chunk A -- already present --> 0 payload bytes
 +-- chunk B -- near match -------> reference + exact patch
 +-- chunk C -- missing ----------> compressed/residual transfer
 +-- chunk D -- held by peer -----> retrieve from peer
```

Nodes can maintain a local `PollicinoStore` containing:

- complete objects;
- content-addressed chunks;
- dictionaries;
- model/checkpoint identities;
- previous versions useful for delta coding;
- manifests and provider hints.

The network should exchange availability summaries compactly and avoid retransmitting chunks already available at the receiver.

---

## 5. Delay/disruption tolerant operation

PollicinoNet should support intermittent connectivity rather than assume a permanent end-to-end path.

Useful primitives:

- TTL / expiry;
- hop limit;
- duplicate suppression;
- store-and-forward;
- resumable chunk transfer;
- partial manifests;
- opportunistic richer-link handover;
- explicit acknowledgement policy;
- forward-error correction where justified;
- final end-to-end cryptographic verification.

A node may learn about content over LoRa, carry that knowledge physically for hours, and resolve/download it only when Internet or another peer later becomes available.

---

## 6. Integration with DNA / Travel DNA

The repositories `kinderp/dna` and the imported Travel domain already separate **discovery**, **rendezvous** and **data exchange** and model communication through replaceable transport adapters. PollicinoNet fits underneath those contracts rather than replacing them.

Recommended responsibility split:

```text
DNA / Travel DNA
  identity, intent, consent, visibility,
  DNATrace, DNAFragment, GeoRoom, domain semantics
              |
              v
DNA CommunicationTransport / Discovery ports
              |
              v
PollicinoNet adapter/service
  coordinate, resolver, cache, P2P,
  exact/semantic contract, scarce-link planning
              |
              v
Pollicino codec + physical transports
  LoRa / BLE / Wi-Fi / Internet
```

### 6.1 DNATrace over PollicinoNet DISCOVERY

A `DNATrace` is already defined as a minimal pseudonymous temporary discovery object. This is a natural LoRa payload.

For very small trace payloads, a schema-aware deterministic binary representation is likely more useful than invoking an expensive neural codec. Candidate techniques:

- fixed version/domain/capability dictionaries;
- bit masks for domain and rendezvous capabilities;
- varints for intent codes, nonce and lifetime;
- compact relative expiry rather than textual timestamps;
- rotating ephemeral identifiers;
- compact application authenticator.

The JSON schema remains the domain contract; the compact wire representation is a transport encoding.

### 6.2 Rendezvous over LoRa, payload elsewhere

Typical flow:

```text
Device A                         Device B
   |                                |
   |---- compact DNATrace/LoRa ---->|
   |                                |
   |<--- compact rendezvous --------|
   |                                |
   +====== Internet/Wi-Fi/P2P ======+
             authorized data
```

The LoRa exchange can advertise a one-time/scoped PollicinoNet coordinate. After consent, the richer network resolves it to the complete manifest and retrieves the authorized data.

### 6.3 DNAFragment transport

A `DNAFragment` is an authorized, limited view of a profile and therefore belongs to the EXACT contract unless a future schema explicitly says otherwise.

Preferred order:

1. exchange only a coordinate if a richer path exists;
2. fetch the fragment over Internet/Wi-Fi/P2P;
3. exploit cache/content-address references when the receiver already has shared material;
4. use exact Pollicino coding for the missing bytes;
5. use LoRa chunk transfer only as a last-resort path when no richer transport is available.

Never transmit the complete private `DNAProfile` merely because the link can carry it.

### 6.4 Travel DNA examples

PollicinoNet can support Travel DNA without coupling the travel domain to LoRa:

- discover another traveller/group with compatible intent;
- exchange a short coordinate for a GeoRoom or authorized Travel fragment;
- advertise a POI/route/guide manifest and download it later over Internet;
- propagate a Cartolina/content coordinate rather than its photo/video payload;
- synchronize small exact route/itinerary updates when offline;
- transfer missing map/guide chunks opportunistically over Wi-Fi Direct or peers;
- carry discovery metadata across disconnected areas with store-and-forward.

Safety-critical navigation or emergency delivery must not depend on an experimental PollicinoNet path without an independently validated reliability design.

---

## 7. Privacy and security invariants for DNA

PollicinoNet must preserve DNA's privacy-by-default model.

Rules:

1. **Compress before encrypting.** Ciphertext is intentionally incompressible; exact compression/deduplication happens before end-to-end encryption when policy permits.
2. **No persistent public radio identity.** Use rotating/scoped rendezvous identifiers.
3. **No sensitive public content hash.** For private content, a stable content hash can itself become a correlatable identifier. Public radio advertisements should use scoped/keyed/rotating coordinates when necessary.
4. **Authenticate at the application envelope.** Do not assume the physical link provides sufficient authenticity or replay protection.
5. **Respect consent and expiry.** Cache and relay logic must honor revocation/retention rules where the application contract requires it.
6. **Minimize metadata.** A compact packet that leaks identity, precise location or rare interests is not a successful optimization.
7. **Separate EXACT and SEMANTIC.** DNA claims, consent, signatures and authoritative state remain exact.

---

## 8. Adaptive path selection

The same object may be delivered differently depending on context.

```text
Need object X
    |
    +-- Internet available?
    |       yes -> DISCOVERY coordinate + Internet retrieval
    |
    +-- local high-bandwidth peer available?
    |       yes -> Wi-Fi/BLE rendezvous + exact P2P
    |
    +-- receiver already owns most chunks?
    |       yes -> references + exact residuals
    |
    +-- only scarce link available?
    |       yes -> prioritized/resumable EXACT transfer
    |
    +-- realtime perceptual media?
            yes -> SEMANTIC mode if explicitly requested
```

The application states requirements; PollicinoNet chooses a permitted reconstruction/delivery strategy.

---

## 9. Primary research metric: Transmission Reconstruction Cost

Compression ratio alone is insufficient for a network system.

Define an experimental accounting metric:

```text
TRC =
    discovery bits
  + rendezvous bits
  + manifest bits
  + missing/reference/residual payload bits
  + FEC bits
  + acknowledgement bits
  + retransmission bits
```

Track separately:

- useful payload bytes;
- radio bytes and airtime;
- content/cache hit ratio;
- model/dictionary side-information cost;
- encode/decode/reconstruction compute;
- energy proxy;
- latency / time-to-reconstruction;
- successful handover rate;
- duplicate/relay overhead;
- exact hash verification rate;
- privacy/metadata exposure class.

The research objective is a Pareto frontier, not one magic score.

---

## 10. Proposed experiment sequence

### PN-001 — Compact DNA trace

Take real `DNATrace v0.1` examples and compare:

- JSON;
- CBOR/MessagePack baseline;
- custom schema-aware deterministic binary encoding;
- generic classical compression;
- Pollicino codec where meaningful.

Measure total on-air bytes including integrity/authentication overhead.

### PN-002 — LoRa-like impaired-link simulator

Extend/mock a scarce transport with:

- payload cap;
- bitrate/airtime budget;
- loss;
- duplication;
- reorder;
- intermittent gateways;
- duty/budget constraints supplied as experiment parameters.

Validate discovery, expiry, replay protection and deduplication.

### PN-003 — Coordinate -> Internet retrieval

LoRa-like discovery transports only a compact coordinate. The receiver resolves a full manifest over a simulated Internet adapter and verifies the final object hash.

Primary question: how many scarce-link bytes are needed to discover and retrieve an arbitrary external object?

### PN-004 — DNAFragment exact transfer

After an explicit consent/rendezvous step, transfer an authorized `DNAFragment` through:

- Internet;
- local peer path;
- scarce-link fallback.

Verify bit-perfect reconstruction and revocation/expiry behavior.

### PN-005 — Cached P2P file reconstruction

Measure how radio traffic falls as peers share increasingly large chunk stores and previous object versions.

### PN-006 — Travel DNA field-oriented prototype

Use the Travel domain as the first application vertical:

- trace discovery;
- group/GeoRoom rendezvous;
- content coordinate;
- richer-link handover;
- offline/store-and-forward scenario.

Hardware comes only after the protocol is reproducible in the simulator.

### PN-007 — Semantic realtime branch

Only after the exact/discovery plane is stable, investigate speech and avatar/semantic media as a separate lossy contract.

---

## 11. Non-goals

PollicinoNet does **not** claim that:

- a short hash can reconstruct arbitrary unknown data;
- random/encrypted data can be losslessly compressed below their information content without side information;
- LoRa is an appropriate bulk-transfer medium when a better link exists;
- semantic reconstruction is lossless;
- anonymity is guaranteed merely because identifiers are pseudonymous;
- one radio technology should leak into DNA domain entities.

Its research question is narrower and testable: **how much can shared state, content addressing, prediction, caching, alternative transports and reconstruction compute reduce the scarce-link information that must actually cross the air?**
