# PollicinoNet related-work matrix

Status: 2026-08-25 literature checkpoint

This matrix is a compact companion to `pollicinonet-related-work-literature-survey.md`. It is meant to drive experiments and prevent accidental novelty claims for already established ideas.

| Project / research line | What it already solves | Overlap with PollicinoNet | What PollicinoNet should learn/test | Do not claim as novel |
| --- | --- | --- | --- | --- |
| Netsukuku / QSPN | Decentralized mesh routing, compact/fractal route state, low-resource distributed network | Future large-scale route-state problem | Study hierarchical route summaries if the real testbed scales; compare QSPN ideas only when contemporaneous mesh routing becomes a blocker | Decentralized mesh routing; compact hierarchical routing as a general idea |
| DTN / BPv7 (RFC 9171) | Store-carry-forward bundles over intermittent heterogeneous networks | Very high: persistent relay, TTL/lifetime, hop policy, heterogeneous bearers | Write BPv7 semantic/interop ADR; decide whether PNB1 is experimental profile, gateway protocol or independent layer | Bundles, store-carry-forward, intermittent end-to-end delivery |
| BPSec (RFC 9172) | Bundle integrity/confidentiality | Current PollicinoNet security gap | Define authentication, encryption, replay and metadata privacy before field deployment | Checksums as security |
| Epidemic Routing | High-redundancy opportunistic replication | Similar to FloodAll | Implement canonical semantics as benchmark baseline | Flooding in intermittent networks |
| Spray-and-Wait | Bounded-copy opportunistic routing | Natural fit for scarce LoRa | Add copy-budget baseline; compare delivery/traffic | Limited replication idea |
| PRoPHET / RFC 6693 | Encounter-history + transitive delivery prediction | Similar future goal to learned/observed relay suitability | Add encounter-history baseline before custom prediction | Using past encounters to select relays |
| MaxProp | Delivery-likelihood prioritization plus buffer/drop management | Routing + relay GC/scheduling overlap | Add later baseline combining forwarding and buffer pressure | Buffer-aware DTN prioritization |
| RAPID | Routing as explicit resource-allocation optimization | Very close to priority/scheduler/benchmark direction | Implement RAPID-like utility baseline for deadlines/delay | Utility-based DTN resource allocation |
| Bubble Rap | Social/community-aware forwarding | Student/human mobility could have community structure | Test only with synthetic/privacy-preserving mobility initially | Social centrality for opportunistic routing |
| The ONE | DTN simulator, mobility models, traces, protocol comparison | Strong overlap with scenario families/benchmark | Add trace import/export; reproduce published baseline scenarios | General DTN scenario simulator concept |
| CCN / NDN | Named/content-centric networking, caches, data-oriented security | Content-addressed object/chunk view | Clarify push/store-carry vs Interest/pull difference; study cache/security semantics | Content-centric forwarding/caching |
| ChronoSync / SVS | Distributed dataset-state synchronization | Strong overlap with PNA1/state exchange | Compare sync-state overhead and semantics | Dataset synchronization based on compact state |
| IBLT / minisketch / rateless set reconciliation | Communicate set differences with cost tied to difference size | Extremely close to "send only what receiver lacks" | Build PNA2 experiment; compare bitmap vs sketches across manifest sizes/difference ratios | Set reconciliation / symmetric-difference sketches |
| SCHC (RFC 8724) | Shared static context replaces known headers with compact RuleID; LPWAN fragmentation | Deep conceptual overlap with Pollicino compression philosophy | Test SCHC-inspired compact control plane; quantify savings/complexity | Shared-context LPWAN header compression |
| LoRaMesher | LoRa mesh routing, TDMA, discovery, gateway capability, TTL flooding, simulation, current large reliable transfer work | Closest physical LoRa neighbour | Benchmark and/or use as bearer; compare connected mesh vs disruption-tolerant overlay | Generic multi-hop LoRa, route discovery, reliable large transfer |
| Meshtastic | Practical LoRa mesh messaging/telemetry with constrained packets, hop limits and duplicate suppression | Real-world field baseline | Use as practical comparison for flooding/overhead/usability | LoRa messaging mesh |
| FreakWAN | LoRa mesh/off-grid communication | Already separately audited in this repo | Keep existing audit; use in practical comparison set | Off-grid LoRa mesh idea |
| Reticulum | Heterogeneous post-IP networking, compact hashed destinations, radio/serial/IP interfaces, encryption | Philosophically close to bearer-neutral networking | Measure wire/identity overhead; evaluate adapter or interoperability experiment | Multi-interface post-IP network stack |
| Haggle / SCAMPI | Opportunistic context-aware multi-interface dissemination | Multi-bearer/opportunistic overlap | Study context/routing policy architecture | Opportunistic heterogeneous networking |
| Briar | Direct/offline synchronization over Bluetooth/Wi-Fi/removable media with security focus | Application/use-case analogue | Learn security/privacy/UX/battery lessons | Offline multi-bearer sync/data mule by itself |
| KioskNet / DakNet | Vehicle/bus data-mule mechanical backhaul | Direct use-case analogue | Use as reference for data-mule scenario families | Physical mobility carrying data |
| IPFS | Content-addressed blocks/Merkle-DAG storage | PollicinoStore/content-addressing overlap | Keep content addressing as infrastructure, not novelty claim | Content-addressed block storage |
| Fountain / erasure coding | Recover data from arbitrary sufficient encoded symbols | Alternative to exact missing-chunk requests | Benchmark under low-feedback/lossy contacts | Rateless erasure coding itself |

## Priority of follow-up experiments

The literature changes the immediate research priority to:

| Priority | Experiment | Why now |
| --- | --- | --- |
| P0 | Epidemic + Spray-and-Wait + PRoPHET + RAPID baselines | Required to judge our routing work scientifically |
| P0 | BPv7 semantic/interop ADR | Prevents unnecessary reinvention of bundle/convergence semantics |
| P0 | PNA2 set-reconciliation prototype | Closest literature match to Pollicino's minimum-information objective |
| P1 | The ONE trace import/export | Makes benchmark results comparable with established DTN research |
| P1 | LoRaMesher adapter/comparison | Avoids rebuilding solved physical mesh components |
| P1 | BPSec-inspired security requirements | Required before a real distributed student network |
| P2 | SCHC-inspired control compression | Strong LPWAN idea, but should follow baseline correctness work |
| P2 | Fountain/erasure coding experiment | Useful alternative under scarce feedback |
| P3 | Netsukuku/QSPN compact-routing prototype | Valuable only when route-state scale becomes a demonstrated problem |

## Working positioning statement

A defensible current positioning is:

> PollicinoNet is an experimental disruption-tolerant, bearer-neutral exact-object transport and reconciliation layer. It studies how little verifiable information must cross scarce/intermittent links when receivers may already possess chunks, versions, context or eventually shared learned models. Its research testbed explicitly separates modeled behavior from physical evidence and is designed to compare established DTN, reconciliation and LoRa-networking baselines rather than replace them by assumption.

This statement is intentionally narrower than saying that PollicinoNet invents a new mesh network. It is also a stronger research position because it points directly to measurable questions.
