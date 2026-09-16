# PNA2 simple codec and PNF1 wire regimes

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-27

## Use-case gate question

Current PNA1 sends a fixed availability bitmap for every PCM1 manifest. At the current PCM1 maximum of 65,535 chunks this costs 8,231 source bytes even when the receiver is missing only a handful of chunks or owns almost nothing.

The concrete use case is exact synchronization over a scarce/intermittent contact where the peers already refer to the same manifest and the receiver must describe its verified chunk availability with fewer bytes.

Before adding minisketch, IBLT or rateless reconciliation, the Use-Case Justification Gate requires the simplest lossless alternatives to be measured first.

## Current PNA1 baseline

From the existing production format:

```text
PNA1 header = 39 bytes
availability = ceil(chunk_count / 8)
MAX_CHUNKS = 65,535
```

Therefore:

```text
PNA1(max) = 39 + 8,192 = 8,231 bytes
```

PNA1 remains unchanged by this research.

## Research harness

`availability_reconciliation.py` defines a non-production `PNR2` research envelope with a common 40-byte header and five lossless candidate codecs:

1. `MISSING_U16` — sorted missing chunk indices;
2. `AVAILABLE_U16` — sorted available chunk indices;
3. `MISSING_RANGES_U16` — `(start,length)` ranges of missing chunks;
4. `AVAILABLE_RANGES_U16` — `(start,length)` ranges of available chunks;
5. `BITMAP_ZLIB` — lossless zlib compression of the existing availability bitmap.

Every candidate must round-trip exactly back to the existing `AvailabilitySummary` before it is eligible for comparison.

This is a benchmark harness, not a PNA2 negotiation or production wire contract.

## Sparse-index threshold at the real PCM1 limit

For 65,535 chunks, a missing-index list costs:

```text
40 + 2 * missing_count
```

Observed exact threshold relative to PNA1:

```text
4,095 missing -> 8,230 bytes  < 8,231 PNA1
4,096 missing -> 8,232 bytes  > 8,231 PNA1
```

So with this one-byte-larger research header, plain missing-u16 is source-byte-cheaper than PNA1 only below 4,096 missing chunks, about 6.25% of the maximum manifest.

This threshold does not apply to range or compressed representations.

## Structure matters more than count alone

The first validation intentionally failed an assumption: with only twenty chunks available in a 65,535-chunk manifest, `AVAILABLE_U16` is only 80 bytes, but a nearly all-zero bitmap compresses even further with zlib.

The test was corrected to preserve that result instead of forcing sparse indices to win.

Representative source-byte regimes:

- 20 isolated missing chunks -> `MISSING_U16`, 80 bytes;
- one contiguous hole of 4,096 chunks -> `MISSING_RANGES_U16`, 44 bytes;
- only 20 available chunks in a highly structured bitmap -> compressed bitmap can beat the 80-byte available list;
- deterministic high-entropy availability -> compressed bitmap grows and PNA1 remains preferable.

The conclusion is therefore not “use sparse indices”. It is:

> availability representation should be selected from the observed state pattern, and PNA1 must remain an explicit candidate.

## PNF1 wire benchmark

`availability_wire_benchmark.py` passes PNA1 and every research candidate through the existing deterministic exact PNF1 transfer path.

This measures:

- source bytes;
- PNF1 frame count;
- data transmissions;
- ACK transmissions;
- deterministic retries;
- data wire bytes;
- ACK wire bytes;
- total wire bytes;
- exact round-trip state.

The representative no-loss profile used for the checkpoint is explicitly synthetic:

```text
max_frame_bytes = 64
payload capacity = 46 bytes after current PNF1 header
ack_bytes = 8
bitrate_bps = 5000
```

No real LoRa capacity is inferred from these values.

## Representative wire results

Validation: GitHub Actions `33082601315`.

- full project suite: 274 passed, 2 skipped;
- targeted availability codec + wire tests: 8 passed.

At `MAX_CHUNKS = 65,535`:

| Availability pattern | Best representation | Source bytes | PNF1 frames | Modeled wire bytes | PNA1 frames | PNA1 modeled wire |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 20 isolated missing | missing-u16 | 80 | 2 | 132 | 179 | 12,885 |
| one missing range of 4,096 | missing-range | 44 | 1 | 70 | 179 | 12,885 |
| none available | available-ranges / empty representation | 40 | 1 | 66 | 179 | 12,885 |
| all available | missing-ranges / empty representation | 40 | 1 | 66 | 179 | 12,885 |

A separate deterministic high-entropy test requires PNA1 itself to win over every candidate. This prevents the research selector from assuming compression is always beneficial.

A deterministic impaired-link test also verifies that shorter exact representations preserve their advantage while retries remain explicitly accounted rather than hidden in an encoded-byte proxy.

## Why this matters for PollicinoNet

A saved availability byte can save more than one wire byte because crossing a PNF1 fragmentation boundary also adds another frame header and ACK, and may expose another frame to retry.

This is especially relevant for:

- `UC-CONTENT-001`, where a returning node may already own almost every chunk of a file/manifest;
- school/data-mule synchronization, where repeated encounters can leave peers nearly synchronized;
- any reference/metadata corpus where the difference is sparse or clustered.

## Current gate decision

**PNA2 simple-codec family: PROTOTYPE / CONTINUE.**

**minisketch / IBLT / rateless reconciliation: DEFER for the current asymmetric manifest-availability use case.**

The simple candidates already cover several high-value regimes with very small state and no advanced data structure. Advanced reconciliation should be introduced only for a discriminating use case that these representations do not solve adequately, such as a genuinely symmetric two-partial-peer set-difference problem where neither side can cheaply describe its state relative to a known manifest.

Do not replace PNA1 yet. The next architectural question is how a future peer would safely select/negotiate one of these representations while preserving backward compatibility and without spending more negotiation bytes than the chosen codec saves.

## Evidence boundary

All values are deterministic `MODEL_SYNTHETIC` PNF1 accounting. They are not measured LoRa airtime, energy, range, collision probability or field capacity.

Physical calibration remains behind **GATE PROVE FISICHE HW-006**.
