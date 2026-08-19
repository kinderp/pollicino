# HW-002T first physical timing trace — COM3 initiator, 42 B

First physical HW-002T timing transaction after the frozen HW-002 same-bench baseline.

## Result

- initiator: COM3;
- responder: COM4;
- H2 frame: 42 B each direction;
- result: success;
- RTT: 182,709 us;
- nominal RadioLib ToA: 88,000 us per frame, 176,000 us round trip;
- RTT excess over nominal two-frame ToA: 6,709 us;
- initiator TX blocking: 89,965 us, i.e. 1,965 us above nominal one-frame ToA;
- responder RX IRQ -> TX start: 2,287 us;
- responder TX blocking: 90,461 us, i.e. 2,461 us above nominal one-frame ToA;
- derived residual: -4 us.

The responder turnaround decomposition is internally exact:

`734 + 864 + 689 = 2,287 us`

where:

- RX IRQ -> handler: 734 us;
- handler -> readData complete: 864 us;
- readData complete -> TX start: 689 us.

The responder total is also internally exact:

`2,287 + 90,461 = 92,748 us`.

The observed RTT excess is almost completely decomposed by the measured local intervals:

`1,965 + 2,287 + 2,461 = 6,713 us`, versus an observed excess of `6,709 us`, leaving the reported `-4 us` cross-clock residual.

## Interpretation boundary

The -4 us residual is not a negative propagation time. Initiator and responder use independent ESP32 clocks, and the residual combines clock tolerance plus uninstrumented radio/driver timestamp boundaries and physical propagation. At this scale the important result is closure to a few microseconds, not the sign.

This one sample is consistent with the hypothesis that the previously observed sub-millisecond RTT phase structure may be localized in responder firmware scheduling/handling or blocking-TX timing. A paced series is required before correlating RTT phase with `irq_to_handle_us` or any other component.
