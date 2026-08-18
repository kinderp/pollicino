# PN-005 — Content-addressed P2P chunk store

PN-005 tests whether verified receiver-side state can reduce scarce-link traffic without changing exact reconstruction. It remains standalone: no DNA, LoRa SDK, hosted resolver or application schema is required.

## Generic mechanism

- `PollicinoStore`: SHA-256-addressed verified chunks;
- `PCM1`: fixed-size chunk manifest with full object SHA-256 and per-chunk SHA-256;
- `PNA1`: compact availability bitset bound to the complete PCM1 fingerprint;
- only missing chunks cross the PN-002 exact-transfer path;
- final object reconstruction is verified against the full object SHA-256.

Identical chunk content is addressed once regardless of which object position references it.

## Accounting boundary

Two cases are reported separately:

1. **manifest-on-scarce** — PCM1 + PNA1 + missing chunks count on the scarce link;
2. **manifest-pre-resolved** — PCM1 was already obtained through a PN-003-style richer path, so scarce traffic contains PNA1 + missing chunks.

The second case shifts manifest cost to the rich-path side; it does not make that cost disappear.

## Frozen experiment

- object: 8192 bytes, SHA-256 `4518db781dcd29303c5d0ff540bb57c504595158fa885f0f93a5f4667ef57ff0`;
- 16 deliberately unique fixed 512-byte chunks;
- PCM1 raw manifest: 627 bytes;
- cache levels: 0%, 25%, 50%, 75%, 100%;
- clean PN-002 64-byte profile, isolating cache effects from packet loss;
- direct complete-object PNF1 reference: **12,846 scarce-link bytes**.

## Scientific result

Successful GitHub Actions run `32186393469`, scientific head `8fa6640af20a16b50f74e19d954975d752437791`:

- **121 root/scientific tests passed in 6.26 s**;
- every cache level and manifest mode reconstructed the exact object;
- artifact `9342615953` (`pn-005-results`);
- digest `sha256:ac9d7e17f83e21aae60a7f9e71f4f1c14713cc4b02e6acdfff1932b84e5ecdce`.

| Cache | Missing chunks | Chunk wire | Total with manifest on scarce | Total if manifest pre-resolved |
| ---: | ---: | ---: | ---: | ---: |
| 0% | 16 | 13,216 B | **14,274 B** | **13,283 B** |
| 25% | 12 | 9,912 B | **10,970 B** | **9,979 B** |
| 50% | 8 | 6,608 B | **7,666 B** | **6,675 B** |
| 75% | 4 | 3,304 B | **4,362 B** | **3,371 B** |
| 100% | 0 | **0 B** | **1,058 B** | **67 B** |

The fixed scarce costs are 991 B for framed PCM1 and 67 B for framed PNA1. Each 25% increase in this frozen receiver cache removes exactly four 512-byte source chunks and 3,304 scarce-link chunk bytes.

The zero-cache chunk protocol is intentionally worse than direct PNF1 transfer: 14,274 B with the manifest, or 13,283 B with a pre-resolved manifest, versus 12,846 B direct. Shared state has a coordination cost. The crossover occurs already at the frozen 25% cache level: 10,970 B including the scarce manifest, about 85.4% of direct-transfer traffic.

At 50% cache, total scarce traffic is 7,666 B with the manifest and 6,675 B when the manifest is pre-resolved. At 100% cache, no chunk payload crosses at all; only the 1,058 B manifest+availability exchange remains, or just the 67 B availability exchange if PN-003 already delivered the manifest through a richer path.

## Success criteria

All frozen criteria passed: exact reconstruction, monotonic missing-data reduction, strictly decreasing chunk traffic, zero chunk traffic at 100% cache, correct manifest accounting, the 25% crossover, fail-closed PCM1/PNA1 parsing, and zero application/radio dependency in the core.

## Conclusion and boundary

**PN-005 is a positive technical result for P2P shared-state reconstruction.** It demonstrates a concrete regime in which storing verified chunks at peers reduces the number of scarce-link bytes required to reproduce the exact file.

This is deduplication/shared-state gain, not compression of unknown data. PN-005 uses fixed-size chunks and no delta coding; content-defined chunking, version-aware patches and multi-peer sourcing remain later work.
