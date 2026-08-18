# PN-001 — Standalone discovery wire

PN-001 starts PollicinoNet from a strict dependency rule:

> **PollicinoNet must be useful without DNA, Travel DNA, LoRa hardware, an Internet service, or a learned model.**

DNA is the first application integration, not a dependency of the core.

## Question

Can a tiny deterministic, application-agnostic discovery descriptor provide a useful baseline for scarce-link rendezvous before we add domain-specific adapters or neural compression?

## PND1 primitive

`pollicino.net.DiscoveryDescriptor` encodes only generic transport/reconstruction hints:

- version;
- application-defined object class;
- generic flags;
- capability bit mask;
- TTL;
- hop limit;
- nonce;
- rendezvous key;
- opaque application metadata;
- optional authenticator.

The core assigns no meaning to object class, flags, capability bits or metadata. An application adapter may define those mappings externally.

The fixed PND1 header is 25 bytes. Variable key, metadata and authenticator bytes follow it exactly; no padding or text representation is used.

## Standalone fixtures

The first benchmark uses only generic examples:

1. a file/content coordinate;
2. a message/topic coordinate;
3. a service/resource coordinate.

For each fixture compare:

- compact PND1 bytes;
- canonical JSON representation;
- zlib-9 over canonical JSON.

The comparison is intentionally modest: PN-001 is establishing a deterministic wire baseline, not claiming a universal compressor win.

## DNA compatibility comes second

A later PN-001B adapter will map real `DNATrace v0.1` semantics onto the generic fields and opaque metadata. That adapter may depend on the DNA schema; `src/pollicino/net/` must not.

## Exit criteria

- deterministic encode/decode round trip;
- no external runtime dependencies;
- no imports from DNA or a radio SDK;
- all generic fixtures round-trip exactly;
- persist byte counts for PND1, JSON and zlib;
- application-specific integration remains outside the core package.
