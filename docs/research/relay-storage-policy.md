# Relay storage policy: quota, retention and garbage collection

PollicinoNet relays are allowed to keep verified data across disconnected contacts, but a real relay cannot keep everything forever. This note defines the first deterministic local storage policy.

## Functional goal

A relay may dedicate only a bounded amount of local storage to PollicinoNet. The relay keeps a catalog of active bundles and the PCM1 manifest/chunks each bundle references. Garbage collection then removes data only when it is no longer justified by any active bundle.

This is especially relevant for a future student network: a board/gateway/laptop may participate as a relay without giving PollicinoNet unlimited disk space.

## Policy

`RelayStoragePolicy` currently has two independent limits:

- `max_store_bytes`: maximum bytes that the relay wants the managed content-addressed store to occupy;
- `retention_seconds`: maximum local retention from the most recent registration of a bundle.

Bundle TTL remains a hard protocol boundary. Local retention can shorten TTL, never extend it.

```text
local retain-until = min(bundle TTL expiry, local retention expiry)
```

## Garbage-collection order

The collector is deterministic:

1. remove catalog entries whose retention/TTL has expired;
2. remove corrupt addressed files, because they are not valid custody;
3. remove valid store objects that no active bundle references;
4. if the store is still above quota, evict the oldest unpinned bundle;
5. repeat reference-aware cleanup until under quota or only pinned bundles remain.

A shared chunk survives if at least one active bundle still references it.

## Pinned bundles

A bundle can be marked `pinned` to protect it from quota eviction. Pinning does **not** override TTL or retention expiry.

If pinned data alone exceed the configured quota, PollicinoNet reports `over_quota_bytes` rather than silently deleting protected data.

## Custody

Garbage collection may remove a bundle that the local custody ledger previously recorded. When a ledger is supplied, collection returns a pruned ledger with local custody records removed for bundles that were actually dropped.

Processed contact IDs remain recorded so replaying an old contact remains idempotent.

## Crash persistence

The relay catalog is persisted as canonical JSON inside a checksummed envelope using the same atomic-write primitive as durable exact-session state:

```text
temporary file -> fsync -> atomic replace
```

The checksum detects accidental corruption; it is not an authentication mechanism against a hostile local writer.

## Physical-test boundary

No radio hardware is required to validate quota, retention, reference tracking or garbage collection. They are local storage/protocol properties.

Physical HW-006 measurements become relevant later when storage policy is coupled to measured contact opportunities, for example deciding to retain a large bundle because the next real LoRa contact may be rare. Until then such decisions must remain synthetic policy experiments.
