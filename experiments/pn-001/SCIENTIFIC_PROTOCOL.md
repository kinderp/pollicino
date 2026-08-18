# PN-001 scientific protocol — standalone discovery wire

PN-001 is the first executable PollicinoNet experiment.

## Primary invariant

Pollicino and PollicinoNet must remain independently usable without DNA, Travel DNA, a LoRa SDK, a hosted resolver, a learned checkpoint, PyTorch or MLX.

DNA is an optional application integration. It is deliberately excluded from the PN-001 core implementation and primary fixtures.

## Frozen wire candidate

`PND1` is a transport- and application-agnostic discovery descriptor with:

- magic/version;
- opaque object class;
- opaque flags;
- generic capability mask;
- TTL;
- hop limit;
- opaque rendezvous key;
- opaque metadata;
- optional authenticator;
- nonce.

The core assigns no domain meaning to those fields.

## Primary fixtures

Three generic cases are frozen before any DNA adapter is introduced:

1. file coordinate;
2. message coordinate;
3. service coordinate.

## Baselines

For each fixture compare:

- canonical JSON representation;
- zlib level 9 over canonical JSON;
- PND1 deterministic binary representation.

CBOR/MessagePack and the real DNATrace integration are deliberately deferred to a follow-up phase because PN-001 first establishes the zero-dependency standalone contract.

## Success criteria

PN-001 succeeds technically if:

1. every fixture round-trips exactly;
2. encoding is deterministic;
3. invalid/truncated encodings fail closed;
4. the full existing Pollicino test suite remains green;
5. `pollicino.net` has no runtime dependency on DNA or radio SDKs;
6. PND1 is smaller than canonical JSON for all frozen fixtures.

No claim is made yet about LoRa airtime, real radio reliability, anonymity, or superiority over specialized encodings such as CBOR. Those belong to later PN experiments.
