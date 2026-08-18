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

## Scientific result

Successful GitHub Actions run `32184992611`, scientific head `56b0faa5b13d5ddf7bb7f3d9adbb6a005c805f94`:

- **109 root/scientific tests passed in 5.86 s**;
- both frozen objects were retrieved byte-for-byte exactly;
- full SHA-256 matched the resolved manifest in both cases;
- repeated retrieval produced identical reports;
- a second rotating coordinate resolved the same 64 KiB exact manifest;
- artifact `9342131189` (`pn-003-results`);
- artifact digest `sha256:2a0b5046dff4bd2b9d5baa7e4b8c8670303409f58d8437ed7fcbd937232a03a5`.

| Object | Scarce discovery | Rich manifest | Rich content | Clean full scarce fallback | Lossy full scarce fallback |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 KiB | **45 B** | 79 B | 1024 B | 1622 B | 2558 B |
| 64 KiB | **45 B** | 80 B | 65536 B | 102586 B | 140348 B |

The 45-byte discovery advertisement is 2.774% of the clean full-scarce transfer cost for the 1 KiB object and about 0.0439% for the 64 KiB object. Against the frozen lossy fallback it is about 1.759% and 0.0321%, respectively.

This is **not a compression claim**. The object still crosses the richer path: 1024 or 65536 content bytes plus the resolved manifest, before any real rich-network protocol overhead. PN-003 demonstrates that the scarce link can carry a small rendezvous object whose size is decoupled from the bulk content size.

The rotating-alias test reinforces the identity boundary: a second 12-byte coordinate retrieves the same 64 KiB object, while exactness still comes from the unchanged full SHA-256 in the manifest.

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

**All criteria passed.** Tests also cover hash-invalid provider rejection, verified provider fallback, missing-coordinate failure and coordinate rebinding protection.

## Conclusion and boundary

**PN-003 is a positive technical result for standalone DISCOVERY + verified rich-path retrieval.** PollicinoNet can advertise an opaque coordinate on a scarce link, resolve it through a replaceable richer-path adapter and reconstruct an arbitrary object exactly without making the coordinate itself a content hash.

No claim is made about real Internet protocol overhead, resolver scalability, DHTs, anonymity, latency, availability or LoRa airtime. Those require later adapters and experiments. DNA remains an optional consumer of the same generic mechanism.
