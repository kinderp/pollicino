# PN-005 — Content-addressed P2P chunk store

PN-005 tests whether verified receiver-side state can reduce scarce-link traffic without changing exact reconstruction. It remains standalone: no DNA, LoRa SDK, hosted resolver or application schema is required.

## Question

When two peers share a content-addressed chunk store, how does total scarce-link traffic change as the receiver already owns a larger fraction of the exact chunks needed for an object?

## Generic mechanism

- `PollicinoStore`: SHA-256-addressed verified chunks;
- `PCM1`: deterministic fixed-size chunk manifest with full object SHA-256 and one full SHA-256 per chunk;
- `PNA1`: compact availability bitset bound to the complete PCM1 manifest fingerprint;
- missing chunks only: the sender transmits a small chunk-index prefix plus the exact missing chunk bytes through PN-002 PNF1 framing;
- final object reconstruction from the receiver store with full SHA-256 verification.

Identical chunk content is addressed once regardless of which object position references it.

## Accounting boundary

Two deployment cases are measured separately:

1. **manifest-on-scarce** — PCM1 itself is transferred through the scarce link, then PNA1 returns receiver availability, then only missing chunks cross;
2. **manifest-pre-resolved** — the receiver already obtained PCM1 through a PN-003-style richer path; scarce traffic therefore contains PNA1 plus only missing chunks.

The second case does not treat the manifest as free: it is simply outside the scarce-link byte count and would belong to the rich-path side of TRC.

## Frozen object

- 8192 bytes total;
- 16 deterministic, deliberately unique 512-byte chunks;
- fixed-size chunking only for this first store experiment.

Content-defined chunking and delta/patch coding are intentionally deferred.

## Frozen cache levels

Receiver starts with the first:

- 0 / 16 chunks = 0%;
- 4 / 16 chunks = 25%;
- 8 / 16 chunks = 50%;
- 12 / 16 chunks = 75%;
- 16 / 16 chunks = 100%.

All transfers use the PN-002 clean 64-byte profile so PN-005 isolates the effect of cache state instead of mixing it with packet loss. A direct PNF1 transfer of the complete object is measured as the no-cache reference.

## Success criteria

PN-005 succeeds technically if:

1. the full root/scientific suite remains green;
2. every cache level and manifest mode reconstructs the exact object and full SHA-256;
3. missing source bytes and missing chunk count decrease monotonically with cached state;
4. missing-chunk wire bytes decrease strictly at each 25% cache increment;
5. 100% cache requires zero chunk-payload transfer;
6. manifest-pre-resolved mode transfers zero PCM1 bytes on the scarce link;
7. at each cache level, pre-resolved scarce traffic is no greater than manifest-on-scarce traffic;
8. by 25% cached state, total manifest-on-scarce traffic is already lower than direct full-object PNF1 transfer for this frozen object;
9. PNA1 is bound to the exact PCM1 fingerprint and malformed summaries/manifests fail closed;
10. the core retains zero DNA/radio-SDK/application runtime dependencies.

A positive result is about deduplication/shared state, not compression of unseen random data.
