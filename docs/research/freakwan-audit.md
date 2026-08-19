# FreakWAN audit — relevance for PollicinoNet

This note audits `antirez/freakwan` as an external reference implementation for bare-LoRa networking.

Frozen upstream reference used for this audit:

```text
repository: antirez/freakwan
branch: main
commit: 6b734768bb326449c9b3fabab55f9a261091340a
license: BSD-2-Clause
```

The goal is not to merge FreakWAN into PollicinoNet. The goal is to identify proven design ideas, useful baselines, and architectural differences.

---

## 1. What FreakWAN is

FreakWAN is a custom WAN built directly on **bare LoRa**, without LoRaWAN.

Its stated goals are:

1. distributed plaintext/encrypted chat when Internet/cellular infrastructure is unavailable;
2. a reusable robust LoRa protocol for applications such as sensors and home automation.

Its implementation is primarily MicroPython and targets ESP32 LoRa boards.

Important for PollicinoNet: FreakWAN explicitly supports the **LILYGO TTGO T3 v2 1.6** family and its device configuration uses the same SX1276 pin mapping we validated physically:

```text
MISO 19
MOSI 27
SCK  5
CS   18
RST  23
DIO0 26
LED  25
OLED SDA/SCL 21/22
```

This makes FreakWAN unusually relevant to HW-001/HW-002 because it is not only conceptually similar: it runs on essentially the same hardware family.

---

## 2. FreakWAN architecture in one picture

```text
Application
  chat / sensors / small media / IRC / Telegram
                |
                v
FreakWAN protocol
  message IDs
  TTL
  broadcast relay
  ACK
  HELLO
  retry/random delay
  encrypted groups
  local history
                |
                v
custom SX1276/SX1262 drivers
                |
                v
bare LoRa PHY
```

FreakWAN therefore owns much more of the networking stack than HW-001 currently does.

HW-001 is intentionally narrower:

```text
PollicinoNet host protocol
        |
        v
transparent serial/radio bridge
        |
        v
RadioLib
        |
        v
SX1276 / LoRa
```

---

## 3. Features worth studying

### 3.1 Broadcast/flood routing

FreakWAN implements a distributed network based on broadcast routing. Messages can be relayed by nodes rather than requiring a central gateway.

Why this matters to PollicinoNet:

- useful baseline for disruption-tolerant multi-hop communication;
- useful comparison against our future sparse gossip / content-aware routing;
- demonstrates how a network can operate without Internet, cellular or LoRaWAN infrastructure.

What not to assume:

Flooding is simple and robust, but can become expensive in airtime when node density grows. PollicinoNet should benchmark it as a baseline rather than adopt it automatically.

---

### 3.2 Message IDs and duplicate handling

FreakWAN messages have a generated 32-bit UID and a sender identity. The message format includes flags and TTL.

Relevant ideas:

- compact wire identity;
- duplicate suppression;
- relay-safe message semantics;
- finite propagation using TTL.

PollicinoNet already has transfer IDs, content hashes and scoped coordinates, so we should not copy the exact format. We should compare the **cost and behavior** of both approaches.

---

### 3.3 TTL

FreakWAN DATA messages carry a TTL.

This maps directly to a PollicinoNet delay/disruption-tolerant requirement:

```text
message / descriptor
  + TTL
  + hop policy
  + duplicate suppression
```

PND1 already has a lifetime concept; HW/network experiments should distinguish:

- time-based expiry;
- hop count;
- retry budget.

---

### 3.4 HELLO neighbor discovery

FreakWAN advertises nearby nodes with HELLO messages and can list sensed nodes.

This is highly relevant for a future PollicinoNet local discovery layer.

Potential experiment:

```text
PN-HW HELLO
  node ephemeral ID
  capabilities
  cache summary hint
  supported rich links
  time/TTL
```

But PollicinoNet should preserve its privacy model: stable hardware IDs should not be exposed by default.

---

### 3.5 Ping/pong and RTT + bidirectional RSSI

FreakWAN implements direct `PING` / `PONG`; the current README describes reporting round-trip time and signal strength in both directions.

This is immediately useful for HW-002.

Our HW-001 loopback already records RSSI/SNR per received frame but does not yet implement a single protocol transaction that measures:

```text
A sends ping
B receives + records RSSI
B returns pong containing observed RSSI
A receives + records RSSI
A computes RTT
```

Recommendation: add a **PollicinoNet measurement ping**, not by copying FreakWAN's packet format, but by adopting the experiment concept.

---

### 3.6 Randomized retransmission delays

FreakWAN supports configurable retransmissions with random delays.

This is important in a shared broadcast medium because deterministic simultaneous retries can collide again.

For PollicinoNet this should become an experimental policy dimension:

```text
fixed retry
vs
random backoff
vs
FEC
vs
selective ACK
```

TRC must include all retransmitted radio bytes and airtime.

---

### 3.7 First-hop ACK

FreakWAN supports first-hop acknowledgements.

This is a useful baseline, but PollicinoNet should distinguish:

- radio-hop receipt;
- frame receipt;
- complete transfer reconstruction;
- final cryptographic object verification.

A hop ACK is not the same as end-to-end success.

---

### 3.8 Duty-cycle tracking

FreakWAN has a small `DutyCycle` class that tracks TX-active time over rotating time slots. Its default design uses four 15-minute slots and computes percentage of TX time over valid slots.

This is particularly useful for PollicinoNet HW-002/HW-003 because we need a **measured airtime accounting primitive**, not just packet counts.

Recommendation:

Implement a transport-neutral airtime ledger in PollicinoNet hardware tooling with fields such as:

```text
started_at
ended_at
airtime_ms
payload_bytes
wire_bytes
retry_index
transfer_id
radio_profile
```

Then compute rolling TX occupancy/duty metrics outside the core protocol.

Do not copy regulatory thresholds into the core: legal limits depend on region/sub-band/current rules.

---

### 3.9 Local message storage

FreakWAN stores message history locally and removes old entries.

This maps well to PollicinoNet's planned:

- store-and-forward;
- disconnected operation;
- resumable transfer;
- local chunk cache.

PollicinoNet can go further because its store should be content-addressed and understand manifests/chunks rather than only application messages.

---

### 3.10 Small image transport

FreakWAN includes FCI, a tiny lossless 1-bit image representation with run-length compression, used as a proof of concept for small media over LoRa.

This is extremely useful as a **baseline experiment** for Pollicino:

```text
FCI/RLE baseline
vs
PNG-derived tiny format
vs
zlib/zstd
vs
Pollicino predictive codec
vs
semantic reconstruction
```

The point is not to replace Pollicino's compression research with FCI. The point is to have a simple, understandable baseline designed specifically for scarce LoRa packets.

---

### 3.11 BLE and USB control plane

FreakWAN exposes CLI interaction through USB serial and Bluetooth LE.

That supports an architectural idea already present in PollicinoNet:

```text
LoRa = scarce / long-range link
BLE  = nearby control/config link
Wi-Fi = rich local data link
Internet = rich remote data link
```

A future hardware adapter can advertise which richer links are available and negotiate handover.

---

### 3.12 Custom SX1276 driver

FreakWAN contains a compact MicroPython SX1276 driver under BSD-2-Clause.

Interesting aspects:

- direct register-level control;
- frequency, BW, CR, SF and TX power configuration;
- explicit DIO0 RxDone/TxDone mapping;
- RSSI/SNR extraction;
- CRC error handling;
- frequency-error reading;
- very small dependency footprint.

This is valuable for education because students can see what RadioLib hides.

Recommendation:

Keep **RadioLib C++ as the main PollicinoNet hardware benchmark adapter** for now, because HW-001 is already validated and reproducible.

Add a later educational track:

```text
HW-LOWLEVEL-001
RadioLib abstraction
vs
register-level SX1276 implementation
```

FreakWAN's driver is an excellent reference for that lab.

---

## 4. Encryption: study, do not copy blindly

FreakWAN supports encrypted virtual groups. Its current keychain implementation derives separate encryption/MAC keys, uses AES-CBC for encryption and a truncated HMAC-SHA256 for integrity.

This is valuable to study because it demonstrates an important networking property: a node may relay ciphertext without being able to decrypt the application payload.

That idea is relevant to PollicinoNet multi-hop privacy.

However, for a new PollicinoNet security design we should not adopt an existing custom packet crypto construction merely because it works in another project.

Recommendation:

- treat FreakWAN security as a comparative/reference design;
- define PollicinoNet threat model first;
- use a standard, reviewed AEAD construction/library where available;
- separate identity, authentication, confidentiality, replay protection and relay metadata explicitly.

---

## 5. FreakWAN vs PollicinoNet

| Dimension | FreakWAN | PollicinoNet |
|---|---|---|
| Primary goal | resilient LoRa WAN/chat | minimize transmission/reconstruction cost |
| PHY | bare LoRa | transport-neutral; LoRa is one adapter |
| Hardware | ESP32 LoRa boards | currently LILYGO HW-001, extensible |
| Routing | broadcast/flood relay | not frozen; sparse/content-aware candidates |
| Discovery | HELLO nodes | object/service/capability discovery |
| Object identity | message UID/sender | coordinate + full manifest/hash/content IDs |
| Exact files | not primary abstraction | primary EXACT channel |
| Content cache | message/history oriented | content-addressed chunks/manifests |
| Rich-link handover | Wi-Fi/Telegram/IRC integrations | explicit DISCOVERY → rich retrieval architecture |
| Semantic channel | no | planned |
| Duty tracking | yes | planned physical TRC/airtime ledger |
| Compression research | small FCI images | central research axis |
| ML/learned codec | no | central Pollicino axis |
| DNA integration | no | optional adapter |

The projects overlap most strongly in the **scarce-link networking layer**, but diverge strongly in the object/reconstruction layer.

---

## 6. What we should reuse conceptually

Priority A — useful almost immediately:

1. ping/pong measurement with RTT + bidirectional RSSI;
2. duty/airtime rolling ledger;
3. randomized retry/backoff baseline;
4. HELLO/capability discovery baseline;
5. duplicate suppression + TTL/hop experiments;
6. store-and-forward reference behavior.

Priority B — useful for teaching/research comparison:

7. MicroPython SX1276 register-level driver;
8. FCI tiny-image baseline;
9. BLE serial/config channel;
10. flooding vs sparse gossip benchmark.

Priority C — study but redesign:

11. security/encrypted relay model;
12. message identity/addressing;
13. application-specific chat/media packet formats.

---

## 7. What we should not do

Do **not** turn PollicinoNet into a fork of FreakWAN.

Do not make `pollicino.net` depend on:

- MicroPython;
- FreakWAN packet classes;
- a specific LoRa driver;
- chat semantics;
- stable device IDs;
- flooding as mandatory routing.

The dependency direction should remain:

```text
PollicinoNet core
   ^
   |
optional hardware/network experiments
   |
LoRa / FreakWAN-inspired adapters or baselines
```

not:

```text
PollicinoNet core -> FreakWAN
```

---

## 8. Proposed experiment sequence after HW-001

### HW-002 — link characterization

- packet sizes;
- packet loss;
- RSSI/SNR distributions;
- RTT;
- measured/estimated airtime;
- bidirectional asymmetry;
- fixed PHY first.

### HW-003 — reliability policies

Compare:

```text
no retry
fixed retry
randomized retry
ACK
selective ACK
FEC
```

Use FreakWAN behavior as one reference baseline.

### HW-004 — discovery/relay

Start with 3+ nodes when hardware is available:

```text
HELLO
TTL
UID/duplicate suppression
single relay
flood baseline
sparse gossip candidate
```

### HW-005 — store-and-forward / content cache

Move from messages to Pollicino objects/chunks.

### HW-006 — rich-link handover

```text
LoRa descriptor
→ BLE/Wi-Fi/Internet rendezvous
→ exact retrieval
```

---

## 9. Strongest conclusion

FreakWAN is **very useful to PollicinoNet**, but mainly as:

- a mature bare-LoRa reference implementation;
- a protocol-design baseline;
- an educational low-level SX1276 implementation;
- a source of experiments to reproduce scientifically.

The fact that it supports the same LILYGO T3 v2 1.6 / SX1276 pinout makes it unusually valuable: many comparisons can be run on the exact hardware already used for HW-001.

PollicinoNet should preserve its distinctive research question:

> transmit the minimum information necessary to locate, derive or reconstruct the intended object, and measure the complete cost of doing so.

FreakWAN helps us build and benchmark the **network below that idea**; it should not replace the idea itself.

---

## 10. Upstream files inspected

Audit based on upstream commit `6b734768bb326449c9b3fabab55f9a261091340a`, including:

- `README.md`;
- `devices/device_config.t3_v2_1_6.py`;
- `sx1276.py`;
- `message.py`;
- `dutycycle.py`;
- `keychain.py`;
- repository metadata/license.
