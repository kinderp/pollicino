# PollicinoNet related-work literature survey

Status: literature checkpoint, 2026-08-25

This document deliberately pauses feature invention and asks a more important question: which parts of PollicinoNet are already well studied, which systems are its closest technical relatives, which established baselines must be implemented before making research claims, and where a plausible original contribution may remain.

This is a related-work survey, not a novelty proof. A claim that PollicinoNet is novel would require a broader systematic search, including literature outside the sources below and, if commercialization/patenting ever matters, a separate prior-art analysis.

## Executive conclusion

PollicinoNet is not best described as a new mesh-routing protocol. Its present architecture sits at the intersection of several mature research areas:

1. Delay/Disruption-Tolerant Networking (DTN): persistent store-carry-forward under intermittent connectivity.
2. Opportunistic routing: deciding which encountered node should receive which message under scarce contact time, storage and energy.
3. Information-/content-centric networking: identifying and caching data independently of host location.
4. Distributed synchronization and set reconciliation: communicating what differs rather than retransmitting a whole dataset.
5. LPWAN adaptation/compression: exploiting shared context to replace verbose information with compact identifiers and residuals.
6. LoRa mesh networking: discovery, routing, fragmentation, reliability and multi-hop operation over LoRa radios.
7. Heterogeneous/post-IP networking: moving information across LoRa, BLE, Wi-Fi, Internet and even physical transport without making IP connectivity the primary abstraction.

The closest conceptual ancestor of the current PollicinoNet core is DTN/Bundle Protocol, not Netsukuku. Netsukuku remains important for a different future problem: scalable, decentralized route-state representation when a large contemporaneously connected mesh exists.

A plausible research contribution for PollicinoNet is therefore not "multi-hop LoRa", "bundles", "TTL", "content addressing" or "store-and-forward" individually. Those ideas already have substantial prior work. The more interesting hypothesis is the combination of disruption-tolerant multi-bearer delivery with exact content reconciliation, an explicit objective of minimizing information sent relative to receiver knowledge, rigorous synthetic-vs-physical evidence accounting, and eventually Pollicino's learned/model-assisted reconstruction.

## 1. Netsukuku and QSPN

Netsukuku was designed as an autonomous peer-to-peer network capable of handling very large node counts with limited CPU and memory, without central servers, ISPs or an authority. Its topology work groups nodes recursively into a fractal hierarchy so that a node need not retain a flat route entry for every possible peer. QSPN (Quantum Shortest Path Netsukuku) propagates tracer information to discover efficient routes and update route knowledge when links change.

This is highly relevant to PollicinoNet's long-term scalability, especially if a student network grows from tens to hundreds or thousands of simultaneously reachable nodes. It is less directly equivalent to the current PollicinoNet core: Netsukuku is primarily solving decentralized layer-3-like route discovery in a mesh, whereas PollicinoNet currently assumes that connectivity can disappear completely and that data may need to be stored for hours before being physically carried to another node.

Ideas worth retaining from Netsukuku:

- hierarchical/compact route state rather than global flat topology;
- distributed discovery and no central routing authority;
- link-quality-aware route information;
- explicit design for small-resource nodes;
- treating naming/discovery as distributed infrastructure (ANDNA is also worth reading).

Do not copy QSPN into PollicinoNet merely because it is interesting. First establish whether a future route-state layer is actually required above the DTN/opportunistic layer.

Primary references:

- Andrea Lo Pumo, *Overview of the Netsukuku network*, arXiv:0705.0815, 2007.
- Andrea Lo Pumo, *Quantum Shortest Path Netsukuku*, arXiv:0705.0817, 2007.
- Andrea Lo Pumo, *The Netsukuku network topology*, arXiv:0705.0819, 2007.
- Dyne.org, *Netsukuku architecture overview*.

## 2. DTN and Bundle Protocol: the closest standards family

RFC 9171 standardizes Bundle Protocol version 7 (BPv7). DTN is explicitly designed for intermittent connectivity, variable/large delays and stressed links. BP forms a store-carry-forward overlay over heterogeneous underlying networks through convergence-layer adapters. A sender and final receiver do not need to be online at the same time.

This overlaps strongly with PollicinoNet:

| PollicinoNet concept | Closest DTN/BP concept | Important difference |
| --- | --- | --- |
| PNB1 bundle | BP bundle/blocks | PNB1 is much smaller and project-specific, not BPv7 compliant. |
| TTL | Bundle lifetime/age | Semantics and encoding are not identical. |
| hop limit | BP Hop Count extension block | Similar safety goal, not wire-compatible. |
| LoRa/BLE/Wi-Fi/Internet bearer | BP convergence-layer adapter | Pollicino's bearer evidence/TRC model is project-specific. |
| persistent relay | DTN persistent store-and-forward | Very close architectural idea. |
| custody PNC1 | BPv6/BIBE custody-family concepts | BPv7 removed old primary custody semantics; PNC1 must not be called BPv7 custody. |

This means PollicinoNet should not evolve as if Bundle Protocol did not exist. A future architecture decision should explicitly choose among three positions: implement a BPv7 convergence/application profile, offer a BPv7 gateway/adapter, or remain a smaller experimental protocol while maintaining a documented semantic mapping.

Security is also a major lesson. RFC 9172 (BPSec) provides integrity and confidentiality mechanisms for bundles. Checksums in current PollicinoNet detect accidental corruption; they are not adversarial authentication. Before a real student network carries nontrivial data, authenticated identities, integrity, confidentiality, replay policy and metadata privacy become a hard design requirement.

DTN is not merely historical research. NASA states that its multi-center DTN project completed in January 2026 and DTN is now operational in the Near Space Network and Deep Space Network. This validates the store-and-forward architectural family as production infrastructure, not just a simulator concept.

Primary references:

- IETF RFC 9171, *Bundle Protocol Version 7*, 2022.
- IETF RFC 9172, *Bundle Protocol Security (BPSec)*, 2022.
- IETF RFC 4838, *Delay-Tolerant Networking Architecture*, 2007.
- NASA, *Delay/Disruption Tolerant Networking*, current operational overview.

## 3. Opportunistic/DTN routing: baselines we must implement

PollicinoNet's synthetic strategies are useful engineering experiments, but they are not yet a scientifically sufficient routing baseline set. Classic DTN literature already defines several important strategies that correspond closely to questions we are asking.

### Epidemic Routing

Vahdat and Becker's Epidemic Routing spreads messages whenever nodes meet, subject to resources. This is the canonical high-redundancy baseline. Our `FloodAllStrategy` is related but should be tested for semantic equivalence before it is described as an Epidemic baseline.

### Spray and Wait

Spray-and-Wait limits the number of message replicas, seeking much of epidemic routing's robustness with substantially less resource use. This is particularly relevant to LoRa, where unrestricted replication is expensive.

### PRoPHET

PRoPHET uses encounter history and transitivity to estimate delivery predictability. This is directly relevant to a student network in which recurring human mobility patterns may exist without a centrally known schedule. PRoPHET is also documented in RFC 6693.

### MaxProp

MaxProp was evaluated on vehicle-based DTNs and combines estimated delivery likelihood with transmit/drop prioritization. Its buffer-management aspect is directly relevant to PollicinoNet's relay quotas and garbage collection.

### RAPID

RAPID is especially close to the direction PollicinoNet has taken. It formulates DTN routing as a resource-allocation problem and can optimize an explicit metric such as deadline delivery or delay rather than hoping that a generic forwarding rule indirectly improves it. Our priority scheduler and multi-dimensional benchmark should therefore include a RAPID-like baseline before inventing a sophisticated custom utility function.

### Bubble Rap and human mobility

Bubble Rap exploits social/community structure and centrality observed in human mobility. It is relevant to a student testbed because students may form recurring communities based on school, town, transport routes and daily routines. The privacy implication is equally important: such features can reveal sensitive social/location information, so any real experiment must avoid publishing identifiable traces.

Required benchmark work before novelty claims:

- canonical Epidemic baseline;
- Spray-and-Wait with configurable copy budget;
- PRoPHET encounter-history baseline;
- RAPID-like resource/deadline baseline;
- later MaxProp-like buffer/routing baseline;
- Bubble-Rap-like experiments only with synthetic or privacy-preserving mobility data initially.

Primary references:

- A. Vahdat, D. Becker, *Epidemic Routing for Partially-Connected Ad Hoc Networks*, Duke TR CS-2000-06.
- T. Spyropoulos, K. Psounis, C. Raghavendra, *Spray and Wait*, WDTN 2005.
- A. Lindgren, A. Doria, O. Schelén, *Probabilistic Routing in Intermittently Connected Networks*, 2003/2004; RFC 6693.
- J. Burgess et al., *MaxProp: Routing for Vehicle-Based Disruption-Tolerant Networks*, INFOCOM 2006.
- A. Balasubramanian, B. Levine, A. Venkataramani, *DTN Routing as a Resource Allocation Problem*, SIGCOMM 2007.
- P. Hui, J. Crowcroft, E. Yoneki, *Bubble Rap*, MobiHoc 2008 / IEEE TMC.

## 4. The ONE: a warning against rebuilding a simulator in isolation

The Opportunistic Networking Environment (The ONE) was created specifically to evaluate DTN routing and application protocols. It supports synthetic mobility models, real traces, multiple routing protocols and scenario-based repeatable experiments.

Our contact-window generator, scenario families and routing benchmark are useful because they are integrated tightly with PollicinoNet's exact content/custody/TRC semantics. They should not grow into an isolated general-purpose DTN simulator without comparison to The ONE.

Recommended action:

- define a minimal export/import format between PollicinoNet synthetic contact windows and The ONE contact/mobility traces;
- reproduce at least one standard ONE experiment with PollicinoNet baselines;
- where possible reuse established trace datasets rather than creating only favorable synthetic scenarios.

Reference:

- A. Keränen, J. Ott, T. Kärkkäinen, *The ONE Simulator for DTN Protocol Evaluation*, SIMUTools 2009.

## 5. Information-Centric / Named Data Networking

CCN/NDN changes the networking question from "which host has this address?" to "which named data do I want?". Named data can be cached in the network and validated as data rather than merely trusting a transport channel.

This overlaps with PollicinoNet's content-addressed store, manifests and ability to retrieve chunks from whichever peer has them. PollicinoNet differs today because it is explicitly disruption tolerant and push/store/carry/forward oriented, while NDN's dominant abstraction is Interest-driven retrieval over forwarding/cache state.

ChronoSync and later State Vector Sync are particularly relevant. They synchronize distributed dataset state and communicate names/state changes rather than blindly retransmitting entire datasets. These systems should be treated as related work for PNA1 and future reconciliation mechanisms.

References:

- V. Jacobson et al., *Networking Named Content*, CoNEXT 2009.
- L. Zhang et al., *Named Data Networking*, ACM CCR 2014.
- Z. Zhu, A. Afanasyev, *Let's ChronoSync: Decentralized Dataset State Synchronization in Named Data Networking*, ICNP 2013.
- P. Moll et al., *A Brief Introduction to State Vector Sync*, NDN Technical Report NDN-0073, 2021.

## 6. Set reconciliation: likely one of the highest-value next research directions

Current PNA1 is a bitmap-like statement of which chunks a target has. That is simple and exact, but its control overhead grows with the number of chunks even when sender and receiver differ by only a tiny fraction.

Set reconciliation asks exactly the Pollicino question: two peers each possess a large set; how can they discover the symmetric difference using communication proportional primarily to the difference rather than to the total set size?

Relevant families include BCH/PinSketch/minisketch, Invertible Bloom Lookup Tables (IBLTs), parity bitmap sketches and newer rateless reconciliation schemes. SIGCOMM 2024 work on Rateless IBLTs is especially interesting because it avoids needing a precise difference-size estimate before communication. Recent work continues to push rateless/adaptive reconciliation.

A direct biological-data connection also exists: WABI 2022 applied IBLTs to highly similar genomic k-mer datasets and obtained structures whose space can scale with the difference rather than total set size. This does not validate the separate DNA/DNATrace project automatically, but it is a striking demonstration that the same mathematical principle applies even to large, highly similar genomic data.

Recommended Pollicino experiment: `PNA2` as an optional reconciliation protocol, initially comparing PNA1 bitmap vs minisketch/IBLT/rateless IBLT over synthetic large manifests with controlled difference cardinality. Do not replace PNA1 before an exactness/overhead benchmark demonstrates a benefit.

References:

- *Practical Rateless Set Reconciliation*, ACM SIGCOMM 2024.
- Pieter Wuille et al., minisketch / BCH-based set reconciliation implementation and related work.
- Y. Shibuya, D. Belazzougui, G. Kucherov, *Efficient Reconciliation of Genomic Datasets of High Similarity*, WABI 2022.
- Recent rateless/adaptive set reconciliation literature should remain on the watch list.

## 7. SCHC: perhaps the closest standardized analogue to the Pollicino compression philosophy

RFC 8724 defines Static Context Header Compression and Fragmentation (SCHC) for LPWANs. Sender and receiver share static rules/context; when header values are already known at both ends, a compact RuleID can stand in for the full known structure. SCHC deliberately avoids expensive context-resynchronization traffic because LPWAN return paths may be restricted or unavailable.

This is a very important conceptual ancestor for Pollicino's "do not transmit what the receiver already knows" philosophy. SCHC applies the idea primarily to predictable protocol headers; Pollicino's research ambition extends it toward arbitrary content, versions, shared models and residual information.

SCHC should therefore influence the LoRa control plane before we invent a custom compression mechanism for every PNB1/PNC1/PCM1/PNA1 field. RFC 9011 profiles SCHC for LoRaWAN and RFC 9441 reduces ACK traffic with compound acknowledgements.

Recommended experiment: static-context encoding of PollicinoNet control objects, measured strictly as wire-byte savings and complexity, without changing the frozen HW-006 PHY until evidence justifies it.

References:

- IETF RFC 8724, *SCHC: Generic Framework for Static Context Header Compression and Fragmentation*, 2020.
- IETF RFC 9011, *SCHC over LoRaWAN*, 2021.
- IETF RFC 9441, *SCHC Compound Acknowledgement*, 2023.

## 8. LoRa-specific mesh systems: we must stop treating multi-hop LoRa as unexplored

### LoRaMesher

LoRaMesher is the most direct technical neighbour found so far. Its current 1.0 codebase implements a C++ LoRa mesh library with distance-vector routing, TDMA scheduling, automatic network formation, gateway/capability discovery, TTL broadcast de-duplication and host-side simulation; it supports RadioLib and SX1276-class hardware. The project cites a 2022 IEEE Access implementation paper and a 2026 Computer Communications paper on large and reliable data transfer for LoRa mesh applications.

Therefore PollicinoNet must not claim novelty for generic multi-hop LoRa, route discovery, reliable large transfer or TTL broadcast de-duplication. A concrete architectural experiment should compare:

- PollicinoNet directly over its current simple LoRa bearer;
- PollicinoNet as an application/DTN/content layer **above LoRaMesher**;
- a LoRaMesher-style continuously connected mesh against PollicinoNet store-carry-forward in disconnected/intermittent scenarios.

This may eventually let us delete custom lower-layer work rather than duplicate it.

### Meshtastic

Meshtastic is another practical baseline: a widely used LoRa mesh system oriented toward messaging/telemetry, with hop limits, duplicate suppression and constrained packet payloads. It is useful as a field baseline even if its goals differ from exact content reconciliation.

### FreakWAN

The repository already contains `freakwan-audit.md` and `freakwan-vs-pollicinonet.md`. This survey does not replace those audits; it places them in the larger DTN/mesh literature.

References:

- J. M. Solé et al., *Implementation of a LoRa Mesh Library*, IEEE Access 10 (2022), DOI 10.1109/ACCESS.2022.3217215.
- J. M. Solé et al., *Large and reliable data transfer service for LoRa mesh network applications*, Computer Communications 248 (2026), DOI 10.1016/j.comcom.2025.108404.
- LoRaMesher current upstream repository and protocol specification.
- Meshtastic documentation.

## 9. Reticulum, Haggle and Briar: heterogeneous networking is not a new category either

Reticulum is philosophically close to PollicinoNet. It is designed for constrained, heterogeneous networking, identifies destinations with compact hashes rather than conventional IP host/port pairs, supports radio/serial/IP interfaces and allows custom interfaces. It is an important benchmark for "one information layer over many bearers" and for security/identity overhead.

Haggle researched opportunistic, context-aware information dissemination across heterogeneous local and Internet links. Briar demonstrates an application-level system that synchronizes directly without central servers and can work offline using Bluetooth/Wi-Fi; it can also use removable media for encrypted offline transfer. Briar is especially useful for security, privacy and UX lessons. Its July 2026 maintenance-mode announcement also documents practical problems such as battery usage, unreliable background operation and difficult offline UX: protocol elegance is not enough for a deployable user system.

For PollicinoNet this means that "physical transport as a bearer" and "automatic multi-bearer synchronization" are plausible ideas but not unique ones. The research question should be how to minimize and verify the information moved under those constraints.

References:

- Reticulum Network Stack Manual, current release family.
- Haggle EU FP6 project publications on opportunistic networking.
- Briar documentation and 2026 maintenance-mode project status note.

## 10. Content addressing, fountain/erasure coding and adjacent work

IPFS and related content-addressed systems demonstrate that content hashes, block stores and Merkle-style structures are established techniques. PollicinoStore content addressing is useful engineering infrastructure but not, by itself, a research contribution.

Fountain/erasure codes (e.g. LT/Raptor families) and network coding are worth testing for contacts with expensive or unreliable acknowledgements. A relay could receive any sufficient subset of coded symbols rather than named missing chunks. This could reduce interaction at the cost of coding overhead, memory and more complex custody semantics. It should be benchmarked as an alternative, not assumed superior.

## 11. Revised novelty hypothesis

The survey suggests a narrower and stronger hypothesis for PollicinoNet.

**Established components:** store-carry-forward, bundles, TTL/hop count, opportunistic replication, route prediction, content-addressed blocks, multi-hop LoRa, LoRa fragmentation/reliable transfer, multi-interface networking, shared-context header compression and dataset synchronization all have substantial prior art.

**Potentially research-worthy combination:** a disruption-tolerant, bearer-neutral object transport whose primary optimization target is the minimum verifiable information required for a particular receiver to reconstruct an exact object, where receiver state, cached chunks, prior versions, shared static context and eventually shared learned models can all reduce the transmitted residual; decisions are evaluated with non-overlapping traffic accounting and explicitly separated synthetic vs physical evidence.

The strongest future differentiator may therefore come from the **reconstruction/reconciliation layer**, not from inventing another mesh routing protocol.

## 12. Literature-driven roadmap changes

Before adding more custom routing intelligence, the research roadmap should insert the following work:

1. Add canonical DTN baselines to the existing benchmark: Epidemic, Spray-and-Wait, PRoPHET and RAPID first.
2. Add a The ONE trace import/export bridge and reproduce at least one standard DTN scenario.
3. Write a BPv7 semantic/interop ADR: PNB1/BPv7 mapping, convergence-layer options and whether interoperability is desirable.
4. Start a `PNA2` set-reconciliation experiment using IBLT/minisketch/rateless techniques for large chunk sets.
5. Evaluate SCHC-inspired static-context compression for control traffic before inventing a new compact-control codec.
6. Build a LoRaMesher comparison/adapter experiment before expanding the custom LoRa mesh layer.
7. Add BPSec/Reticulum/Briar-derived security requirements before a distributed student field network carries anything sensitive.
8. Keep Netsukuku/QSPN as a scalability research track for compact decentralized route state, not as an immediate replacement for DTN routing.
9. Later test fountain/erasure coding against explicit missing-chunk synchronization on lossy/low-feedback links.

This pause therefore changes the preferred next step: **do not continue by inventing another PollicinoNet routing strategy. Implement literature baselines and interoperability/reconciliation experiments first.**

## 13. Implications for the future student LoRa network

The planned student network is scientifically valuable because it can become a rare bridge between simulation and real opportunistic/LoRa measurements. It should be positioned as a testbed rather than merely a messaging network.

Before deployment, the protocol work should establish authentication/encryption, pseudonymous node identity, privacy-preserving trace collection, data-retention policy and spectrum/regulatory constraints. Real home addresses or precise personal mobility traces must not be committed to the repository. Synthetic topology families should remain the development default until a consented field methodology exists.

Once HW-006 is resumed, measurements should be used to calibrate contact-capacity/loss models and then replay the *same* benchmark baselines with measured inputs. Only then can we say that a routing/reconciliation strategy performs better for the real Messina-area student testbed.

## 14. Reading order

Recommended reading sequence for the project team:

1. RFC 9171 + RFC 9172 (DTN/BPv7 and security).
2. Epidemic, Spray-and-Wait, PRoPHET, RAPID, MaxProp.
3. The ONE simulator paper/manual.
4. LoRaMesher 2022 paper + current protocol specification + 2026 large-transfer paper.
5. RFC 8724 SCHC (+ LoRaWAN profile/compound ACK).
6. ChronoSync/SVS and NDN synchronization.
7. Rateless IBLT/minisketch/set-reconciliation papers.
8. Netsukuku QSPN/topology papers.
9. Reticulum and Briar as engineering/security/UX comparators.

The survey should be updated as experiments produce new questions; related work is now part of the PollicinoNet research workflow, not a one-time bibliography exercise.
