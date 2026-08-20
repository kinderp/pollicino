# HW-003 CRC repeat 1

## Purpose

Repeat the mirrored HW-003 direction (COM4 initiator -> COM3 responder) without moving or reflashing the boards, after the prior mirrored 20-sample run produced two responder `RXERR crc` events at sequences 2 and 20.

The question is deliberately narrow: do those CRC observations reproduce immediately under the same bench direction, and does the event-driven scheduling behavior remain stable?

## Repeat result

Configuration: 42-byte H2 PING/PONG, frozen PHY, 20 paced attempts, COM4 initiator, COM3 responder.

| Metric | Repeat 1 |
| --- | ---: |
| Attempts | 20 |
| Successful transactions | 20 |
| Matched timing/scheduler traces | 20 |
| CRC observations | 0 |
| RTT mean | 181049.55 us |
| RTT range | 58 us |
| IRQ -> handler mean | 16.15 us |
| IRQ -> handler range | 1 us (16..17) |
| IRQ -> TX-start mean | 1241.5 us |
| IRQ -> TX-start range | 25 us |
| RTT residual mean | 22.95 us |
| Spurious task wakeups | 0 |

Scheduler counters progressed coherently from 21 to 40 for both task wait and task wake counts.

## Comparison with the immediately preceding mirrored run

The previous COM4 -> COM3 run produced 18 successful transactions and two CRC observations. Both failed initiator transactions were timeouts whose responder serial tail reported `RXERR crc`.

The immediate repeat produced 20/20 successful transactions and no CRC observation. Therefore the previous two CRC events are not reproducible as a deterministic per-direction failure under this immediate same-bench repeat.

This does **not** prove that the CRC events were random, nor does it justify a packet-loss probability. Across these two same-direction runs the descriptive bench total is 38 successful transactions out of 40 attempts, with two observed CRC events, but that aggregate is retained only as a record of what happened on this bench.

## Scheduling conclusion

The scheduling result strengthens rather than weakens HW-003: on this repeat COM3 as responder held IRQ -> handler to 16..17 us across all 20 transactions while the normal Arduino loop retained its 1 ms idle delay. The approximately 1 ms polling modulation seen in HW-002T remains absent.

The scheduling-latency conclusion is therefore considered closed for the current same-bench, two-board scope. CRC reliability remains a distinct radio/reliability question.

## Next reliability step

Do not change firmware in response to the two prior CRC observations yet. A useful later reliability experiment should be explicitly designed for that purpose, with enough repeated observations and controlled variables (direction, board placement, frame size, PHY, RSSI/SNR, and environmental notes) to distinguish intermittent RF behavior from a systematic board/direction effect.

## Scientific boundaries

- Bench counts are descriptive and are not deployment packet-loss probabilities.
- No range, NLOS or interference conclusion is made.
- Cross-clock RTT residual is diagnostic only and is not propagation delay.
- Scheduler blocking/wakeup counters are not an electrical energy measurement.
