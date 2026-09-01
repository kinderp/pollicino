# PX3-PN-D2 local bounded reference catalog contract

Status: PRE-REGISTERED BEFORE NATIVE ACCOUNTING, 2026-09-01

## Scope and ownership

Pollicino owns a bounded local mapping and exact exchange planning. A caller owns
the meaning and canonical construction of both fields:

```text
bounded non-empty logical key bytes
    -> bounded non-empty opaque reference bytes
```

The key identifies the caller's logical object. The opaque value describes how
the caller may locate or interpret its reference. The catalog does not derive a
key by hashing the opaque value and does not parse either field.

This is a validated-local-primitive experiment, not a stable API promise.

## Pre-registered representation and bounds

```text
LOGICAL_KEY_TYPE: bytes
MAX_KEY_BYTES: 256
MAX_REFERENCE_BYTES: 4096
MAX_CATALOG_ITEMS: 10000
MAX_CATALOG_BYTES: 16777216
MAX_EXCHANGE_ITEMS: 100
VARIANT_MODEL: A_SINGLE_OPAQUE_REFERENCE
```

The catalog byte quota counts `len(key) + len(reference)` for every stored
entry. It is model payload accounting, not Python allocator or device-memory
measurement. Smaller injected limits are allowed for deterministic boundary
tests; callers cannot raise a limit above the generic maxima.

Bound decisions:

| Evidence bound | Decision | Rationale |
|---|---|---|
| key, 256 bytes | ADJUST_GENERIC | PX2 had no key bound; a modest byte-key cap is required for deterministic bounded state. |
| reference, 4096 bytes | ADOPT_GENERIC | Both PX2 consumers fit and a reference must remain small. |
| items, 10000 | ADOPT_GENERIC | Bounds local growth without selecting a retention policy. |
| catalog payload, 16 MiB | ADOPT_GENERIC | Bounds model payload independently of item count. |
| exchange page, 100 | ADOPT_GENERIC | Bounds every local exchange planning call and supports paging. |
| retrieval variants, 8 | APPLICATION_ONLY | Only the scientific-package consumer supplied this evidence. |

## Variant decision

Model A is pre-registered. Each key has one canonical caller-owned opaque value.
Any equivalent retrieval alternatives are encoded by the caller inside that
value. Neither independent fixture requires the core to compare or merge
alternatives, so a generic variant collection would add unsupported identity
and quota rules.

## Mutation and state contract

- A new key is added.
- The same key and exact value is an idempotent no-op.
- The same key and different value is an explicit conflict; no overwrite occurs.
- Any type, size, item, payload, or exchange violation fails before mutation.
- Batch pull application is atomic.
- Removal affects only this in-memory catalog mapping.
- Canonical local state sorts entries by byte key and embeds a SHA-256 body
  digest for corruption detection.

The canonical bytes are classified only as:

```text
LOCAL_CANONICAL_STATE_FORMAT
```

They are not a network format, signature, trust statement, or global state.

## Pre-registered accounting threshold

Accounting is labeled `MODEL_PROTOCOL_ACCOUNTING_ONLY`.

Success:

```text
RECONCILE_AND_PULL reduces total modeled exchange bytes by at least 50%
against FULL_REFERENCE_LIST in at least one catalog-size >= 100,
sparse-interest target workload.
```

Kill/defer:

```text
No strategy produces at least a 25% reduction in any size >= 100 workload.
```

The final matrix will use deterministic sizes 10, 100, and 1000; overlaps 0%,
50%, 90%, and 99% where integral; and selection fractions 100%, 10%, and 1%.
No physical or runtime-network measurement is authorized.

