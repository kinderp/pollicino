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
- domain and rendezvous-capability arrays are already in deterministic code order, because PND1 bit masks preserve membership but not arbitrary array order;
- the complete DNA-specific metadata fits PND1's 64-byte opaque metadata field;
- the DNATrace authenticator fits PND1's 32-byte authenticator field;
- no distinct radio authenticator is requested.

If any representation detail would be lost, the adapter uses reference mode instead of silently normalizing the authoritative trace.

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

The fixtures, coordinates, link profile and expected modes were frozen before the final correctness rerun.

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

## Scientific result

Final successful GitHub Actions run `32187579277`, scientific branch head `ed29dd394407204fb06fda2a4cb39af576f1f11f`:

- **129 root/scientific tests passed in 6.56 s**;
- `import pollicino.net` remains independent of the DNA integration;
- all three frozen fixtures used the preregistered mode and round-tripped exactly;
- artifact `9343035464` (`pn-006-results`);
- artifact digest `sha256:3ecbd6f98ed2d7355daa95750b467d9d8dd3ee9e67d9ae6095b4a72c4b8b059c`.

| Fixture | Mode | Canonical JSON | zlib-9 JSON | PND1 | PND1 scarce wire | Direct JSON scarce wire | Rich manifest/content |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| compact-travel | inline | 302 B | 222 B | **91 B** | **143 B** | 484 B | 0 / 0 B |
| large-multidomain | reference | 580 B | 313 B | **51 B** | **103 B** | 918 B | 83 / 580 B |
| offset-time | reference | 271 B | 198 B | **50 B** | **102 B** | 427 B | 77 / 271 B |

The scarce-link descriptor costs are about 29.5%, 11.2% and 23.9% of direct canonical-JSON scarce transfer for the three frozen fixtures. The reference rows are deliberately not treated as compression of the DNATrace: their complete authoritative JSON bytes move through the richer path and are verified against the full PNM1 SHA-256.

A prior green run (`32187201915`, 127 tests) was superseded before merge. Review found that inline bit masks could preserve set membership while normalizing a valid noncanonical JSON array order. The adapter was tightened to force reference mode in that case, two regression tests were added, and the unchanged scientific fixtures were rerun. The measured PN-006 rows remained unchanged.

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

**All frozen criteria passed.** Additional regression tests now force reference mode whenever bit-mask inline encoding would lose the original domain or capability array ordering.

## Conclusion and boundary

**PN-006 is a positive technical result for an optional DNA discovery adapter.** A compact DNATrace can travel inline when its representation is provably reversible; otherwise the same standalone PollicinoNet primitives carry a small reference and retrieve the authoritative trace exactly over a richer path.

PollicinoNet remains usable on its own. Travel DNA, GeoRoom, DNAFragment/ConsentGrant integration and real LoRa hardware remain separate follow-up layers.
