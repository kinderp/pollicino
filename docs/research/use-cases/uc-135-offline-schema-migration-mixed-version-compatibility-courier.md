# UC-135 — Offline Schema Migration and Mixed-Version Compatibility Courier

## Idea

Roll out a new data or message schema across disconnected nodes without assuming they upgrade at the same time. Each node advertises the schema versions it can read and write, and migrations remain explicit until the old compatibility window can safely close.

## Problem solved

IoT boards, Raiatea workers and student laptops may remain offline for days. A rollout can therefore leave old producers on schema v1 while newer consumers expect v2, with historical v1 records still present in caches.

PollicinoNet needs a safe answer when an older node reconnects: exchange compatible data, supply a declared migration path, keep the old side read-only, or mark the pair incompatible.

## Actors / nodes

Schema publisher, producers, consumers, local stores, migration worker, student relay/store-and-forward nodes and optional Raiatea corpus or index nodes.

## Why PollicinoNet fits

Schema IDs, hashes, compatibility mode and migration plans are tiny compared with datasets. LoRa can carry capability and version summaries while actual record batches or migration bundles use richer bearers.

The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: schema ID and hash, readable and writable versions, migration-needed status and deprecation epoch.
- BLE: nearby schema or migration bundle exchange.
- Wi-Fi/LAN: record batches, migration packages and validation reports.
- Internet: optional schema-registry fast path.
- Physical transport: laptop or removable storage for larger historical datasets.

## What we can test now in software

Define v1, v2 and one intentionally incompatible v3 for a small sensor or Raiatea record.

Test backward-compatible field addition, an old consumer receiving new data, a new consumer reading old data, transitive versus previous-version compatibility, a node returning after the compatibility window, interrupted migration, rollback to an older application and schema hash mismatch.

Useful outcomes include READ_ONLY_OLD, MIGRATION_REQUIRED, INCOMPATIBLE and UNKNOWN.

Measure successful decode and migration, quarantined records and extra bytes moved. Schema compatibility must not be treated as proof of semantic correctness.

## What requires real hardware

Use 4–6 boards or laptops running deliberately different firmware or application versions. Let v1 and v2 coexist, disconnect one old node, migrate the others, then reconnect it later.

The useful physical result is whether the mixed-version interaction follows the declared compatibility policy. No radio-performance claim is implied.

## Messina teaching scenario

Student groups in different coarse islands run sensor loggers or Raiatea mini-corpora on different schema versions. A v2 rollout starts at school while one group remains disconnected.

When that group later reconnects through a relay, PollicinoNet identifies its version and either exchanges compatible data, supplies a migration bundle or returns INCOMPATIBLE.

## Privacy / security

Authenticate schema and migration publishers; bind migrations to exact source and target schema hashes; preserve original records until validation succeeds; minimize data samples in compatibility reports; and require an explicit trusted migration package.

## Difficulty

Medium-high. Compatibility rules are understandable; mixed-version rollout, rollback and interrupted migration make the distributed case substantial.

## Why this is distinct

UC-115 maps different vocabularies or schemas between corpora. UC-117 validates data against rules. UC-135 manages temporal evolution of one contract across mixed software versions, including upgrade order and migration state.

## Research / implementation signal

Production schema systems distinguish backward, forward, full and transitive compatibility precisely because producers and consumers do not upgrade atomically. PollicinoNet extends that mixed-version period across long partitions.

References:

- https://docs.confluent.io/platform/7.7/schema-registry/fundamentals/schema-evolution.html
- https://avro.apache.org/docs/current/specification/
