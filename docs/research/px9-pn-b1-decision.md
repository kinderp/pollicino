# PX9-PN-B1 decision

## Classification

```text
POLLICINO_BEARER_ADAPTER_LOSSY_IN_MEMORY_READY_WITH_LIMITS
```

Confidence: **HIGH** for the deterministic local complete-record model.

Selected contract: one complete bounded D2/D3 record per ephemeral B1 attempt,
with deterministic delivery, drop, duplication, disconnect, bounded temporary
delay, or sender uncertainty. Existing native stores remain the only commit
authority. New contacts derive missing work from durable state.

The kill criterion did not trigger. Persistent contact/session state, ACK
state, peer progress, and custody state are not required. PX3, PX5, PX6, and
PX8 remain valid unchanged; the production change is additive and D4 itself is
unchanged.

Validation: 29 focused PX9 tests passed; the focused D2/D3/D4/PX8/PX9 set
passed 193 with 3 skips; the full declared suite passed 318 with 5 skips;
compileall and parsing of all 11 machine-readable artifacts passed.

## Inherited limits

- bounded D2/D3 stores and records, no TTL/GC or query authentication;
- PX5's POSIX-tested full-snapshot persistence, one authoritative writer per
  directory, and no concurrent-reader contract;
- PX8's complete-record local method calls, linear identifier reconciliation,
  100-item contact cap, and logical—not wire—byte accounting;
- no routing, custody, delivery guarantee, automatic selection/fetch/import,
  or application authority mutation.

## New B1 limits

- complete units are in-process Python objects, not serialized frames;
- the PX8 planner still reconciles directly visible local stores; reconciliation
  metadata is not exchanged through B1;
- deterministic delay is an intra-attempt hold, not time or reordering;
- no bit corruption, truncation, fragmentation, MTU, retry, or ACK protocol;
- attempts and trace entries are capped at 100, duplicate presentation at two,
  and the temporary queue at one;
- the implementation depends on PX8's private deterministic work-plan helpers,
  appropriate for this local gate but not a stable integration API;
- all accounting is experimental model accounting, not airtime or throughput.

## Next experiment

The smallest supported next experiment is to carry reconciliation metadata and
a complete-record encoding across an independently instantiated deterministic
in-memory duplex boundary, then repeat the uncertainty/restart matrix without
direct visibility of the peer store. The repository evidence does not name an
authorized post-PX9 gate for this step, so this report does not invent a gate
identifier and does not implement it. Physical and RF work remains separately
gated.
