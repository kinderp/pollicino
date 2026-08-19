# PollicinoNet vs FreakWAN

FreakWAN and PollicinoNet overlap at the **bare-LoRa networking** layer, but
they optimize different problems.

| Area | FreakWAN | PollicinoNet | Relationship |
|---|---|---|---|
| Primary goal | resilient distributed chat / generic LoRa WAN | minimize scarce-link information needed to discover, retrieve or reconstruct content | different objective |
| Radio baseline | bare LoRa | bare LoRa in HW-001/HW-002 | common |
| LoRaWAN required | no | no | common |
| Current hardware | ESP32 LoRa boards incl. LILYGO T3 v2 1.6 | validated LILYGO T3 V1.6.1/SX1276 | strongly comparable |
| Implementation on device | mainly MicroPython + own radio drivers | C++/Arduino + RadioLib transparent/measurement adapter | different implementation |
| Distributed operation without Internet | yes | yes, `LORA_ONLY` mode | common goal |
| Flood/broadcast relay | implemented | candidate baseline, not yet adopted as default | FreakWAN reference |
| HELLO neighbor discovery | implemented | planned capability/privacy-aware discovery | idea reusable |
| Message UID / duplicate suppression | implemented | transfer IDs/content identities/duplicate suppression requirements | same problem, different identity model |
| TTL | implemented for network messages | expiry + hop-limit requirements | common primitive |
| ACK | first-hop ACK | policy-dependent hop/frame/end-to-end verification | PollicinoNet distinguishes more layers |
| Retries/backoff | configurable retransmissions + random delays | planned experiment dimension | useful baseline |
| Ping/pong | RTT + bidirectional signal strength | HW-002 firmware measurement PING/PONG | concept adopted, wire format independent |
| Duty/airtime tracking | rolling duty-cycle tracker | HW-002 time-on-air ledger/planner | concept adopted/generalized |
| Local storage | message history | content-addressed store, manifests, chunks, resumable transfer | related, PollicinoNet content-centric |
| Encryption | symmetric encrypted groups | application/transport security to be threat-model driven | do not copy construction blindly |
| Small media | FCI compressed images | EXACT/SEMANTIC branches + rich-link handover | different philosophy |
| Content addressing/cache reuse | not central | core research mechanism | PollicinoNet-specific |
| Coordinate → richer link | not central | central DISCOVERY pattern | PollicinoNet-specific |
| Wi-Fi | optional IRC/Telegram/backend features | rich data-plane/handover candidate | both use it, different purpose |
| BLE | serial/CLI access | local rendezvous/control/handover candidate | both use it, different purpose |
| LoRa-only mode | effectively yes | explicit `LORA_ONLY` transport mode | common |
| LoRa + Wi-Fi mode | possible app bridge | explicit preferred discovery→rich-data mode | PollicinoNet makes it architectural |
| LoRa + BLE mode | BLE CLI | explicit nearby handover/control mode | PollicinoNet makes it architectural |
| Automatic path selection | not primary objective | explicit `AUTO` policy | PollicinoNet-specific |
| LoRaWAN | not used | future optional gateway adapter only | common current non-use |
| Exact file reconstruction / SHA verification | not primary goal | core EXACT contract | PollicinoNet-specific |
| TRC accounting | no equivalent central metric | primary network research metric | PollicinoNet-specific |

## Short summary

FreakWAN asks mainly:

> How can a useful decentralized network carry messages robustly over bare LoRa?

PollicinoNet asks mainly:

> How can we avoid carrying unnecessary bytes over the scarce link at all?

Therefore FreakWAN is an excellent **routing/reliability/airtime baseline**, but
it should remain an external reference rather than becoming the PollicinoNet
core.
