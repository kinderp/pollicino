# PX3-PN-D2 genericity audit

Audit target: [catalog.py](../../src/pollicino/net/catalog.py)

## Dependency and placement result

```text
generic namespace: pollicino.net.catalog
top-level pollicino export added: NO
pollicino.net re-export added: NO
new dependency: NO
optional integration import: NO
PollicinoStore import: NO
PR #52 import/cherry-pick/merge: NO
network/runtime import: NO
```

The module imports only `dataclasses`, `enum`, `hashlib`, `struct`, and `typing`.

## Semantic scan

The generic core was searched case-insensitively for the forbidden fixture and
domain terms required by the Gate. Result:

```text
forbidden semantic token matches: 0
APPLICATION_SPECIFIC_CORE_BRANCHES = 0
```

Tests and reports intentionally name the two fixtures and are outside the core.

## Two-consumer matrix

| Property | FARO-like sanitized fixture | CONTENT-like lawful fixture |
|---|---|---|
| Generic type | `BoundedReference` | `BoundedReference` |
| Generic catalog | `BoundedReferenceCatalog` | `BoundedReferenceCatalog` |
| Key | caller-owned synthetic package-ID bytes | caller-owned synthetic object-ID bytes |
| Value | canonical opaque pointer bytes | opaque coordinate/token bytes |
| Core parsing | none | none |
| Core branch | none | none |
| External runtime/dependency | none | none |
| External contact/download | none | none |
| Authority inferred | none | none |

The FARO-like opaque value deliberately contains two retrieval alternatives.
Their construction and compatibility are caller-owned; the core stores one
opaque value and therefore does not acquire a generic alternative-set model.

## Authority audit

The core stores no publisher, provider count, source count, ranking, trust,
authorization, validation, ownership, timestamp, popularity, or operator
identity. Repeated arrivals do not change state. State digest and snapshot mean
only “these local canonical bytes,” never application or global truth.

## Privacy and key-material audit

Fixtures contain only deterministic synthetic IDs and opaque tokens. Scans found
no usernames, hostnames, absolute personal paths in committed artifacts, IP/MAC
fixtures, secret assignments, PEM headers, private keys, or seed phrases.

Machine-readable evidence is in
[genericity-matrix.json](../../experiments/px3-pn-d2/genericity-matrix.json).
