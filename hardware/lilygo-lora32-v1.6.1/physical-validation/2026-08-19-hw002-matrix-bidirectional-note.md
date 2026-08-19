# HW-002 bidirectional payload-size matrix — same-bench checkpoint

Frozen PHY: `868.100 MHz`, `BW125`, `SF7`, `CR4/5`, `10 dBm`.

Two mirrored runs were executed without intentionally changing the test scenario:

- COM3 initiator -> COM4 autonomous responder: 18/18 observed successes;
- COM4 initiator -> COM3 autonomous responder: 17/18 observed successes.

Combined same-bench matrix: **35/36 successful transactions** across 16, 32, 42, 60, 120 and 240 byte H2 measurement frames.

## Mean RTT of successful transactions

| Frame | Combined attempts | Successful | Mean RTT |
|---:|---:|---:|---:|
| 16 B | 6 | 6 | 109.195 ms |
| 32 B | 6 | 6 | 150.666 ms |
| 42 B | 6 | 5 | 181.534 ms |
| 60 B | 6 | 6 | 233.403 ms |
| 120 B | 6 | 6 | 408.419 ms |
| 240 B | 6 | 6 | 769.511 ms |

RTT remains dominated by the nominal two-frame LoRa time-on-air. The mirrored means differ only by sub-millisecond amounts at every size; this is descriptive same-bench evidence, not a general latency model.

## First observed physical error

COM4-initiator sequence 8, frame size 42 B, returned:

```text
error=rx state=-7
```

RadioLib 7.6.0 defines `-7` as `RADIOLIB_ERR_CRC_MISMATCH`: the CRC calculated from a received LoRa packet did not match the expected CRC. This is therefore the first HW-002 observation of a CRC-invalid received frame, not a receive timeout.

The evidence supports only this narrow statement: a CRC-invalid LoRa frame was detected during the COM4 receive window. Because the initiator cannot inspect a CRC-invalid payload, the run cannot prove that the damaged frame was the expected H2 PONG, nor can it prove from this result alone that COM3 successfully received the initiating PING.

## Directional link-quality observations from successful transactions

Across the 35 successful bidirectional matrix transactions:

- COM3 -> COM4 mean RSSI: approximately `-39.46 dBm`, mean SNR `10.00 dB`;
- COM4 -> COM3 mean RSSI: approximately `-39.91 dBm`, mean SNR `9.84 dB`.

The observed mean RSSI asymmetry is therefore small (~0.46 dB) in this checkpoint.

## Scientific boundary

Do not infer a true loss probability of 1/36 or a 42-byte loss probability of 1/6 from these small, non-randomized same-bench samples. The counts are descriptive only. The single CRC event is a reason to add explicit failure-class accounting and to repeat targeted reliability measurements before range/NLOS conclusions.

Next recommended step: keep the current PHY fixed and run a larger targeted 42-byte reliability repeat in both initiator directions, then proceed to controlled distance/environment sweeps.
