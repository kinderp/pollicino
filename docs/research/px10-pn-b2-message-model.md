# PX10-PN-B2 experimental message model

The encoding is explicitly:

```text
EXPERIMENTAL_B2_ENCODING = pollicino.experimental-b2.v1
```

It is deterministic evidence for this gate, not a stable public wire protocol.

## Envelope

All integers are unsigned big-endian. The fixed 42-byte envelope is:

```text
magic[4] = PB2E
version[1] = 1
message_type[1]
body_length[4]
sha256(body)[32]
body[body_length]
```

The digest detects accidental alteration; it is not authentication, a MAC, a
signature, trust, or sender identity. Unknown magic, version, type, length,
digest, truncated body, trailing body data, duplicate identity, and bound
violations fail deterministically before native mutation.

## Message types actually required

| Type | Body | Purpose |
|---|---|---|
| `ADVERTISEMENT` | record kind, count, sorted `(identity, digest)` entries | expose bounded local identity state |
| `REQUEST` | record kind, count, sorted identities | ask for advertised missing records |
| `RECORD` | record kind and one complete native record body | deliver one complete D2/D3 record |
| `REFERENCE_SELECTION` | count and sorted D2 keys | express caller-owned explicit D2 selection |

Query and reference identities use a two-byte length followed by bytes. Result
identities use query-ID and result-ID lengths followed by both values. Query,
result, and reference record bodies use bounded length fields matching their
existing native limits. Candidate keys remain opaque D2 keys.

Per-record advertisement digests are SHA-256 over the canonical experimental
record body, excluding the B2 envelope. Sorting in message constructors ensures
that equivalent identity sets encode identically.

## Disclosure

Advertisements reveal exact query IDs or result identity pairs, per-record
digests, page counts, ordering, and approximate set size. Requests reveal which
advertised identities are absent locally. Reference selection reveals selected
D2 keys. Record contents appear only in complete record messages.

This supports exact reconciliation but permits correlation, membership tests,
and possible dictionary inference. It is neither private-set reconciliation nor
confidential discovery. Bloom filters, IBLT, Minisketch, private set
intersection, encryption, and authentication remain deferred.
