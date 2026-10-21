# RF evidence catalog and deterministic replay

Pollicino keeps physical RF measurements as scientific evidence rather than treating them as anecdotes or converting them immediately into a universal packet-loss model.

The RF evidence layer exists so network/session development can continue when the two LoRa boards are unavailable.

## Goals

The layer has two responsibilities:

1. **catalog evidence** from supported HW records into a small normalized shape;
2. **extract ordered traces** when a raw record actually contains per-attempt observations.

It must not:

- merge overlapping raw and derived summaries into a fake aggregate;
- infer receiver telemetry that was not observed;
- reinterpret an untethered timeout as a specific RF failure;
- repeat a short physical trace silently and present the repetition as new evidence.

## CLI

From the repository root:

```bash
python -m pollicino.net.rf \
  hardware/lilygo-lora32-v1.6.1/physical-validation
```

With the package installed:

```bash
pollicino-rf \
  hardware/lilygo-lora32-v1.6.1/physical-validation
```

Optional JSON output:

```bash
pollicino-rf \
  hardware/lilygo-lora32-v1.6.1/physical-validation \
  --output /tmp/pollicino-rf-catalog.json
```

## Normalized evidence

`RFEvidence` records file-scoped metrics such as:

- lab and schema;
- environment/checkpoint/direction;
- frame size and TX power when fixed;
- attempts/successes/failures;
- CRC events when reported;
- mean RSSI/SNR/RTT/IRQ timing when available;
- explicit source/provenance references when the historical record contains them.

The catalog deliberately does **not** calculate one global packet-loss rate across every JSON file. The archive contains raw captures, one-direction runs, bidirectional summaries and later derived analyses that can overlap.

An aggregate is scientifically meaningful only after selecting a set of disjoint experiments.

## Replay traces

`RFReplayTrace` contains ordered `RFTraceSample` observations.

Initial extractors support:

- `pollicino-hw002-benchmark-v1` raw `samples`;
- executed `pollicino-hw006-checkpoint-v1` raw `attempts`.

A trace preserves:

- success/failure;
- failure class;
- frame bytes;
- local/remote RSSI;
- local/remote SNR;
- RTT;
- time-on-air.

Missing telemetry remains `None`.

### Untethered HW-006 boundary

For HW-006 the remote serial stream is not available during a physical checkpoint. A timeout therefore stays:

```text
timeout_ambiguous_untethered
```

The replay layer must not decide after the fact whether that timeout was caused by:

- a lost PING;
- remote CRC/decode failure;
- a lost return PONG;
- remote reset or power-bank shutdown;
- another RF failure.

Remote RSSI/SNR exist only when a valid PONG returned them in the frozen H2 frame.

## Replay exhaustion

By default:

```python
trace.replay(100)
```

fails if only 20 physical samples were recorded.

Explicit repetition:

```python
trace.replay(100, repeat=True)
```

is allowed only as a **synthetic reuse mode**. It does not create 100 new measurements and must not be cited as physical evidence.

## Relationship to the scarce-link simulator

The existing `ScarceLinkProfile` uses deterministic synthetic loss probabilities and supports fragmentation, duplicate handling, ACK accounting and stop-and-wait retry.

RF replay is complementary:

```text
synthetic profile -> controlled probability/seed experiments
physical trace    -> deterministic replay of an observed sequence
```

The next step is to let exact-session and resumable-transfer tests consume a physical transaction trace without changing PNF1 or the radio firmware.

## HW-006 readiness

No new physical measurement is required to develop this layer. When hardware access returns, each executed HW-006 checkpoint already emits the fields needed by the replay extractor.

That lets the future workflow become:

```text
run checkpoint
 -> save JSON
 -> catalog evidence
 -> replay exact-session behavior
 -> compare synthetic simulator with measured trace
 -> decide whether the model/PHY needs refinement
```
