# HW-002 COM3 payload-size matrix — first physical sweep

Same-bench indoor run with COM3 initiator and COM4 autonomous responder. Frozen PHY: 868.100 MHz, BW125, SF7, CR4/5, 10 dBm. Three H2 PING/PONG transactions were executed for each frame size: 16, 32, 42, 60, 120 and 240 bytes.

## Result

All 18 attempted transactions succeeded. This is a repeatability checkpoint only; 18/18 does not establish a true zero packet-loss probability.

| Frame | ToA/frame | Mean RTT | RTT excess over 2×ToA | Airtime share of mean RTT | Mean remote RSSI | Mean local RSSI |
|---:|---:|---:|---:|---:|---:|---:|
| 16 B | 52 ms | 109.438 ms | 5.438 ms | 95.03% | -39.0 dBm | -39.0 dBm |
| 32 B | 72 ms | 150.522 ms | 6.522 ms | 95.67% | -39.0 dBm | -39.0 dBm |
| 42 B | 88 ms | 181.617 ms | 5.617 ms | 96.91% | -39.0 dBm | -39.33 dBm |
| 60 B | 113 ms | 233.405 ms | 7.405 ms | 96.83% | -39.0 dBm | -39.0 dBm |
| 120 B | 200 ms | 408.269 ms | 8.269 ms | 97.97% | -39.0 dBm | -39.0 dBm |
| 240 B | 380 ms | 769.406 ms | 9.406 ms | 98.78% | -39.33 dBm | -39.33 dBm |

The corrected planner estimated 234.260 s and the actual run completed in 234.328 s, only ~68 ms above the nominal lower-bound estimate. Total confirmed radio accounting for the successful run is 3,060 radio bytes and 5.430 s of two-node TX airtime.

## Descriptive relationship

Across the six same-bench size means, mean RTT follows round-trip RadioLib time-on-air extremely closely. A descriptive least-squares fit gives approximately:

`RTT_ms = 1.00575 × (2 × ToA_ms) + 5.375`

with R² ≈ 0.999994.

This is useful evidence that airtime dominates RTT under this fixed PHY, but it is **not** a general propagation/channel model: there are only six size means, all measured in one bench environment.

## Link-quality observation

Mean RSSI stays approximately -39 dBm in both directions across all tested sizes. Mean SNR remains roughly 9.4–10.9 dB. There is no visible payload-size-dependent RSSI degradation in this small same-bench sweep.

The high 12.5 dB and 12.25 dB remote SNR readings in individual small-frame samples are preserved as observations and are not smoothed away or given a causal interpretation.

## Scientific boundary

This run does not characterize:

- packet-loss probability beyond the observed 18/18 success checkpoint;
- distance/range behavior;
- NLOS, walls/floors or interference;
- alternative SF/BW/CR/power profiles;
- regulatory compliance for general deployment.

The next controlled step is the same six-size × three-sample matrix with COM4 as initiator, without moving either board, followed by a bidirectional comparison.
