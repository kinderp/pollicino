# UC-190 — Heterogeneous Mesh Application Gateway / Interoperability Courier

## The concrete problem
A school owns PollicinoNet boards, while a nearby workshop experiments with LoRaMesher or a different LoRa/IP mesh. Radio packets, routing and addressing are not automatically interoperable. Reflashing every device or altering Pollicino's **frozen LoRa PHY** is not acceptable. Can a gateway carry one *authorized application object* between these otherwise separate islands without claiming their radios speak the same protocol?

## Actors and scenario
Two intentionally separate test islands, one PollicinoNet and one third-party stack (initially simulated); an approved gateway with one interface/client per stack; two school checkpoints, optional Wi-Fi host, relays carried by consenting students. In a Messina–Villafranca–Rometta/Venetico testbed, the gateway may be a Raspberry Pi at a school laboratory, not an invisible radio repeater.

## Why PollicinoNet
Exchange an *application-level envelope*: content hash, source trust domain, intended destination, creation/lifetime, priority, purpose, explicit gateway policy, hop provenance, deduplication ID and verified receipt. Translate only meanings common to both applications. If the foreign stack cannot represent a required property (expiry, authorization, integrity or privacy), **reject/quarantine**, do not silently downgrade it. Loop suppression must survive gateway reboot; bound retention, hops and replication.

## Bearers
- **LoRa:** each island uses its **own existing stack and radios**; no new Pollicino PHY/MAC or assumed over-the-air compatibility.
- **BLE / Wi-Fi / LAN:** permitted gateway-to-gateway control, logs and actual objects after local handoff.
- **Internet:** optional lab backhaul; no permanent connectivity assumption.
- **Physical carry:** managed encrypted SSD/SD with manifest when neither radio island can deliver a bulk object.

## Test now, without hardware
Run two independent mocked protocol adapters and a small persistent gateway service. Pass a signed synthetic school notice and a 50-kB public dataset object across both directions. Inject message loops, duplicate foreign IDs, missing expiry, unsynchronized clocks, trust downgrade, mismatched hash, failed gateway storage, a gateway restart and no network contact. Compare accept/reject/quarantine decisions against an explicit policy table. Do not claim LoRaMesher/BPv7 binary compatibility: an adapter is an experiment until demonstrated.

## Necessary physical test
After a software contract review, use 4–8 LoRa boards split between the two test islands and a Raspberry Pi or laptop acting as **dual-stack application proxy**; where needed use physically separate radios. Restrict first test to a school lab. Measure exact receive/forward/verify receipts, forwarded bytes, loops, bridge restart recovery, lost authorization fields and contact availability. Respect regional radio constraints; no automatic uncontrolled rebroadcast.

## Privacy, safety, difficulty
**High.** No relay of personal data across trust domains by default. Sign/authenticate original object and bridge decisions, forbid untrusted foreign commands, preserve provenance, keep ID mapping local, rotate experiment IDs and keep bounded logs. This is a controlled interoperability prototype, not proof of certification.

## Difference from existing cases
UC-033 negotiates rich-bearer handoff; UC-124 chooses transports; UC-135 handles data-schema migration; UC-068 enrolls native devices. **UC-190 explicitly crosses different network protocol/trust domains using an application proxy while preserving Pollicino's existing PHY.**

## Evidence and references
- DTN gateways and application proxies: https://www.rfc-editor.org/rfc/rfc4838
- Candidate third-party protocol to inspect, not assume compatible: https://github.com/LoRaMesher/LoRaMesher
- Bundle Protocol as comparison reference, **not a compatibility claim**: https://www.rfc-editor.org/rfc/rfc9171
