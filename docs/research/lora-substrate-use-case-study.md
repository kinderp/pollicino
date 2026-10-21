# LoRa substrate choices — use-case-gated study

Status: literature/architecture checkpoint, 2026-08-25

This study asks whether PollicinoNet should continue to own raw-LoRa network mechanics, sit above LoRaMesher, integrate Reticulum, or keep several experimental backends.

The answer is intentionally use-case dependent.

## Executive decision

Do **not** replace the current PollicinoNet bearer layer yet.

Use three roles instead:

1. **raw LoRa** — minimal physical evidence and direct/disruption-tolerant baseline;
2. **LoRaMesher** — prototype as a connected multi-hop LoRa segment below PollicinoNet;
3. **Reticulum** — research/overhead baseline for a mature heterogeneous secure network substrate, not an architectural dependency yet.

Meshtastic/FreakWAN remain practical external field baselines rather than immediate core dependencies.

## 1. Raw LoRa

### Concrete use cases

- two nodes communicate directly;
- there is no contemporaneous multi-hop path and store-carry-forward is required;
- we need clean RF experiments with minimal hidden protocol behavior;
- we need exact evidence tying a Pollicino frame attempt to radio conditions.

### Advantages

- smallest conceptual stack;
- easiest physical attribution of bytes/retries/airtime;
- no routing-control traffic unless Pollicino explicitly adds it;
- current HW-001..HW-006 work already exists here.

### Costs

- Pollicino must not gradually reinvent a complete connected-mesh MAC/routing protocol by accident;
- collision avoidance, route discovery, network joining and multi-hop connected forwarding become substantial projects.

### Gate

**Decision: KEEP as evidence/reference bearer.**

Raw LoRa is justified independently by physical measurement and disruption-tolerant direct-contact use cases.

## 2. LoRaMesher

Current LoRaMesher is an active C++20/ESP32 project using RadioLib and FreeRTOS. Its current protocol is a distance-vector mesh coordinated by TDMA, with discovery/joining, route maintenance, a network-manager role, capability/gateway discovery, TTL flooding and desktop simulation.

Its current documentation lists RadioLib support for SX1276-class radios and a full host-side simulation/test environment. The 2026 project also cites published work on reliable large data transfer over LoRa mesh.

### Relevant wire/architecture facts

Current protocol specification documents a point-to-point DATA structure with a 10-byte LoRaMesher header before user payload:

- 6-byte base header;
- 4-byte data extension containing next hop, TTL and sequence number.

It also maintains routing-table information, synchronization/TDMA state, joining/discovery messages and network-manager coordination.

This is not "free routing": it exchanges control state and introduces timing/network-formation behavior. Those bytes and delays must be included in any fair comparison with raw PollicinoNet.

### Concrete use case that passes the gate

> A set of student nodes are simultaneously connected through a multi-hop LoRa cluster. PollicinoNet wants exact object/reconciliation/DTN semantics but should not implement another full distance-vector + TDMA mesh solely to cross that connected cluster.

Possible composition:

`Pollicino object/reconciliation/DTN -> LoRaMesher connected segment -> LoRa radio`

When the connected path disappears, Pollicino's persistent store-carry-forward remains above it.

### Questions the adapter prototype must answer

1. Can PNB1/PCM1/PNA/data traffic be transported without fighting LoRaMesher fragmentation/reliable-transfer semantics?
2. What is the real control-plane + data-header cost per delivered Pollicino byte?
3. Does TDMA/network formation help or hurt short opportunistic contacts?
4. How quickly can a node join/recover relative to the contact windows we care about?
5. Can the underlying routing state be hidden cleanly behind the existing bearer API?
6. Does LoRaMesher support the exact current LILYGO T3 V1.6.1 board configuration directly, or only the SX1276 radio family requiring custom pins/board integration?
7. Does its network-manager/TDMA architecture fit intermittent student clusters, or assume a longer-lived connected mesh than our use cases provide?

### Minimal experiment before hardware

Use LoRaMesher's desktop/native simulation or a thin adapter mock.

Compare identical Pollicino object transfers over:

- raw synthetic direct/multi-contact Pollicino;
- LoRaMesher connected segment;
- optional direct LoRaMesher large/reliable transfer baseline.

Metrics:

- Pollicino payload delivered;
- LoRaMesher data/control bytes;
- modeled airtime;
- route/discovery convergence delay;
- number of relays/hops;
- CPU/RAM if available;
- adapter complexity;
- behavior when topology breaks mid-transfer.

### Kill criterion

Do not adopt LoRaMesher as a bearer if:

- connected-cluster use cases are rare;
- joining/TDMA convergence is too slow for target contacts;
- overhead erases the routing benefit;
- integration couples Pollicino object semantics to LoRaMesher internals;
- hardware integration is materially harder than the value gained.

### Gate

**Decision: PROTOTYPE/COMPARE.**

No physical superiority claim until later HW campaign.

## 3. Reticulum

Reticulum is a mature heterogeneous network stack supporting many interface types, including RNode LoRa, Wi-Fi/Ethernet/IP/serial/custom paths. It provides network identity, announces/path discovery, links and secure communication semantics.

This is highly relevant because PollicinoNet should not claim that multi-interface/post-IP networking itself is novel.

Current Reticulum documentation gives example complete on-wire sizes such as:

- Path Request: 51 bytes;
- Announce: 167 bytes;
- Link Request: 83 bytes;
- Link Proof: 115 bytes;
- Link RTT packet: 99 bytes;
- Link keepalive: 20 bytes.

These are useful overhead baselines for our "small control plane" objective.

Current hardware documentation includes several LilyGO/RNode device families and SX1276-class radios, but exact compatibility with Pollicino's LILYGO T3 V1.6.1 revision must be verified rather than inferred from transceiver family alone.

### Candidate use cases

A. Use a mature secure identity/path layer instead of custom discovery/security across LoRa + Wi-Fi + Internet.

B. Interoperate with an existing Reticulum/RNode ecosystem.

C. Compare Pollicino's compact object-control plane against a mature post-IP network substrate.

### Architecture gate

Adopting Reticulum would be a major cross-cutting dependency, not a local feature. The project rule requires at least two concrete independent use cases or a strong external constraint.

Today:

- C is a valid research use case;
- A is a broad architectural motivation, not yet proven to reduce total complexity;
- B is not currently required by an external deployment.

### Gate

**Decision: RESEARCH ONLY / OVERHEAD BENCHMARK.**

Do not replace Pollicino's bearer layer yet.

## 4. Meshtastic and FreakWAN

These remain valuable practical baselines for off-grid LoRa messaging, flooding, duplicate suppression, TTL/hops, usability and real deployment behavior.

FreakWAN already has a separate detailed audit in this repository.

### Gate

**Decision: EXTERNAL FIELD/UX BASELINES, not immediate runtime dependencies.**

Use them when the concrete use case is messaging/telemetry usability or field reliability rather than exact object reconciliation.

## 5. DSME-LoRa and other MAC/network alternatives

Research such as DSME-LoRa demonstrates that LoRa can be paired with scheduled peer-to-peer MAC mechanisms beyond LoRaWAN.

This is relevant prior art but currently does not pass a distinct Pollicino implementation gate: LoRaMesher already gives us a concrete TDMA/mesh candidate for the connected-segment use case.

### Gate

**Decision: RESEARCH SHELF.**

Reopen only if LoRaMesher fails for a reason a standards-based MAC specifically addresses.

## 6. Decision matrix

| Substrate | Justified use case now? | Current decision |
| --- | --- | --- |
| raw LoRa | direct RF evidence + disconnected contacts | KEEP |
| LoRaMesher | contemporaneously connected multi-hop LoRa cluster | PROTOTYPE/COMPARE |
| Reticulum | multi-interface secure substrate | RESEARCH/OVERHEAD BENCHMARK |
| Meshtastic | practical off-grid messaging baseline | EXTERNAL BASELINE |
| FreakWAN | practical bare-LoRa networking baseline | EXTERNAL BASELINE |
| DSME-LoRa | alternative scheduled peer-to-peer MAC | RESEARCH SHELF |

## 7. Architectural boundary to preserve

PollicinoNet should try to keep this boundary explicit:

`object identity / receiver knowledge / exact reconstruction / DTN policy / evidence accounting`

above

`connected-bearer routing / MAC / RF transport`.

That allows raw LoRa, LoRaMesher or a future external network stack to compete underneath without forcing the object/reconciliation research to be rewritten.

If this boundary proves impossible for two genuinely different bearer implementations, that itself becomes evidence for an architectural redesign.

## 8. Next experiment justified by this study

No production integration yet.

The smallest useful experiment is a **host-side LoRaMesher bearer adapter benchmark** using a concrete use case:

> an exact Pollicino object crosses a temporarily connected three-hop LoRa cluster, while a later topology break is handled by Pollicino store-carry-forward rather than by pretending the mesh remains connected.

This should be done only after the canonical DTN baselines/PNA2 study have a minimal benchmark scaffold, because those are more central to the current research question.

## References

- LoRaMesher project, current protocol specification v1.6 (2026-03-12).
- J. M. Solé et al., *Implementation of a LoRa Mesh Library*, IEEE Access 10, 2022, DOI 10.1109/ACCESS.2022.3217215.
- J. M. Solé et al., *Large and reliable data transfer service for LoRa mesh network applications*, Computer Communications 248, 2026, DOI 10.1016/j.comcom.2025.108404.
- J. Miquel, F. Freitag, R. Baig, *LoRaMesher: An open-source library for multi-hop LoRa mesh networks*, SoftwareX 34, 2026, DOI 10.1016/j.softx.2026.102570.
- Reticulum Network Stack manual, current interface/hardware/understanding documentation.
- J. Álamos et al., *DSME-LoRa: Seamless Long Range Communication Between Arbitrary Nodes in the Constrained IoT*, 2022.
