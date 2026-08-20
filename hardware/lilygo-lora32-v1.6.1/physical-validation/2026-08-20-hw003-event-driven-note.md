# HW-003 physical validation — event-driven responder

Date: 2026-08-20

## Purpose

Test whether the RX-done-to-handler latency can remain low while the Arduino loop still keeps a 1 ms idle delay, by moving radio receive handling to a dedicated FreeRTOS task notified directly from the SX1276 RX-done ISR.

This is a scheduler/latency experiment. It is not an electrical power measurement and does not establish watts, joules, current draw, or battery life.

## Physical run

- direction: COM3 initiator -> COM4 responder
- frame: 42 bytes H2 PING/PONG
- count: 20 paced transactions
- PHY: 868.100 MHz, BW 125 kHz, SF7, CR 4/5, private sync 0x12, 10 dBm, preamble 8
- nominal per-frame ToA: 88,000 us
- pacing input: 1.0% occupancy cap
- elapsed: 167.438 s
- environment label: `same-bench-indoor-hw003-event-driven`

Firmware advertised `lab=hw-003`, `event_driven_rx=1`, `scheduler_trace=1`, `scheduler_trace_version=1`, and `serial_idle_delay_ms=1`.

## Primary all-20 result

- attempts: 20
- successes: 20
- matched responder traces: 20
- RTT: mean 181,053.8 us, min 181,041 us, max 181,117 us, range 76 us, p50 181,052 us, p95 181,062 us
- IRQ -> handler: mean 16.4 us, min 16 us, max 23 us, range 7 us, p50 16 us, p95 17 us
- IRQ -> TX start: mean 1,240.75 us, min 1,234 us, max 1,258 us, range 24 us
- RTT residual: mean 22.8 us, min 12 us, max 30 us, range 18 us

Scheduler trace:

- task wait count: 6 -> 25
- task wake count: 6 -> 25
- each successive trace increments both counters by exactly one
- spurious wake count: 0 -> 0
- counter sequence consistency: true

The counter delta is 19 because the summary compares the first and twentieth observed cumulative values; the twenty individual traces themselves are 6,7,...,25.

## Startup sensitivity

Sequence 1 is retained in the primary summary. It had slightly longer local TX/response intervals than the following samples, but unlike HW-002T A1 it did not introduce millisecond-scale IRQ scheduling latency.

For samples 2–20:

- RTT mean: 181,050.47 us; range: 21 us
- IRQ -> handler mean: 16.42 us; range: 7 us
- IRQ -> TX start mean: 1,239.84 us; range: 12 us

## Comparison with HW-002T A-B-A

Using the same samples-2–20 sensitivity convention:

| Condition | Responder policy | IRQ->handler range | RTT range |
| --- | --- | ---: | ---: |
| HW-002T A1 | `delay(1)` polling | 959 us | 973 us |
| HW-002T B | `yield()` polling | 12 us | 33 us |
| HW-002T A2 | `delay(1)` polling restored | 613 us | 619 us |
| HW-003 | ISR -> FreeRTOS task notification, Arduino loop still idles 1 ms | **7 us** | **21 us** |

Relative to A1, the stable HW-003 range is 99.27% smaller for IRQ->handler and 97.84% smaller for RTT. Relative to A2, the reductions are 98.86% and 96.61% respectively.

HW-003 is also at least as stable as the prior `yield()` intervention while no longer requiring the receive path to be polled at yield-loop cadence.

## Interpretation

Under this firmware and same-bench setup, the event-driven responder successfully decouples RX-done handling latency from the Arduino loop's 1 ms cadence. The approximately 1 ms modulation seen with HW-002T `delay(1)` polling is absent: responder-local IRQ->handler latency remains in the tens-of-microseconds regime with only a 7 us observed range over 20 transactions.

The scheduler counters are consistent with the intended mechanism: the responder task blocks, is notified for each received packet, and no spurious wakeups were observed in this run.

This supports the architectural choice of an event-driven receive task for low and stable latency without relying on a fast polling loop.

## Scientific boundaries

- These 20/20 bench successes are descriptive and are not a deployment packet-loss probability.
- The run does not characterize range, NLOS, interference, mobility, or deployment conditions.
- ESP32 initiator and responder clocks are independent; the RTT residual is diagnostic and is not one-way propagation delay.
- Scheduler blocking/wakeup counters are proxies for control-flow behavior only. Electrical energy claims require external current/power instrumentation.
- A mirrored COM4 -> COM3 HW-003 run is still useful before declaring the behavior board-symmetric.

## Raw evidence

The physical runner generated the raw artifact locally as:

`hardware/lilygo-lora32-v1.6.1/physical-validation/2026-08-20-hw003-benchmark-com3-42b-20.json`

The machine-readable summary committed with this note is derived from that physical runner output. Preserve the local raw JSON for later inclusion/archival.
