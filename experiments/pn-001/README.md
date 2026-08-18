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

The comparison is intentionally modest: PN-001 establishes a deterministic wire baseline, not a universal compressor claim. Specialized compact formats such as CBOR/MessagePack are deferred to a follow-up baseline.

## Scientific result

Successful GitHub Actions run `32183486241`, scientific head `22bca9b1619d838886ea5877afbbc2a21a0df121`:

- **96 root/scientific tests passed in 5.79 s**;
- all three PND1 fixtures round-tripped exactly;
- artifact `9341613027` (`pn-001-results`);
- artifact digest `sha256:94a41d6acea5a642c21634f8b97ab2669894249e5a9597d20f746a2dc9272005`.

| Fixture | PND1 | canonical JSON | JSON + zlib-9 |
| --- | ---: | ---: | ---: |
| file coordinate | **41 B** | 188 B | 151 B |
| message coordinate | **50 B** | 205 B | 165 B |
| service coordinate | **73 B** | 252 B | 174 B |
| **mean** | **54.67 B** | 215.00 B | 163.33 B |

PND1 is smaller than canonical JSON on 3/3 frozen fixtures and also smaller than zlib-compressed JSON on 3/3. Mean size is about 74.6% below canonical JSON and about 66.5% below zlib-9 JSON for these fixtures.

These numbers are specific to the frozen descriptors and do not establish superiority over compact schema-aware formats generally.

## Provenance note

An earlier PR-triggered run (`32183347938`) failed during test collection because the workflow invoked repository-wide `pytest -q`, which also collected the separate course activity harnesses. Those labs expect execution from their own directories and some have optional teaching dependencies. PN-001 itself did not execute and no result artifact was produced in that run.

The successful run corrected only test scope/dependencies: the scientific/root suite is `tests/`. No PN-001 fixture, wire format or benchmark policy was changed in response to result data.

## DNA compatibility comes second

A later adapter can map real `DNATrace v0.1` semantics onto the generic fields and opaque metadata. That adapter may depend on the DNA schema; `src/pollicino/net/` must not.

## Conclusion

**PN-001 is a positive technical result for the standalone contract.** It provides a deterministic, zero-application-dependency discovery primitive and a compact baseline suitable for the next scarce-link experiments.

The next step is not to bind the core to DNA. PN-002 should first add a generic impaired-link simulator and framing/retry accounting; DNA fixtures and the real LoRa hardware can then plug into those generic contracts as optional integrations.
