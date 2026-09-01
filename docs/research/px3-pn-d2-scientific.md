# PX3-PN-D2 scientific report

Status: PASS, local/software-only, 2026-09-01

## Hypothesis

A small mapping from bounded caller-supplied byte keys to bounded opaque byte
references can be a generic Pollicino primitive if it remains deterministic,
fail-closed, application-blind, and useful across independent local nodes and
two materially different fixtures.

The pre-registered success threshold was a reduction of at least 50% for exact
`RECONCILE_AND_PULL` against `FULL_REFERENCE_LIST` in at least one size >= 100
sparse-selection workload. The kill/defer threshold was no reduction of at
least 25% in any such workload. See [the frozen contract](px3-pn-d2-contract.md).

## Reproducibility boundary

```text
original checkout branch: main
original checkout HEAD: 750405a4aba86e7335141383396edf84347fc1d8
original checkout status: clean

worktree: /private/tmp/pollicino-px3-pn-d2
branch: pollicino/px3-pn-d2-bounded-reference-catalog
base: 750405a4aba86e7335141383396edf84347fc1d8

origin/main observed: 750405a4aba86e7335141383396edf84347fc1d8
PR #52 head observed read-only: be8bf8a8f3f9410efd3c82deaacd2f9917709f80
documentation checkpoint: 7f6457427b68ec8145f992fb0bf81cade94e1e38
implementation commit: 5fd578ac54a223892ddaa692119606d9e99d151b
```

The six required research documents were read with `git show` from the exact
documentation checkpoint. That branch was not merged or cherry-picked. PR #52
was not fetched, merged, imported, or called.

## Baseline

The environment initially lacked `pytest`; an ignored worktree-local virtual
environment was created and only the declared test dependency was installed.

The declared pinned root suite was then run as `pytest -q tests` with `src` on
`PYTHONPATH`:

```text
BASE_TESTS_PASS: 125
BASE_TESTS_FAIL: 0
BASE_TESTS_SKIP: 2
```

A raw repository-wide `pytest` was also attempted. It collected course activity
directories outside the declared root suite and stopped with 58 collection
errors (`main` activity imports and optional Torch), plus one skip. This is the
same optional/course boundary anticipated by the Gate and is not hidden as a
passing suite.

## Native implementation

The implementation is [catalog.py](../../src/pollicino/net/catalog.py). It uses
only Python standard-library types and adds no top-level `pollicino` or
`pollicino.net` re-export.

The contract is:

```text
BoundedReference(bytes logical_key, bytes opaque_reference)
BoundedReferenceCatalog
CatalogLimits
reconcile_and_pull(...)
```

The caller constructs canonical byte keys and opaque references. The catalog
does not hash the reference to define caller identity and does not inspect
either field. Model A was selected: one opaque value per key. Retrieval
alternatives, when required, remain inside the caller's canonical opaque value.

### Generic bounds

| Bound | Value | PX3 decision |
|---|---:|---|
| logical key | 256 bytes | ADJUST_GENERIC; new defensive byte-key bound |
| opaque reference | 4096 bytes | ADOPT_GENERIC |
| catalog items | 10000 | ADOPT_GENERIC |
| catalog model payload | 16777216 bytes | ADOPT_GENERIC |
| exchange page | 100 items | ADOPT_GENERIC |
| retrieval alternatives | no generic collection | APPLICATION_ONLY |

Catalog payload is exactly the sum of key and opaque-reference lengths. It is
not a claim about Python heap size or hardware capacity.

### Mutation and identity results

```text
new key/value: ADDED
same key/exact value: NOOP_DUPLICATE
same key/different value: ReferenceConflictError
last-write-wins: absent
majority/source arbitration: absent
```

Single and batch mutations stage their complete result before replacing local
state. Key, reference, item, byte, and exchange failures leave the prior state
and digest unchanged. Tests exercise the true default limits at exactly 256 and
4096 bytes per field, 10000 catalog items, 16 MiB catalog payload, and 100
exchange items, plus one-over rejection.

Removal only removes a local mapping. A test stores an independent object in
`PollicinoStore`, removes its reference from the catalog, and verifies the store
object remains present.

## Canonical local state

The catalog has a versioned, length-delimited, insertion-order-independent local
state encoding. Entries sort by raw byte key. The header contains the item
count, model payload count, and SHA-256 of the encoded body. Decoding rejects:

- unsupported version or bad magic;
- duplicate keys;
- truncated headers or values;
- trailing data;
- payload-count mismatch;
- body-digest mismatch;
- declared or encoded quota overflow.

Two processes and independently ordered instances produce identical bytes for
equal logical state. The format is classified only as:

```text
LOCAL_CANONICAL_STATE_FORMAT
```

Its digest is a deterministic integrity helper, not trust, authenticity,
publisher authority, or global truth. No network-visible format was created.

## Two-consumer evidence

The focused suite constructs both fixtures as `BoundedReference` and inserts
them into the exact same `BoundedReferenceCatalog` class:

1. A sanitized FARO-like fixture uses a synthetic package ID as its byte key
   and canonical opaque pointer bytes containing two caller-owned retrieval
   alternatives. Provenance is FARO PX2 final closure
   `6edf1f7d6f3ff91e07822a28910e7335958e1da3`. It imports no FARO code and copies
   no scientific evaluation logic.
2. A CONTENT-like fixture uses a distinct synthetic opaque identity and lawful
   coordinate token. It contacts no provider and implements no retrieval
   system semantics.

The core's static audit found zero forbidden semantic token matches and zero
optional-integration imports:

```text
APPLICATION_SPECIFIC_CORE_BRANCHES = 0
```

No fixture presence changes trust, authorization, validity, recommendation, or
ownership. No source/provider count is stored.

## Local multi-node evidence

Three independent catalogs began with different state digests:

```text
A: {0, 1, 2}
B: {2, 3, 4}
C: {4, 5, 0}
```

Bounded local method-call exchanges ran in order `A<->B`, `B<->C`, `A<->C`.
No singleton or shared backing mapping existed. Divergence was valid initially;
after exact exchange all nodes held six entries and had the same state digest:

```text
304851c725938da67de9f51a72311a495f1876699592d348954e1f51ce3b90e9
```

This is deterministic convergence of equal local states, not consensus.
Details are in [the multi-node matrix](px3-pn-d2-multi-node-matrix.md) and
[machine-readable fixture](../../experiments/px3-pn-d2/multi-node-fixtures.json).

## Exchange strategies and accounting

All five simple exact roles were implemented or modeled:

| Strategy | Role | Complexity | Delivers selected new references? |
|---|---|---|---|
| `FULL_REFERENCE_LIST` | bounded pages of all entries | O(n log n) ordering | yes, plus duplicates/irrelevant values |
| `SORTED_IDS` | deterministic advertisement | O(n log n) | no; planning control only |
| `RECEIVER_KNOWN_IDS` | exact known comparison | O(n + m) after ordering | yes, all unknown values |
| `PULL_SELECTED` | direct pull when keys already known | O(k log k) | yes |
| `RECONCILE_AND_PULL` | advertise, exact difference, caller selection, pull | O(n log n + k log k) | yes |

All have no new parser, persistent state, dependency, or network format.

The deterministic matrix covers sizes 10, 100, and 1000; 0%, 50%, 90%, and 99%
overlap where integral; and 100%, 10%, and 1% selection. Every row records
control, logical-ID, reference, duplicate, irrelevant, and total modeled bytes,
plus reference counts.

Target result:

```text
catalog size: 1000
overlap: 0%
selection: 1%

FULL_REFERENCE_LIST: 550080 modeled bytes
RECONCILE_AND_PULL:   39596 modeled bytes
reduction:            92.801774%
threshold:            >= 50%
result:               PASS
```

`PULL_SELECTED` is cheapest (5516 bytes) only when desired keys are already
known; it cannot discover an unknown catalog. `SORTED_IDS` is the simplest
advertisement but does not deliver values. For unknown-catalog discovery with
selected delivery, `RECONCILE_AND_PULL` is therefore the native winner. Exact
lists already cross the threshold, so minisketch, IBLT, Bloom, and Cuckoo
structures remain unjustified and deferred.

All figures are:

```text
MODEL_PROTOCOL_ACCOUNTING_ONLY
```

No latency, rate, energy, airtime, or scalability claim is made.

## Validation

```text
focused PX3: 43 passed
full declared suite: 168 passed, 2 skipped
compileall: PASS
git diff --check: PASS
genericity scan: PASS / 0 core matches
privacy scan: PASS
private-key scan: PASS
runtime network: NOT_USED_BY_DESIGN
performance benchmark: NOT_RUN_BY_DESIGN
```

The final scan commands and closure commit are reported in
[the decision record](px3-pn-d2-decision.md).

## Negative results and limitations

- The FARO-side limit of eight retrieval alternatives was not generalized.
- No query language, ranking, popularity, source count, time, TTL, or retention
  policy was needed.
- No persistence was added; state decoding proves format safety, not restart
  durability or atomic filesystem recovery.
- No stable public API or stable wire protocol is claimed.
- No runtime, bearer, custody, routing, radio, Internet, or external retrieval
  path was used.

## Classification and next Gate

```text
POLLICINO_BOUNDED_REFERENCE_CATALOG_LOCAL_READY
confidence: HIGH
```

The evidence supports exactly one next Gate:

```text
PN-D2R — Persistent Bounded Reference Catalog Restart/Recovery
```

All network carriage, runtime integration, public distribution, automatic
fetch/import/trust/recommendation, and advanced reconciliation remain blocked.
