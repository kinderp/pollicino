# PX11-PN-B2F preregistration

`PX11-PN-B2F` is the candidate identifier supplied by the repository owner.
No authoritative post-PX10 identifier for this experiment exists in the exact
PX10 tree (`9870d9eccf1e583c4d8dd3debe8a1a63caf30575`), so this experiment retains
the supplied name without altering historical roadmap evidence.

## Baseline

- PX10 closure: `9870d9eccf1e583c4d8dd3debe8a1a63caf30575`
- PX9 checkpoint: `c8b8ebcec4414849fc8d72011c45771224caeb3d`
- declared suite: 368 passed, 5 skipped
- focused PX10 B2 suite: 50 passed
- compileall: pass
- worktree before changes: clean

## Hypothesis

For a finite static eligible dataset, repeated finite B2 contacts can
eventually expose and transfer every missing D2/D3 record using only durable
canonical state and current-contact messages. No persistent per-peer
pagination or progress state is required.

## Registered success criteria

```text
STARVED_ELIGIBLE_RECORDS = 0
STARVED_DIRECTION = NONE
DIRECT_REMOTE_STORE_READS = 0
APPLICATION_SPECIFIC_B2_BRANCHES = 0
PERSISTENT_PEER_PROGRESS_AUTHORITIES = 0
PERSISTENT_ACK_STATE_REQUIRED = NO
PERSISTENT_SESSION_STATE_REQUIRED = NO
LOSS_BEFORE_COMMIT_MUTATION = 0
ALREADY_COMMITTED_RECORD_RETRANSFERRED_AS_MISSING = 0
BOUNDED_CONTACT_TERMINATION = YES
STATIC_FINITE_FAIRNESS = PASS
MULTIPAGE_RESTART = PASS
MULE_RESTART = PASS
```

Fairness is tested at 100, 101, 1,000, and 10,000 identities, including a
single lexicographically final missing identity, alternating and sparse gaps,
two-way backlogs, cross-category backlogs, loss, sender uncertainty, restart
after every contact, and a paged mule path. Every convergence loop has an
explicit contact horizon.

## Models to falsify or compare

1. **Canonical prefix replay (PX10):** every fresh contact starts at page zero.
   This is expected to exhibit prefix, direction, or category starvation under
   the 100-attempt ceiling and is retained as the negative control.
2. **Durable-state-derived divergent-page reconciliation:** bounded page-range
   descriptors let a receiver identify pages that differ from its local
   durable state; pages that commit cease to be divergent on a fresh contact.
3. **Ephemeral fair lane scheduling:** current-contact queues rotate among
   direction/category lanes. They are destroyed after contact and are not a
   progress authority.
4. **Persistent per-peer cursor:** rejected unless the kill criterion fires.
5. **Probabilistic/compact reconciliation:** explicitly deferred; correctness
   is established before byte/privacy optimization.

## Kill criterion

If correctness requires durable state equivalent to a peer-keyed cursor,
offset, page, continuation, session journal, ACK ledger, or custody log, stop
without adding it and classify the gate as
`POLLICINO_PERSISTENT_PEER_PROGRESS_REQUIRED`.

## Scope boundaries

This gate adds no real transport, fragmentation, PNF1, retry protocol,
authentication, encryption, routing, custody, TTL/GC, background worker, or
application semantics. Exact identity/digest disclosure and control cost are
measured as limitations; they are not optimized here.
