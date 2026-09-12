# PX15 scientific report

## Result

```text
GATE: PX15-PN-B4
IDENTIFIER_PROVENANCE: repository-owner candidate derived from PX14 recommendation
CLASSIFICATION: POLLICINO_BOUNDED_FRAGMENTATION_READY_WITH_LIMITS
CONFIDENCE: HIGH
PX14_BASELINE: 73c72d55d9775029cdc1824b04fea8e5e53367d2
IMPLEMENTATION: b0d3302edde427ccb91e0efa64a9bb4c5ea160b3
```

The hypothesis survived. Complete experimental B2/B2F/B2C/B2A messages crossed
a synthetic bounded MTU through real independent Python workers. Fragment loss,
duplication, reverse delivery, deterministic reordering, interruption,
corruption, and process restart did not produce partial native state. Durable
D2/D3 state remained the only persistent progress authority.

Baseline validation was 564 passed, 5 skipped; focused inherited PX11-PX14 was
196 passed; compileall passed. The implementation closure ran 667 passed, 5
skipped and the PX15-focused suite ran 103 passed.

## Selected model

Model A, a clean 52-byte experimental B4 fragment envelope, was selected. It
uses complete-message SHA-256 identity, inherited total-length bounds, canonical
index/count shape, payload length, and fragment CRC32. It supports unordered
delivery and identical duplicates with one volatile incomplete message per
direction. The existing complete B2 message digest and native decoder remain
authoritative.

Model B (reuse PNF1 pure primitives) was rejected because current PNF1 uses a
caller-provided 32-bit transfer identifier, lacks a receiver allocation bound
derived from B2, and is batch rather than incremental one-in-flight reassembly.
Model C (wholesale PNF1) was rejected because `transmit_exact()` combines frame
transfer with stop-and-wait retry and ACK-loss behavior. Model D (no protocol
fragmentation) was falsified: lawful messages up to 29,245 bytes cannot fit the
registered small units. `link.py` remained byte-for-byte unchanged.

## Quantitative boundary

| Message | Bytes | MTU 64 | 128 | 256 | 512 | 1024 | 1500 | 4096 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| small control | 49 | 5 | 1 | 1 | 1 | 1 | 1 | 1 |
| capacity-10 compact | 797 | 67 | 11 | 4 | 2 | 1 | 1 | 1 |
| capacity-1000 compact | 28,517 | 2,377 | 376 | 140 | 62 | 30 | 20 | 8 |
| max query | 4,146 | 346 | 55 | 21 | 10 | 5 | 3 | 2 |
| ~16 KiB advertisement | 16,105 | 1,343 | 212 | 79 | 36 | 17 | 12 | 4 |
| maximum B2 message | 29,245 | 2,438 | 385 | 144 | 64 | 31 | 21 | 8 |

The maximum-message envelope overhead is 433.496%, 68.456%, 25.604%, 11.380%,
5.512%, 3.734%, and 1.422% at the registered MTUs. The capacity-10 probe's
overhead is 437.139%, 71.769%, 26.098%, 13.049%, and 6.524% for each of the
three one-fragment MTUs. These are protocol-byte measurements, not airtime.

## Adversarial findings

All registered loss locations caused incomplete whole-message delivery and zero
native mutation. Identical duplicates were idempotent; reverse and seeded
orders reconstructed exactly; conflicting duplicates and cross-message mixing
failed closed. Truncation, corrupt CRC, corrupt complete digest, unknown format,
impossible shape, and oversized total length were rejected finitely.

Crashes during reassembly and after reassembly/before apply left the record
missing. A crash after native commit preserved the full record; a fresh contact
then skipped it without persistent ACK state. Both-side restart and the
semantic-blind process mule converged. A 105-record exact workload made progress
over fresh finite processes with zero starvation.

PX13 behavior was preserved through B4: differences 0, 1, and 10 produced
equality/compact decode; 100 and 1,000 produced a delivered capacity failure
and exact fallback. Compact fragment loss was transport failure and did not
trigger fallback. Exact-fallback fragment loss retained only earlier complete
commits.

Three local failures were repaired before closure:

- `C. REASSEMBLY_IMPLEMENTATION_ERROR`: a delayed duplicate after completion
  initially opened a new incomplete reassembly. Bounded volatile
  last-completed identity metadata now suppresses it.
- `A. TEST_HARNESS_ERROR`: the first partial-reassembly fixture accidentally
  selected a one-fragment message. The test now proves the intended boundary.
- `D. FRAGMENT_ACCOUNTING_ERROR`: the relay initially decoded corruption while
  accounting. It now forwards malformed bytes to receiver-owned validation.

No prior-gate correctness defect was found.

## Invariants and limits

Observed zeros: roundtrip mismatches, partial-fragment native mutations, false
reassemblies, cross-message contaminations, unbounded allocations, false
convergence after loss, starved records, oracle mismatches, undetected false
negatives, direct remote-store reads, application/concrete-bearer B4 branches,
and fragmentation-specific D4 branches.

No persistent reassembly, fragment ACK, fragment cursor, peer progress,
adaptive policy, or process session state was introduced. No retry, ARQ, FEC,
PNF1 dependency, real transport, authentication, or encryption was introduced.

Inherited limits remain: all B2/B4 encodings are experimental; process pipes
are not a real bearer; structural digests/CRC are not authentication; no
transport discovery, negotiation, routing, reliability guarantee, or RF result
exists. PX12's historical text/executable discrepancy remains unedited; the
tested implementation is still 64-bit fingerprints and 32-bit checksums.

New measured limits are the 52-byte frame header and its severe tiny-MTU
overhead, minimum MTU 53, maximum 2,438 fragments/message, one incomplete
message per direction, configured rather than negotiated MTU, whole-message
resend on later contacts, and no multiplexing or fragment recovery.
