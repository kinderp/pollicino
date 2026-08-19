# HW-002T same-bench timing localization

## COM3 initiator, COM4 responder

20×42-byte paced transactions, fixed PHY, same bench:

- 20/20 successes and 20/20 matched responder traces;
- RTT mean 181.4957 ms, range 181.170–181.925 ms;
- responder `irq_to_handle_us` mean 432.55 us, range 113–849 us;
- Pearson r(RTT, `irq_to_handle_us`) = 0.9995909;
- linear slope ≈ 1.0122 us RTT / us irq-to-handler;
- R² ≈ 0.999182;
- mean diagnostic residual = -0.55 us.

## COM4 initiator, COM3 responder

The exact mirrored 20×42-byte run reproduces the same mechanism on the other physical board:

- 20/20 successes and 20/20 matched responder traces;
- RTT mean 181.6421 ms, range 181.061–182.032 ms (971 us range);
- responder `irq_to_handle_us` mean 575.8 us, range 2–977 us (975 us range);
- Pearson r(RTT, `irq_to_handle_us`) = 0.9969472;
- linear slope ≈ 0.99858 us RTT / us irq-to-handler;
- R² ≈ 0.993904;
- mean diagnostic residual = -2.2 us, range -13..+13 us.

The clearest phase-wrap example is sequence 15 -> 16: RTT drops by 971 us while `irq_to_handle_us` drops by 975 us.

## Bidirectional checkpoint

Across all 40 successful timed transactions:

- Pearson r(RTT, `irq_to_handle_us`) = 0.9978877;
- linear slope ≈ 1.0040 us/us;
- R² ≈ 0.995780.

This strongly localizes the structured ~1 ms RTT modulation to responder scheduling between the SX1276 RX-done interrupt and `handleReceivedPacket()` on both boards. The firmware's `loop()` includes `delay(1)`, so that cadence is now a specific causal hypothesis, but this evidence alone does not prove it is the sole cause.

## Next causal experiment

Keep PHY, H2 wire format, 42-byte payload, timing instrumentation, board placement and pacing fixed, and change only the responder-loop 1 ms sleep policy. Compare the existing `delay(1)` baseline against a no-1-ms-sleep/yield-only variant.

## Scientific boundary

These are sequential, same-bench, fixed-PHY observations. Samples are not independent. The cross-clock residual is diagnostic and must not be interpreted as propagation delay. No distance, range, NLOS, interference or deployment-loss conclusion is supported.
