# PX11-PN-B2F fairness model

## Question and negative control

PX10 emits every sorted identity page from offset zero on every fresh contact.
At 10,000 queries, a receiver that already stores the first 9,999 sees 100
advertisements. The 100th advertisement discovers the last missing identity,
but the inherited 100-attempt ceiling prevents its request. Three entirely
fresh contacts reproduced the same zero-commit result. This is a prefix
starvation witness, not a PX10 regression: PX10 expressly left extreme paging
fairness unproven.

## Selected model

PX11 adds an experimental B2F layer alongside B2:

1. A source divides its local canonical identities into native 100-record
   pages and sends bounded descriptors containing the inclusive identity range,
   record count, and SHA-256 digest of each page's identities and native record
   digests.
2. A receiver compares each descriptor only with its own durable state. Equal
   pages need no detailed advertisement. Divergent ranges are requested in the
   current contact.
3. The source answers a range request with the existing exact B2
   identity-plus-record-digest advertisement. Existing B2 requests and complete
   record messages then reach the unchanged native D2/D3 apply methods.
4. Query, result, reference, and direction lanes receive one scheduling turn
   per round. Responses go to the front of their own lane so control cannot
   indefinitely postpone its record consequence.

All lane queues, descriptors, requests, and reports are ephemeral. No peer
label, cursor, offset, continuation token, ACK, or session object is written to
persistence. A new endpoint recomputes descriptors from local canonical state.

## Why fresh contacts progress

For the registered finite static model, native records are immutable and
successful additions are durable. Once records from a divergent range commit,
the receiver's next locally computed page comparison has fewer differences.
When the range becomes equal it stops generating detailed work, so earlier
completed work cannot permanently hide later divergent ranges. The lane
scheduler provides the analogous property across directions and categories
when a contact budget is large enough to complete the required control chain.

This is an experimental argument backed by the scale and adversarial matrix,
not a proof for Byzantine metadata, deletion, concurrent mutation, or infinite
churn. Remote page claims influence planning only. They never establish local
possession; only native durable apply does that.

## Explicit sufficiency condition

A one-page, one-lane first commit requires five bearer attempts:

```text
directory -> page request -> advertisement -> record request -> record
```

With the maximum two directory chunks and a populated reverse lane, the final
10,000-item page requires eight attempts. A smaller contact returns boundedly
without a commit and is not described as a sufficient delivery opportunity.
For all six lanes to reach their first record in one contact requires 32
attempts. The tests use explicit horizons and sufficient budgets; the
implementation never retries automatically.

## Rejected models

- Persistent peer cursors would make another authority for progress and fail
  the preregistered kill criterion.
- Hash-seeded rotation lacks a simple collision-free finite fairness argument.
- Blind prefix replay is the reproduced starvation control.
- Bloom filters, IBLT, Minisketch, Merkle reconciliation, and PSI address
  efficiency/privacy rather than the scheduling correctness question and are
  deferred.

## Result

The largest static experiment stored 10,000 identities (100 native pages), and
the complete missing set converged in 109 fresh contacts. The last-item and
late-suffix adversaries, two-way backlog, category backlog, restart, loss, and
mule paths all reached zero starved eligible records without persistent peer
progress state.
