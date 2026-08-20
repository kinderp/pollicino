# HW-004 — controlled CRC / reliability characterization

## Purpose

HW-003 closed the same-bench scheduling-latency question: with either physical board acting as responder, the SX1276 RX-done interrupt wakes a dedicated FreeRTOS task in tens of microseconds while the Arduino loop keeps its 1 ms idle delay.

A separate observation remains: one COM4 -> COM3 HW-003 run produced two responder `RXERR crc` events, while an immediate same-direction repeat produced none. HW-004 is designed to characterize that phenomenon without changing the validated HW-003 firmware.

HW-004 is **not** a deployment packet-loss experiment. It is a small, controlled bench matrix intended to decide which follow-up hypothesis deserves more samples.

## Questions

1. **Direction / board-role association** — do CRC observations preferentially occur when one physical board is the responder?
2. **Frame-size association** — are observations concentrated at larger or smaller H2 frame sizes?
3. **Time / intermittency** — do observations cluster in experiment order rather than by direction or size?
4. **Scheduler separation** — on a CRC event, did the event-driven responder task still wake exactly once?

The fourth question matters because a CRC failure is a decode/reception outcome, while HW-003 scheduling is a firmware wakeup outcome. They must not be conflated.

## Frozen radio / firmware conditions

HW-004 uses the already validated HW-003 firmware unchanged:

- LILYGO LoRa32 V1.6.1 / SX1276;
- 868.100 MHz;
- BW 125 kHz;
- SF7;
- CR 4/5;
- sync word `0x12`;
- TX power 10 dBm;
- preamble 8;
- H2 `HW2_VERSION=1` PING/PONG layout unchanged;
- dedicated FreeRTOS event-driven responder task;
- Arduino serial loop retains its 1 ms idle delay.

No reflash is required when both boards already run HW-003.

## Default matrix

Default frame sizes reuse the established HW-002 matrix:

`16, 32, 42, 60, 120, 240` bytes.

The recommended first physical run uses four rounds. Every round contains both directions for every size, for a total of:

- 6 frame sizes;
- 2 directions;
- 4 attempts per direction × size cell;
- **48 attempts total**.

The four-round schedule counterbalances two simple order effects:

| Round | Size order | First direction in each size pair |
| --- | --- | --- |
| 1 | ascending | A -> B |
| 2 | descending | B -> A |
| 3 | descending | A -> B |
| 4 | ascending | B -> A |

This is not a randomized clinical/statistical design. It is a deterministic counterbalanced engineering experiment that prevents a simple monotonic time drift from being perfectly confounded with either frame size or direction.

## Per-attempt evidence

For every attempt `hw004.py` records:

- round and global order index;
- direction and physical initiator/responder ports;
- frame size and sequence;
- initiator `MRESULT`;
- matched `H2RESP` timing/scheduler trace when available;
- responder serial tail;
- responder `INFO` scheduler counters immediately **before** and **after** the transaction;
- the resulting counter deltas;
- a failure classification.

Failure classes currently distinguish at least:

- `success`;
- `responder_crc` — failed transaction plus responder `RXERR crc`;
- `responder_rx_error`;
- `responder_invalid_length`;
- `initiator_timeout_no_crc_observed`;
- other initiator-side measurement errors.

A CRC event with responder `task_wake_count` delta = 1 is direct evidence that the event-driven task woke and the frame later failed CRC handling. That separates radio decode reliability from scheduler latency.

## Planning and pacing

The runner first queries `TOA` for every selected size on **both boards** and fails closed if the reported values differ.

Every planned transaction contains one frame transmission per node on the all-success path. The experimental occupancy input is therefore enforced per node using the time-on-air of the previous transaction before the next transaction may start.

`--tx-occupancy-cap-percent` remains an **experiment pacing input**, not a legal-compliance claim. Current regional/sub-band rules must still be verified independently before RF execution.

The runner also requires an explicit per-node `--airtime-budget-ms` before `--execute`.

## Recommended procedure

Keep both boards stationary, antennas attached, and do not change cabling or firmware between dry-run and execution.

First inspect the plan:

```powershell
py hardware/lilygo-lora32-v1.6.1/host/hw004.py matrix `
  --port-a COM3 `
  --port-b COM4 `
  --sizes 16,32,42,60,120,240 `
  --rounds 4 `
  --timeout-ms 3000 `
  --tx-occupancy-cap-percent 1.0 `
  --environment "same-bench-indoor-hw004-crc-matrix" `
  --output hardware/lilygo-lora32-v1.6.1/physical-validation/2026-08-20-hw004-plan.json
```

Inspect in particular:

- `transactions`;
- `planned_per_node_tx_airtime_us`;
- `estimated_minimum_wall_seconds_for_requested_cap`;
- `toa_us_by_frame_bytes`;
- the complete `schedule`.

Only after accepting the plan, execute with an explicit airtime budget greater than or equal to the reported planned per-node airtime.

## Interpretation rules

### If no CRC is observed

Report “0 CRC observations in this 48-attempt controlled bench matrix.” Do **not** report a zero packet-loss probability. The result weakens deterministic direction/size hypotheses but cannot rule out rare intermittent failures.

### If CRC observations cluster by one direction

Repeat only the implicated direction with a larger, predeclared sample count while keeping size/order control. Do not infer a board defect from four attempts per cell alone.

### If CRC observations cluster by frame size

Run a focused size experiment with neighboring sizes and more repetitions. Larger packets have more airtime and encoded bits, but HW-004 alone does not establish a causal mechanism.

### If CRC observations cluster in time

Investigate intermittent RF/environmental effects, power/cabling, nearby emitters, and thermal/time-related behavior before changing protocol code.

### If a CRC occurs with wake delta != 1

Treat it as an instrumentation/scheduler anomaly requiring investigation before using that attempt in a radio-reliability interpretation.

## Scientific boundaries

- Bench success fractions are descriptive only.
- No deployment packet-loss probability is estimated.
- No range, NLOS, interference or field-reliability conclusion is supported by this same-bench matrix.
- RSSI/SNR are available only for successfully decoded transactions in the current firmware; do not invent per-frame RSSI/SNR for CRC-failed packets.
- Cross-board timing residuals are diagnostic and are not one-way propagation-delay estimates.
- Scheduler blocking/wakeup counters are not electrical energy measurements.
- HW-004 does not change the H2 wire format, PHY, or HW-003 firmware.
