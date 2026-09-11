# PX11-PN-B2F scientific report

## Question

Can repeated finite independent-endpoint contacts eventually expose every
eligible missing record without keeping a durable peer pagination cursor?

The exact PX10 closure was
`9870d9eccf1e583c4d8dd3debe8a1a63caf30575`. Its declared suite reproduced at
368 passed and 5 skipped; all 50 focused B2 tests and compileall passed. No
later authoritative gate identifier was present, so the repository-owner
candidate `PX11-PN-B2F` was retained.

## Method

The negative control replayed PX10's sorted pages from offset zero. It starved
the final identity at the 10,000-item maximum under the inherited 100-attempt
ceiling. The additive B2F candidate replaced blind detail scans with bounded
exact page-range directories and scheduled current-contact direction/category
lanes round-robin. Detailed transfer still uses PX10's advertisement, request,
and complete-record bytes; native D2/D3 validation and durability remain the
only state authority.

The experiment exercised static scales 100, 101, 1,000, and 10,000; suffix,
single-last, alternating, sparse, two-way, cross-category, control/record,
restart, subprocess, deterministic impairment, sender uncertainty, contact
history, churn, and paged mule scenarios. Every convergence loop had a fixed
horizon.

The final declared suite passed 414 tests with 5 skips, the focused PX11 suite
passed 46 tests, and compileall passed. Exact PX9 and PX10 closure refs were
also verified remotely as `checkpoint/px9-pn-b1` and
`checkpoint/px10-pn-b2`; remote `main` remained unchanged during those exact
checkpoint-ref writes.

## Results

Static finite fairness passed with zero starved eligible records. Ten thousand
missing queries converged in 109 fresh contacts. The final item at 10,000 and a
late 1,000-record suffix became reachable. A two-way 2,000-record workload made
progress in both directions on every contact. A 3,000-record cross-category
workload made progress in all three categories in its first contact.

Restart after every contact, real subprocess recovery of 105 queries and 105
results, and the paged A-C-B / B-C-A mule passed. Sender uncertainty committed
at the receiver; a new contact emitted no record message for that already
durable identity. Permanent loss terminated without mutation or a convergence
claim.

No endpoint or contact report persisted a peer offset, page, cursor, ACK,
session, or custody record. The B2F driver has no direct store access. The only
production change is the additive generic B2F module; D2, D2R, D3, D4, B1, B2,
and PNF1 files are unchanged.

## Falsification findings

The PX10 prefix strategy fails the PX11 fairness hypothesis, exactly as PX10's
limits anticipated. Page-range comparison plus durable-state shrinkage removed
that failure without another persistent authority. No existing native
correctness bug was found.

The result has sharp limits. Contacts below a complete dependency chain make no
progress, though they terminate. Arbitrary continuous churn is unproven.
Directories linearly scan local exact state and disclose exact bounds/digests.
High overlap is costly: 99.9% overlap consumed 4,997 control bytes and disclosed
143 identity occurrences for one new record. This is sufficient evidence to
gate compact/disclosure-aware reconciliation next, but not to choose its data
structure.

## Scientific classification

```text
POLLICINO_FAIR_PAGED_RECONCILIATION_READY_WITH_LIMITS
```

Confidence is HIGH for the registered deterministic, finite, static,
in-memory, complete-message experiments. It is not evidence for infinite-churn
fairness, privacy, global scale, real I/O, MTU/fragmentation, security, routing,
custody, or delivery guarantees.
