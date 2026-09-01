# PX3-PN-D2 didactic explanation

PX2 showed that two different applications need the same kind of small,
bounded address book. PX3 has now put that address book inside Pollicino.

Each entry has only two things:

```text
an opaque byte key -> opaque reference bytes
```

The key answers “which application object?” The value answers “which exact
reference bytes did the application attach to it?” Pollicino checks sizes,
duplicates, conflicts, ordering, and exchange pages. It deliberately does not
open the value and guess what it means.

A FARO-like caller can use a scientific package ID as the key and place its
canonical package pointer inside the value. A different caller can use a
synthetic lawful object ID and a completely different pointer. Both go through
the same class and the same reconciliation methods. There is no switch saying
which caller is active.

That separation matters. Finding a reference in this address book does not say
that a scientific claim is valid or that a publisher is trusted. For another
application it does not grant permission to retrieve, copy, or use anything.
Those decisions still belong to the caller after it receives the exact opaque
bytes.

The catalog is also strict about identity:

- the same key and same value is harmless repetition;
- the same key and a different value is a conflict;
- the catalog never silently picks the newest, most popular, or most repeated
  value.

Three local nodes were tested with different address books. They compared
sorted keys, identified exact missing keys, and pulled only caller-selected new
values. When they eventually held the same six entries, their canonical local
state bytes were identical. This proves deterministic local representation; it
does not prove global agreement or create a registry authority.

In the most discriminating modeled case, sending all 1000 entries cost 550080
modeled bytes. Advertising IDs and pulling the selected 1% cost 39596 modeled
bytes, a 92.802% reduction. This is a bookkeeping model, not a radio or Internet
measurement.

PX3 therefore validates a local generic primitive. It does not add networking,
persistence, automatic retrieval, application trust, or a stable public wire
protocol. The smallest justified next experiment is restart/recovery for a
persistent bounded catalog.
