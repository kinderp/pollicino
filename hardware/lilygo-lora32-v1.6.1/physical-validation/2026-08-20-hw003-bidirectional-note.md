# HW-003 bidirectional physical validation — 2026-08-20

## Purpose

Validate that the HW-003 event-driven responder architecture removes the ~1 ms polling modulation on both physical LILYGO LoRa32 V1.6.1 boards, while keeping the Arduino loop's 1 ms idle delay.

The test is about responder scheduling latency. It is not a range, propagation-delay, interference, or deployment reliability experiment.

## Direction 1: COM3 -> COM4

Twenty 42-byte paced transactions completed successfully, with twenty matched responder timing/scheduler traces.

- IRQ -> handler: 16..23 us, mean 16.4 us, range 7 us.
- RTT: 181041..181117 us, mean 181053.8 us.
- On samples 2..20, RTT range is 21 us while IRQ -> handler range remains 7 us.
- Wait/wake counters advance coherently from 6 to 25.
- No spurious task wakeups were observed.

This direction was frozen previously in the first HW-003 physical evidence checkpoint.

## Direction 2: COM4 -> COM3

The mirror run produced 18 successful transactions and 2 failed transactions out of 20 attempts.

For the successful transactions:

- IRQ -> handler: 16..28 us, mean 16.78 us.
- RTT: 181025..181201 us, mean 181050.61 us.
- Excluding the first startup-like successful sample, the 17 successful samples from sequence 3 through 19 have IRQ -> handler 16..17 us (range 1 us) and RTT 181025..181050 us (range 25 us).

The successful mirror traces therefore reproduce the low-microsecond event-driven scheduling latency on COM3 as responder. The ~1 ms modulation seen under HW-002T `delay(1)` polling does not reappear.

## The two failed mirror transactions

Sequences 2 and 20 timed out at the initiator with RadioLib state `-6`. In both cases the responder USB output was `RXERR crc`.

That observation matters: these failures are not traces of a responder task waiting ~1 ms or missing its event-driven wake. The responder entered packet handling and rejected the received radio frame at CRC validation before a valid H2 PING could produce an `H2RESP` timing line.

The strict scheduler summary reports `counter_sequence_consistent=false` because it compares only matched `H2RESP` traces. After sequence 1 the matched trace reports wait/wake counters 1/1; the next matched trace, sequence 3, reports 3/3. The missing value 2 belongs to the CRC-failed sequence 2, which did not emit `H2RESP`. This is a limitation of the current matched-trace summary, not evidence that the FreeRTOS wake counter moved incorrectly. Sequence 20 occurs last, so no later H2RESP exists from which to infer the final cumulative value.

## Architectural conclusion

The event-driven architecture has now shown low-microsecond IRQ -> handler latency with either physical board acting as responder, despite the Arduino loop retaining a 1 ms idle delay. This supports the intended architectural claim: RX-done handling is decoupled from the Arduino loop cadence and does not require a busy/yield polling loop.

This closes the HW-003 scheduling-latency question at the current bench scope.

## Reliability follow-up

The mirror run's two CRC failures should not be hidden or converted into a deployment packet-loss probability. They are a separate reliability observation. A targeted follow-up should distinguish transient RF/CRC behavior from any direction-specific or implementation-specific effect before making reliability claims.

## Energy boundary

HW-003 demonstrates a task that blocks and wakes on notification. That is not an electrical energy measurement. No current, power, joules, or battery-life conclusion is supported until an external electrical measurement is performed.
