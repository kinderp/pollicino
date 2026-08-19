# HW-002T — causal loop-delay A–B–A experiment

## Question

Bidirectional HW-002T evidence localized the observed ~1 ms RTT modulation to the responder interval from SX1276 RX-done IRQ to `handleReceivedPacket()`.

The current responder loop contains `delay(1)`. The causal question is:

> Does the fixed 1 ms loop delay cause most of the measured `irq_to_handle_us` and RTT modulation?

## Controlled variable

One firmware image exposes a serial-only runtime control:

```text
LOOPDELAY 1
LOOPDELAY 0
```

- `1`: baseline `delay(1)` behavior;
- `0`: no fixed 1 ms sleep; use cooperative `yield()` instead.

The default after reset is `1` so the historical HW-002T baseline remains the reference behavior.

`INFO` reports both `loop_delay_control=1` and the currently active `loop_delay_ms` value.

The H2 radio wire format, `HW2_VERSION=1`, PHY, frame size and timing trace format do not change.

## Why runtime control?

Opening an ESP32 serial port may reset the board. Therefore setting the policy manually before starting the host runner would not be reliable.

`hw002_timing.py` now accepts:

```text
--responder-loop-delay-ms 0|1
```

After both ports have opened/reset, the runner:

1. verifies timing capability;
2. verifies loop-delay control capability;
3. applies the requested policy only to the responder;
4. re-queries `INFO` and refuses to continue unless the responder confirms the requested value;
5. records requested, initial and applied loop policies in the result JSON.

The initiator stays at its reset/default policy. The initiator is inside a blocking `MPING` transaction while RTT is measured, so the experimental scheduling variable is restricted to the autonomous responder loop.

## A–B–A protocol

Keep fixed:

- same two physical boards;
- same physical placement/orientation;
- antennas attached;
- 868.100 MHz;
- BW 125 kHz;
- SF7;
- CR 4/5;
- sync word `0x12`;
- 10 dBm;
- preamble 8;
- 42-byte H2 PING/PONG;
- 20 transactions per condition;
- 3000 ms receive timeout;
- 1% experiment pacing input;
- same initiator/responder direction for all three runs.

Run:

```text
A1: responder_loop_delay_ms = 1
B : responder_loop_delay_ms = 0
A2: responder_loop_delay_ms = 1
```

Do not move the boards between conditions.

## Falsifiable prediction

If the fixed 1 ms sleep is the main cause:

- A1 and A2 should reproduce a broad, phase-like `irq_to_handle_us` distribution approaching ~1 ms range;
- B should show a large collapse in `irq_to_handle_us` range;
- RTT range should collapse by approximately the same amount in B;
- other measured timing phases should remain broadly comparable;
- restoring A2 should restore the broad scheduling/RTT modulation.

If B retains ~1 ms modulation, the hypothesis is incomplete or wrong and investigation moves to FreeRTOS scheduling, driver/IRQ boundaries or another periodic source.

## Primary metrics

For each condition record:

- attempts/successes/failure classes;
- matched timing traces;
- RTT min/mean/p50/p95/max and range;
- `irq_to_handle_us` min/mean/p50/p95/max and range;
- `handle_to_read_done_us`;
- `read_done_to_tx_start_us`;
- initiator/responder TX blocking distributions;
- diagnostic RTT residual;
- RSSI/SNR only as link-context controls.

For the causal comparison report at least:

```text
range_B / mean(range_A1, range_A2)
```

for both RTT and `irq_to_handle_us`, plus restoration in A2.

## Scientific boundary

This experiment can establish the software scheduling source of the bench RTT modulation. It does not characterize propagation delay, range, NLOS behavior, interference sensitivity or deployment packet-loss probability.
