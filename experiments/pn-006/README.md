# PN-006 — Optional DNA Trace integration

PN-006 is the first application integration built on the standalone PollicinoNet core. DNA is **not** moved into `pollicino.net`; the adapter lives under `pollicino.integrations.dna` and depends one-way on generic network contracts.

## Frozen external contract

The adapter targets `kinderp/dna` `DNATrace v0.1` as frozen in `dna-contract-provenance.json`:

- DNA main commit `01ba2b4d381168566cc3e47c9bda8045897adc0f`;
- schema blob `bbb2dcdce06935d2de51504bd9a7ad38ca76efba`;
- `schemas/v0.1/dna-trace.schema.json`.

No DNA package, checkout or service is required at Pollicino runtime.

## Two delivery profiles

### Inline

A compact, canonical DNATrace can be represented directly inside PND1 integration metadata. The generic core still sees only opaque `object_class`, flags, capability mask, TTL, nonce, coordinate, metadata and authenticator.

Inline is accepted only when:

- timestamps use canonical whole-second UTC `...Z` representation;
- the complete DNA-specific metadata fits PND1's 64-byte opaque metadata field;
- the DNATrace authenticator fits PND1's 32-byte authenticator field;
- no distinct radio authenticator is requested.

The receiver reconstructs the normalized DNATrace directly with no rich-path content fetch.

### Reference

If inline would lose information or exceed the generic limits, the adapter emits a small PND1 reference descriptor. The complete canonical DNATrace JSON is placed behind a generic PNM1 manifest and retrieved through PN-003 exact-content verification.

Reference mode is therefore the fail-safe compatibility path, not an error condition.

## Privacy boundary

The caller supplies the PND1 rendezvous coordinate. The adapter does not derive it from the DNATrace hash or identity. A production DNA integration can therefore rotate/scope coordinates according to application privacy policy.

Opaque/scoped coordinates do not by themselves guarantee anonymity.

## Frozen fixtures

1. `compact-travel` — canonical UTC, small IDs, one domain, two intents, Internet+LoRa rendezvous: expected inline;
2. `large-multidomain` — all current domains/capabilities, 16 intents and long fields: expected reference;
3. `offset-time` — small trace but timestamps expressed with `+02:00`: expected reference to preserve the authoritative representation instead of silently normalizing it inline.

## Baselines and accounting

For each fixture record:

- canonical DNATrace JSON bytes;
- zlib-9 over canonical JSON;
- PND1 descriptor bytes;
- PNF1 wire bytes needed to deliver that descriptor over the clean PN-002 scarce profile;
- PNF1 wire bytes needed to send canonical JSON directly over the same scarce profile;
- rich PNM1/content bytes for reference cases;
- exact normalized trace round-trip.

Reference mode moves authoritative trace bytes to the rich path; that is not a compression claim.

## Success criteria

PN-006 succeeds technically if:

1. the full root/scientific suite remains green;
2. importing `pollicino.net` alone does not import the DNA integration module;
3. `compact-travel` is inline and round-trips to the identical normalized `DNATraceV01`;
4. `large-multidomain` and `offset-time` use reference mode and retrieve the exact canonical JSON through full PNM1 SHA-256 verification;
5. all PND1 descriptors are smaller than their canonical DNATrace JSON representations;
6. all descriptor scarce-wire costs are lower than direct canonical-JSON scarce transfer costs for the frozen fixtures;
7. malformed DNA mappings/base64 and misuse of inline/reference decoding fail closed;
8. the caller-provided coordinate remains independent of content identity;
9. `pollicino.net` retains zero DNA runtime dependency.

Travel DNA, GeoRoom and DNAFragment integration remain separate follow-up use cases; PN-006 validates only the DNATrace discovery boundary.
