# PN-002 — Deterministic scarce-link simulator

PN-002 keeps the standalone rule established by PN-001. It models an unreliable low-bandwidth link without importing DNA, LoRa SDKs, networking services or learned-model runtimes.

## Question

Can PollicinoNet fragment arbitrary bytes, survive deterministic packet/ACK loss with bounded retries, deduplicate repeated deliveries and reconstruct the exact source while accounting for every simulated wire byte?

## PNF1 framing

`FragmentFrame` uses a fixed 18-byte header:

- magic `PNF1`;
- 32-bit transfer ID;
- 16-bit sequence number;
- 16-bit total frame count;
- 16-bit payload length;
- CRC-32 of the payload.

`max_frame_bytes` is a generic whole-frame budget. It is deliberately not a LoRa constant.

## Link model

`ScarceLinkProfile` freezes explicit integer parameters:

- maximum frame bytes;
- nominal bitrate in bits/s;
- data-loss probability in integer parts-per-million;
- acknowledgement-loss probability in integer parts-per-million;
- retry budget;
- ACK byte cost;
- deterministic seed.

Loss decisions are derived deterministically from BLAKE2s over seed, channel, sequence and attempt. Re-running the same transfer under the same profile must produce the same report.

The first transport policy is stop-and-wait. If a data frame arrives but its ACK is lost, the sender retries; the receiver must tolerate the duplicate without changing reconstructed bytes.

## Accounting

PN-002 records:

- source bytes;
- frame count and payload capacity;
- data transmissions and retransmissions;
- duplicate deliveries;
- ACK transmissions;
- data wire bytes;
- ACK wire bytes;
- total wire bytes;
- nominal serialization time = `total_wire_bits / configured_bitrate`.

The serialization value is a generic bit-rate accounting proxy, **not a LoRa PHY airtime model**. Real LoRa airtime belongs to a later hardware/profile adapter.

## Frozen payloads

- `descriptor-bundle`: concatenation of three generic PN-001-style discovery descriptors, 164 bytes;
- `synthetic-512`: deterministic 512-byte arbitrary binary payload.

No DNA fixture is used in the primary experiment.

## Frozen profiles

1. `clean-64`: 64-byte whole-frame cap, 5000 bit/s, zero loss, 8-byte ACK;
2. `lossy-64`: same cap, 20% data loss, 10% ACK loss, seed 11, 12 retries;
3. `narrow-48`: 48-byte whole-frame cap, 2400 bit/s, 10% data loss, 5% ACK loss, seed 23, 12 retries.

These numbers are simulation parameters, not claims about any specific radio configuration.

## Scientific result

Successful GitHub Actions run `32184325879`, scientific head `8b07ebfe7226ab39e92e14c867ff7fc7546cdde8`:

- **103 root/scientific tests passed in 6.20 s**;
- all six payload/profile transfers reconstructed exactly;
- every repeated simulation reproduced an identical report;
- artifact `9341899126` (`pn-002-results`);
- artifact digest `sha256:68060ac82c2473651b267aeb2094297949d401ef84f3dad8cec2fc4bb7cd80be`.

| Payload | Profile | Frames | Retrans. | Duplicates | Total wire | Wire/source | Nominal serialization |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| descriptor 164 B | clean-64 | 4 | 0 | 0 | **268 B** | 1.634× | 0.4288 s |
| descriptor 164 B | lossy-64 | 4 | 7 | 4 | **748 B** | 4.561× | 1.1968 s |
| descriptor 164 B | narrow-48 | 6 | 2 | 0 | **384 B** | 2.341× | 1.2800 s |
| binary 512 B | clean-64 | 12 | 0 | 0 | **824 B** | 1.609× | 1.3184 s |
| binary 512 B | lossy-64 | 12 | 9 | 4 | **1432 B** | 2.797× | 2.2912 s |
| binary 512 B | narrow-48 | 18 | 6 | 1 | **1276 B** | 2.492× | 4.2533 s |

The result is intentionally not presented as an efficiency win: a small reliable-transfer protocol can spend substantially more bytes than the source because framing, acknowledgements and retries are real costs. That makes PN-002 useful for the PollicinoNet objective: future compression, discovery, caching and handover policies must be evaluated against **total reconstruction traffic**, not payload size in isolation.

The frozen `lossy-64` profile exercises both targeted paths: 7/9 retransmissions for the 164/512-byte payloads and 4 duplicate deliveries in each case because an already-delivered frame can be repeated after an acknowledgement is lost.

## Success criteria

PN-002 succeeds technically if:

1. the root/scientific test suite remains green;
2. all frozen transfers reconstruct byte-for-byte exactly;
3. every repeated simulation produces an identical report;
4. the clean profile requires zero retransmissions;
5. the frozen lossy profile exercises at least one retransmission and at least one duplicate delivery caused by ACK loss;
6. malformed/corrupted frames and exhausted retries fail closed;
7. the core retains zero DNA/radio-SDK runtime dependencies.

**All criteria passed.** No profile, seed, payload or threshold was modified after the scientific run.

## Conclusion and boundary

**PN-002 is a positive technical result for deterministic exact transfer over an impaired abstract link.** It gives PollicinoNet a reproducible place to measure retransmission and framing costs before introducing a specific physical transport.

PN-002 does not model duty cycle, spreading factor, coding rate, RSSI/SNR, regulatory rules, routing/mesh, FEC or real hardware. Those remain adapter-level work. DNA remains optional. A real LoRa adapter can later feed measured PHY/link behavior into the same generic accounting without changing the application-independent core.
