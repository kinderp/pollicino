# HW-003 — Event-driven LoRa responder

Status: implementation experiment.

## Goal

Replace the polling cadence that HW-002T identified as the dominant source of the ~1 ms responder RTT modulation with an event-driven responder path, while keeping the radio wire format and frozen PHY unchanged.

HW-003 is not a range test. It is a scheduler/latency experiment with scheduler-level energy proxies.

## Scientific baseline

HW-002T A–B–A showed that changing only the responder loop policy from `delay(1)` to yield-only collapsed `irq_to_handle_us` from a near-1 ms range to a few microseconds, and restoring `delay(1)` restored the modulation. HW-003 therefore tests an architectural fix rather than another observational correlation.

## Design

A dedicated FreeRTOS responder task waits on a direct task notification:

```text
SX1276 DIO0 RX-done
      |
      v
ISR callback
- capture micros()
- set packetReceived
- notify responder task
      |
      v
responder task unblocks
- take radio mutex
- handleReceivedPacket()
- readData()
- build/send PONG
- resumeReceive()
- release radio mutex
- block again
```

The Arduino `loop()` remains responsible for USB serial commands and keeps a 1 ms idle delay. Radio receive processing therefore no longer depends on that polling cadence.

## Invariants

HW-003 keeps unchanged:

- H2 `HW2_VERSION=1` and PING/PONG byte layout;
- 868.100 MHz / BW125 / SF7 / CR4/5 / sync 0x12 / 10 dBm / preamble 8;
- responder timing trace fields introduced by HW-002T;
- host-side airtime budgeting and pacing.

The implementation is a separate PlatformIO environment/source so HW-002T remains frozen and reproducible.

## Concurrency rule

Only one execution context may perform radio transactions at a time. A FreeRTOS mutex guards RadioLib state transitions. The responder task owns asynchronous RX handling; serial-triggered TX/measurement commands take the same mutex.

## Instrumentation

`INFO` advertises:

```text
lab=hw-003 event_driven_rx=1 scheduler_trace=1 scheduler_trace_version=1
```

The existing H2RESP timing fields remain unchanged for direct comparison. HW-003 appends USB-serial-only scheduler fields:

- `sched_v`;
- `task_wait_count`;
- `task_wake_count`;
- `task_spurious_wake_count`.

No scheduler instrumentation travels over LoRa.

## Energy boundary

Without an external current/power meter, HW-003 can report only scheduler-level proxies such as blocked waits and wakeups. It must not claim joules, watts, current draw or battery-life improvement from software timing alone.

A later HW-003E extension may add a USB power meter/current sensor and compare polling, yield-only and event-driven operation electrically.

## First physical acceptance test

Same bench, COM3 initiator -> COM4 responder, 42 bytes, 20 paced transactions.

Expected qualitative result:

- responder trace association remains intact;
- `irq_to_handle_us` remains in the low-microsecond regime despite the Arduino loop retaining a 1 ms idle delay;
- the ~1 ms loop-cadence sawtooth does not return;
- task wake/wait counters advance coherently.

The scientific conclusion is limited to scheduler latency and blocking behavior until direct electrical power measurements exist.
