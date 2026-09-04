# PX10-PN-B2 preregistration

`PX10-PN-B2` is a candidate identifier supplied by the repository owner for
this experiment. The exact PX9 decision describes this next experiment but
does not assign it a gate number; no later repository evidence supplied an
authoritative replacement name.

Baseline: exact PX9 closure
`c8b8ebcec4414849fc8d72011c45771224caeb3d`, preserved locally as
`checkpoint/px9-pn-b1` without modifying its contents.

## Hypothesis

Independent endpoints can converge using only bounded experimental B2
reconciliation metadata and complete-record messages over a B1 bearer.
Remote store visibility is not required. Receiver durable D2/D3 state remains
the sole possession and progress authority.

## Candidate models

1. **Paged identity-plus-digest advertisement, request, complete record.** Each
   endpoint constructs messages from only its local store. Digests allow a
   known identity with conflicting content to fail closed without transferring
   all known records. Select this only if the adversarial matrix passes.
2. **Whole-state snapshot exchange.** Rejected provisionally because it is
   unnecessarily revealing, defeats bounded pagination, and duplicates native
   persistence formats.
3. **State digest only.** Rejected provisionally because inequality does not
   identify missing records or detect which identity conflicts.
4. **Probabilistic/private set reconciliation.** Deferred unless exact bounded
   pages fail a registered correctness requirement.

The existing PX9 object bearer cannot carry control metadata as bytes. The
candidate therefore adds a thin experimental complete-message B1 adapter in
the new B2 layer, reusing only PX9 impairment actions. It does not change PX9,
introduce frames, or claim a stable wire protocol.

## Success criteria

```text
DIRECT_REMOTE_STORE_READS = 0
APPLICATION_SPECIFIC_B2_BRANCHES = 0
PERSISTENT_ACK_STATE_REQUIRED = NO
PERSISTENT_SESSION_STATE_REQUIRED = NO
LOSS_BEFORE_COMMIT_MUTATION = 0
SENDER_UNCERTAINTY_RETRANSFER_AFTER_RESTART = 0
CONFLICTS_FAIL_CLOSED = YES
PERMANENT_LOSS_FALSE_CONVERGENCE = NO
BOUNDED_CONTACT_TERMINATION = YES
MULTIPAGE_RECONCILIATION = PASS
MULE_RESTART = PASS
```

All advertisements, requests, and records must be encoded bytes crossing the
message-bearer attempt boundary. Test code may inspect both endpoint states for
assertions, but production planning may not.

## Preregistered bounds

- at most 100 identities in one advertisement or request;
- deterministic maximum encoded-message size derived from existing D2/D3
  record and identity limits;
- explicit control-message, control-byte, record-message, record-byte, total
  bearer-attempt, and diagnostic-trace budgets per contact;
- one complete encoded B2 message per bearer attempt;
- no automatic retry loop and no cross-contact queue.

## Kill criterion

If correctness requires direct peer-store access or a persistent ACK, session
cursor, peer journal, custody log, or other second progress authority, stop.
Classify the durable-state reconciliation hypothesis as falsified rather than
adding that state silently.
