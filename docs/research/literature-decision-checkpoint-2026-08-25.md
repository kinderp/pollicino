# Literature-driven architecture checkpoint — 2026-08-25

This checkpoint applies the new `use-case-justification-gate.md` to the three literature branches selected for deeper study: BPv7/DTN, set reconciliation, and LoRaMesher/Reticulum.

The purpose is to turn literature into decisions, including decisions **not** to implement something yet.

## 1. BPv7 / DTN: map first, do not integrate yet

### What the standard already covers

RFC 9171 defines Bundle Protocol v7 as a store-carry-forward overlay for stressed networks with intermittent connectivity, physical motility, opportunistic/scheduled contacts and heterogeneous underlying networks through convergence-layer adapters.

It also defines bundle lifetime/expiration, hop-count extension semantics, fragmentation/reassembly and forwarding procedures.

Important boundary: BPv7 deliberately does **not** define the bundle route-computation algorithm or how routing/forwarding information bases are populated. This means our routing-policy research is not made redundant by BPv7; routing can remain an experimental layer even if a future BPv7 adapter exists.

The convergence layer is also a useful architectural analogue for PollicinoNet bearers: a CLA sends/receives bundles using some underlying network protocol and reports transmission disposition. BPv7 additionally requires congestion/rate limiting at the convergence layer because long DTN RTTs are unsuitable for ordinary end-to-end reactive congestion control.

### Where BP fragmentation differs from Pollicino chunks

BPv7 can fragment a bundle when a future contact is too short to forward it whole. This is directly relevant to our contact-window work.

However Pollicino chunking has a different intended value:

- chunk identities are content hashes;
- chunks can already exist at the receiver;
- chunks can be cached/reused across sessions and possibly across related objects;
- exact reconstruction is verified against the content manifest/object hash.

Therefore BP fragmentation is a baseline for **contact-sized transport fragmentation**, while PCM1/chunks are also a **receiver-knowledge/content-reuse representation**. We should measure whether both layers are ever necessary rather than assume they are.

### Use-case gate

Current concrete need: avoid reinventing DTN semantics and understand interoperability options.

Current missing need: no external system in the active project requires PollicinoNet to exchange BPv7 bundles today.

**Decision: RESEARCH ONLY.**

Next artifact should be a semantic ADR mapping PNB1/PNC1/PCM1/PNA1 and bearer/route responsibilities to BPv7 concepts. Do not implement a BPv7 stack or change PNB1 until an interoperability use case exists.

Potential future use cases that would reopen the gate:

1. interoperating with an external BPv7 implementation/testbed;
2. using an established DTN stack below Pollicino object reconciliation;
3. exchanging test scenarios/results with standard DTN tooling;
4. a field deployment where BPv7 management/security ecosystem removes more complexity than it adds.

## 2. Set reconciliation: PNA2 passes the use-case gate, but not a specific algorithm

### Concrete use case

A relay/receiver shares a very large manifest or inventory with another node. The two inventories differ only in a small number of chunks, and the contact byte budget is scarce.

This is directly aligned with the Pollicino objective: communicate information proportional to what the receiver lacks rather than proportional to the whole object/state.

### Current PNA1 scaling

Current PNA1 availability encoding has a 39-byte fixed header plus one bit per manifest chunk:

`PNA1 bytes = 39 + ceil(chunk_count / 8)`

Examples:

| Chunk count | PNA1 bytes |
| ---: | ---: |
| 1,000 | 164 |
| 10,000 | 1,289 |
| 100,000 | 12,539 |
| 1,000,000 | 125,039 |

This is excellent when the universe is moderate or availability is dense/unknown. It becomes expensive on a scarce link when the manifest is huge and the symmetric difference is tiny.

### Literature candidates

`minisketch` implements BCH/PinSketch-style set reconciliation. Its key property is that sketch size can depend on the configured difference capacity rather than the full set size, and two sketches can be combined to decode the symmetric difference.

IBLT and Rateless IBLT provide another family. Rateless reconciliation is especially interesting when the difference cardinality is not known in advance: encoded reconciliation symbols can be sent incrementally until decoding succeeds.

### But simple codecs may be better for Pollicino

Pollicino often has more structure than the generic two-set problem. Once both peers know the same PCM1 manifest, the universe and chunk ordering are already shared.

Therefore the first PNA2 experiment must include:

1. current bitmap PNA1;
2. sparse list of missing/available chunk indices;
3. run-length/range encoding of indices;
4. compressed bitmap where worthwhile;
5. minisketch/PinSketch-style reconciliation;
6. IBLT or rateless reconciliation if the first experiments justify it.

For example, if a complete source knows a 1,000,000-chunk manifest and the receiver is missing only 20 chunks, a direct list of 20 indices may beat a general reconciliation sketch in both wire bytes and CPU. Complexity is justified only when both peers can be partial, the difference direction is unknown, the difference cardinality is unknown, or repeated/adaptive reconciliation makes the sketch family materially better.

### PNA2 experiment design

Test at least:

- total chunks N: 1e3, 1e4, 1e5, 1e6;
- difference d: 1, 5, 20, 100, 1,000 and dense regimes;
- complete-source vs partial-relay/partial-relay cases;
- one-way and bidirectional contact opportunities;
- exact known d vs unknown d;
- benign and adversarial/collision-aware hash choices where applicable.

Metrics:

- bytes on scarce link;
- number of request/response rounds;
- CPU time;
- RAM;
- decode success/failure probability;
- extra retransmission caused by decode failure;
- implementation/security complexity.

Final object SHA-256 remains the exact reconstruction oracle; a compact reconciliation codec must never weaken final exactness.

### Use-case gate

**Decision: PROTOTYPE.**

The use case is real and measurable, but the implementation target is a **codec benchmark**, not “IBLT by default”. Adoption occurs only if a codec beats the simpler baselines in a regime we actually care about.

## 3. LoRaMesher: candidate connected-segment bearer, not replacement for DTN

Current LoRaMesher provides a mature LoRa mesh implementation with distance-vector routing, TDMA, network formation, gateway/capability discovery, TTL flooding/de-duplication, RadioLib support including SX1276-family radios, desktop simulation and reliable/large-transfer work.

This overlaps with radio-network mechanics that PollicinoNet should not reimplement without a specific reason.

But LoRaMesher and current PollicinoNet solve different connectivity assumptions:

- LoRaMesher is strongest when a contemporaneously connected LoRa mesh exists and routing/slot state can be maintained;
- PollicinoNet's store-carry-forward overlay remains useful when contacts disappear for long periods and no end-to-end path exists.

A plausible composition is therefore:

`Pollicino object/reconciliation/DTN layer -> LoRaMesher connected bearer/segment -> radio`

rather than replacing one project with the other.

### Use-case gate

Concrete use case:

> Several student/relay nodes form a temporarily connected LoRa cluster. PollicinoNet should exploit multi-hop connectivity inside that cluster without making its object/reconciliation layer implement its own full mesh routing/TDMA system.

**Decision: PROTOTYPE/COMPARE, not ADOPT.**

First use LoRaMesher's native simulation/host environment or an adapter mock. Measure API/wire overhead and architectural fit. Physical comparison follows later when HW-006/field evidence is available.

## 4. Reticulum: stronger architectural challenge, but no adoption use case yet

Reticulum is particularly relevant because it already offers a bearer/interface-neutral network stack across LoRa/RNode, Ethernet/Wi-Fi, serial, TCP/UDP/IP, pipes and custom interfaces. It also has compact destination-oriented packet formats, signed announces, path discovery, rate limiting and interface-specific airtime controls.

This challenges any claim that PollicinoNet needs to invent a generic heterogeneous network substrate.

It does **not** automatically replace PollicinoNet's content/object layer. Reticulum primarily provides network identity, paths, interfaces and secure communication. Pollicino's distinguishing experiment remains receiver-knowledge-aware exact object transfer/reconciliation and evidence/TRC accounting.

Reticulum's published packet examples also give useful overhead baselines: path request, announce, link request/proof and keepalive traffic are explicit network costs. Those should be measured against Pollicino's small-control-plane goals before considering an adapter.

RNode firmware supports SX1276-class transceivers and several LilyGO/ESP32 families, but exact support for the current Pollicino hardware revision must be verified before any physical plan. Do not infer board compatibility from transceiver-family support alone.

### Use-case gate

Possible use case:

> Replace multiple custom bearer/path/security mechanisms with a mature heterogeneous secure substrate while PollicinoNet remains an application/object reconciliation layer.

This is architecturally significant and therefore needs at least two concrete use cases or an external interoperability constraint before adoption.

Today we have one broad motivation but not enough evidence that replacing the current small bearer layer reduces total complexity.

**Decision: RESEARCH ONLY + adapter/overhead experiment later.**

## 5. Resulting near-term order

The use-case gate changes the near-term work order:

1. **PNA2 codec benchmark** — passes the gate and attacks the central minimum-information objective directly.
2. **Canonical DTN routing baselines** — Epidemic, Spray-and-Wait, PRoPHET and RAPID-like, because routing claims need literature baselines.
3. **BPv7 semantic ADR** — research/documentation only; no implementation until interoperability is needed.
4. **LoRaMesher adapter experiment** — connected-segment use case exists; benchmark before adoption.
5. **The ONE trace interoperability** — justified when canonical baselines are in place so our simulator can reproduce/consume established scenarios.
6. **Reticulum overhead/adapter study** — research until multiple concrete use cases justify a new architectural dependency.

## 6. General lesson

Literature is not a shopping list of features.

For PollicinoNet, the correct process is:

`use case -> prior art/literature -> simplest baseline -> measurable hypothesis -> isolated experiment -> evidence -> adopt/defer/reject`

not:

`interesting paper/project -> add feature`.

This order should be applied prospectively to both new code and new architecture.
