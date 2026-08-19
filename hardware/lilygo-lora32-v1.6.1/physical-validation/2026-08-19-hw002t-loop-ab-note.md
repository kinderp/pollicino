# HW-002T loop-delay A–B–A result — 2026-08-19

## Question

Does the responder's fixed `delay(1)` loop cadence cause the structured approximately 1 ms RTT modulation previously localized to `RX-done IRQ -> handleReceivedPacket()`?

## Controlled intervention

The same firmware image was used in all conditions. H2 radio bytes, PHY, frame size, timing instrumentation, timeout, direction and pacing were held fixed. The only runtime intervention was the responder loop policy:

- **A1:** `loop_delay_ms=1`
- **B:** `loop_delay_ms=0` (`yield()` only)
- **A2:** `loop_delay_ms=1` restored

Initiator remained at its default 1 ms loop policy. All three conditions completed 20/20 successful transactions with 20/20 matched responder traces.

## Primary observation

The intervention behaved as predicted.

| Condition | responder policy | RTT range, all 20 | IRQ->handler range, all 20 | IRQ->handler mean |
|---|---:|---:|---:|---:|
| A1 | 1 ms | 1763 us | 959 us | 609.3 us |
| B | 0 ms/yield | 121 us | 12 us | 7.2 us |
| A2 | 1 ms | 788 us | 895 us | 648.3 us |

The A1 all-sample RTT range is inflated by sequence 1, where several non-IRQ phases were simultaneously slower. That run-start transient was identified after A1 and before executing B. Therefore the complete results remain above, while samples 2–20 are also reported as a sensitivity analysis.

## Stable samples 2–20

| Condition | RTT range | RTT sample SD | IRQ->handler range | IRQ->handler sample SD | r(RTT, IRQ) | slope us/us |
|---|---:|---:|---:|---:|---:|---:|
| A1 | 973 us | 294.14 us | 959 us | 293.69 us | 0.999752 | 1.00127 |
| B | 33 us | 9.82 us | 12 us | 3.95 us | 0.354394 | 0.88151 |
| A2 | 619 us | 195.60 us | 613 us | 197.53 us | 0.999071 | 0.98930 |

The low correlation in B is not evidence against the hypothesis: after the intervention, `irq_to_handle_us` has only a 12 us total range, so there is almost no approximately 1 ms signal left to explain.

Relative to A1, B reduced:

- IRQ->handler range by **98.75%**;
- RTT range by **96.61%**;
- IRQ->handler sample SD by **98.66%**;
- RTT sample SD by **96.66%**.

Relative to A2, B reduced:

- IRQ->handler range by **98.04%**;
- RTT range by **94.67%**;
- IRQ->handler sample SD by **98.00%**;
- RTT sample SD by **94.98%**.

The mean `irq_to_handle_us` fell from 601.58 us in A1 to 7.47 us in B and returned to 677.21 us in A2 (samples 2–20).

## Interpretation

This is intervention-plus-reversibility evidence, not just correlation:

```text
A1: delay(1)   -> broad IRQ->handler phase + broad RTT
B : yield only -> both collapse
A2: delay(1)   -> both return
```

Under this firmware and bench setup, the fixed 1 ms responder loop sleep is therefore a **dominant causal contributor** to the observed approximately 1 ms RTT modulation.

It is still too strong to claim that `delay(1)` is the sole source of every microsecond of latency or jitter. The residual B RTT range is about 33 us on stable samples, and the first transaction in a run has additional startup effects.

## RF-level drift caveat

A2 did not reproduce A1/B RF levels exactly: mean local RSSI moved from approximately -42 dBm in A1/B to -46.6 dBm in A2, and remote RSSI from approximately -41 dBm to -45.2 dBm. SNR remained strong and all transactions succeeded.

That several-dB RF drift prevents describing A2 as a perfectly identical propagation environment. It does **not** erase the software-local causal observation: the `irq_to_handle_us` modulation disappears under the zero-delay policy and reappears when the 1 ms policy is restored.

## Scientific boundary

- sequential samples are not independent;
- no p-value is used as proof of causality;
- the cross-board residual is diagnostic and not propagation delay;
- this experiment says nothing about range, NLOS, interference robustness or deployment packet-loss probability;
- a useful generalization check is to repeat the intervention with the physical roles reversed (COM4 initiator, COM3 responder).

Machine-readable summary: `2026-08-19-hw002t-loop-ab-summary.json`.
