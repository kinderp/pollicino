# HW-005 physical TX-power staircase — 2026-08-20

## Setup

- same-bench indoor geometry;
- LILYGO LoRa32 T3 V1.6.1 / SX1276 pair on COM3 and COM4;
- fixed PHY: 868.100 MHz, BW 125 kHz, SF7, CR 4/5, sync 0x12, preamble 8;
- 42-byte H2 PING/PONG frames;
- HW-005 event-driven responder derived from frozen HW-003;
- both nodes set to the same runtime TX power before each pair;
- PA_BOOST-only staircase: 10, 8, 6, 4, 2 dBm, then 2, 4, 6, 8, 10 dBm with reversed direction-first order;
- 1% experimental TX-occupancy pacing input.

## Result

All 20 planned transactions succeeded and all 20 responder traces matched. No CRC, timeout, spurious-wake, or mutex-timeout failure was observed in this run. This is a descriptive same-bench result, not a deployment packet-loss estimate.

| Configured TX power | Attempts | Successes | Mean local RSSI | Mean remote RSSI |
| ---: | ---: | ---: | ---: | ---: |
| 10 dBm | 4 | 4 | -35.00 dBm | -35.75 dBm |
| 8 dBm | 4 | 4 | -38.75 dBm | -38.75 dBm |
| 6 dBm | 4 | 4 | -40.75 dBm | -40.75 dBm |
| 4 dBm | 4 | 4 | -42.75 dBm | -43.00 dBm |
| 2 dBm | 4 | 4 | -43.50 dBm | -44.25 dBm |

Across the full 10 -> 2 dBm endpoint change, configured TX power decreased by 8 dB while both aggregate local and aggregate remote receiver RSSI means decreased by 8.5 dB. This is strong bench evidence that the runtime power control produces the intended link-strength trend. It is not a calibrated conducted-power measurement and exact per-step linearity is not claimed.

Direction-specific responder-side RSSI also moved coherently:

- COM3 -> COM4: -35.0, -38.5, -40.0, -42.5, -44.0 dBm at 10, 8, 6, 4, 2 dBm;
- COM4 -> COM3: -36.5, -39.0, -41.5, -43.5, -44.5 dBm at 10, 8, 6, 4, 2 dBm.

SNR remained roughly around 9.5–10 dB on the responder-side means across the staircase, and no reliability transition appeared. Under this geometry, reducing configured TX power to 2 dBm therefore did not approach an observed failure region.

## Scheduler observation

IRQ-to-handler remained in the event-driven low-latency regime: 12–36 us overall, mean 24.2 us, median 24 us. Seventeen of the 20 samples were exactly 24 us; the remaining values were 12, 28 and 36 us. No dependence of scheduler latency on configured TX power is inferred from this small run.

## Interpretation

HW-005 phase 1 validates the experimental control variable: software TX-power changes produce a reversible receiver-RSSI trend while the event-driven scheduler remains stable. The staircase alone is insufficient to reach the link margin on the current same-bench geometry.

The next phase should keep this instrumentation and add controlled physical attenuation, separation, or obstacles. The scientific target is the transition region in which RSSI/SNR degrade and CRC/timeout events begin to appear, not simply another all-success bench repeat.

## Boundaries

- RSSI/SNR are receiver observations, not calibrated conducted TX-power measurements.
- Same-bench success fractions are descriptive only.
- No electrical current, power, joule, or battery-life measurement is made.
- RTT residual remains diagnostic only and is not one-way propagation delay.
- The raw runner artifact `2026-08-20-hw005-power-staircase-20.json` remains preserved locally.
