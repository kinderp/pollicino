# HW-002 targeted 42-byte reliability repeats

Frozen PHY: `868.100 MHz`, `BW125`, `SF7`, `CR4/5`, `10 dBm`. Same-bench indoor reliability scenario. Both runs used the same frozen `hw002.py` acquisition runner and 1% experimental pacing input.

## COM4 initiator -> COM3 responder

- 20 attempts, 20 observed successes.
- RTT mean: `181.7417 ms`; min `181.067 ms`; max `182.049 ms`.
- Mean responder-observed COM4->COM3 RSSI/SNR: `-39.25 dBm / 9.8 dB`.
- Mean initiator-observed COM3->COM4 RSSI/SNR: `-38.35 dBm / 9.85 dB`.
- Elapsed: `167.406 s`; planner estimate: `167.376 s`.
- No CRC mismatch or timeout occurred; sequence 8 succeeded normally.

## COM3 initiator -> COM4 responder

- 20 attempts, 19 observed successes, 1 timeout.
- Successful RTT mean: `181.545 ms`; min `181.071 ms`; max `182.042 ms`.
- Mean responder-observed COM3->COM4 RSSI/SNR: `-37.526 dBm / 9.658 dB`.
- Mean initiator-observed COM4->COM3 RSSI/SNR: `-38.789 dBm / 9.987 dB`.
- Elapsed: `167.375 s`; planner estimate: `167.376 s`.
- Failure: sequence 16, `error=timeout`, `state=-6` (`RADIOLIB_ERR_RX_TIMEOUT`), firmware-level RTT `3.091752 s`.

## Combined targeted repeat checkpoint

- 40 attempts total;
- 39 observed successes;
- 1 timeout;
- 0 CRC mismatches in these 40 targeted attempts;
- successful RTT weighted mean: `181.6459 ms`.

The earlier six-size matrix contained one independent `state=-7` CRC-mismatch event. That event remains valid evidence and is intentionally kept separate from the 40 targeted repeats.

## Timing observation

Both directions continue to show structured sub-millisecond RTT phases rather than purely unstructured jitter. The COM3 repeat decreases through the first ten samples, jumps by roughly one millisecond at sequence 11, then drifts downward again; the COM4 repeat showed a related phase-like pattern. No causal explanation is claimed yet. A future instrumentation revision should add internal firmware timestamps before attempting attribution.

## Failure semantics

The frozen acquisition runner reports initiator-observed outcomes. A timeout cannot distinguish whether the initiating PING was lost, the responder transmitted a PONG that was lost, or another receive-path event prevented a valid PONG from being accepted. Likewise, a CRC mismatch proves a CRC-invalid LoRa frame was detected in the receive window but does not by itself prove it was the expected H2 PONG.

A separate host analyzer, `hw002_failures.py`, was added after the physical datasets were frozen. It classifies existing JSON outcomes without changing the acquisition runner or H2 firmware.

## Scientific boundary

`39/40` is an observed same-bench result, not a general packet-loss probability. The sample is still small, fixed-distance, fixed-PHY, sequential and non-randomized. Range, NLOS, interference sensitivity and alternative radio profiles remain uncharacterized.
