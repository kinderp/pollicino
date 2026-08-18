# PN-003 — Opaque coordinate -> verified rich-path retrieval

PN-003 tests the central `DISCOVERY` claim of PollicinoNet without binding the core to DNA, LoRa, HTTP, IPFS, BitTorrent or any hosted service.

## Question

Can a scarce link carry only a small opaque rendezvous coordinate while a separate richer path resolves a complete manifest, retrieves an arbitrary object and verifies its exact SHA-256 identity?

The coordinate is **not** content identity and is never accepted as proof. The resolved `PNM1` manifest contains the full 256-bit digest and declared byte length used for final verification.

## Generic components

- `DiscoveryDescriptor` / `PND1`: scarce-link advertisement containing an opaque rendezvous key;
- `ContentManifest` / `PNM1`: complete content identity plus ordered provider-independent retrieval hints;
- `ManifestResolver`: generic coordinate -> encoded manifest port;
- `ContentProvider`: generic opaque-locator -> bytes port;
- `InMemoryResolver` and `InMemoryContentProvider`: standalone reference adapters for the experiment;
- `retrieve_exact`: tries available providers and accepts bytes only when full size and SHA-256 match the manifest.

Neither the core manifest nor the resolver contract knows what an Internet URL, DNA object, CID or torrent is. Future adapters may define those details externally.

## Privacy boundary

A rendezvous coordinate may be scoped or rotated independently of the content identity. Multiple coordinates may resolve to the same full manifest. PN-003 demonstrates this architectural property but does **not** claim that opaque coordinates alone provide anonymity.

## Frozen objects

Two deterministic application-agnostic byte sequences:

1. `small-1k`: 1024 bytes;
2. `large-64k`: 65536 bytes.

Both use a 12-byte opaque coordinate and an 8-byte descriptor authenticator, making the primary PND1 discovery advertisement 45 bytes before any physical-link framing.

## Comparison

For each object record:

- scarce-link PND1 bytes;
- PNM1 manifest bytes delivered on the rich path;
- object bytes delivered on the rich path;
- full SHA-256 verification;
- clean and lossy PN-002 exact-transfer wire cost if the same object had instead been sent entirely through the abstract scarce link.

The exact-transfer comparison is diagnostic. It does not count the rich path as free; it isolates the scarce-link burden, which is the object of the DISCOVERY mode.

## Success criteria

PN-003 succeeds technically if:

1. the full root/scientific suite remains green;
2. every resolved object is byte-for-byte exact and matches the manifest's complete SHA-256;
3. repeated retrieval is deterministic under the frozen in-memory adapters;
4. every primary discovery advertisement is at most 64 bytes;
5. the opaque coordinate is not treated as, or derived by the core from, the content digest;
6. tampered provider content is rejected and a valid later provider may be used as fallback;
7. the primary scarce-link discovery byte count is lower than clean full-object scarce-link transfer for both frozen objects;
8. `pollicino.net` retains zero DNA/radio-SDK/hosted-service runtime dependencies.

No claim is made about real Internet protocol overhead, resolver scalability, DHTs, anonymity, latency, availability or LoRa airtime. Those require later adapters and experiments.
