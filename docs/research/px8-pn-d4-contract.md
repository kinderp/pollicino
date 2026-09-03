# PX8-PN-D4 contact contract (preregistered)

A contact is an explicitly invoked, finite, application-neutral opportunity
between two caller-provided node states. It is not a socket, stream,
authenticated peer, reliable connection, route, or custody transfer.

Deterministic phases are: queries left-to-right, queries right-to-left, results
left-to-right, results right-to-left, caller-selected D2 references
left-to-right, and caller-selected D2 references right-to-left. Query intent is
carried before answers, while reference work remains last and explicit. The
left/right labels express direction only and confer no authority.

Each missing record is checked against the contact budget and then applied via
the native D2/D3 API as one atomic semantic unit. Interruption is permitted at
phase boundaries, immediately before a record apply, or immediately after a
successful apply. D4 does not fragment records.

Completion outcomes are `NO_MORE_ELIGIBLE_WORK`, `BUDGET_EXHAUSTED`,
`INTERRUPTED`, and `ERROR`. Partial convergence is valid. Reports are local
diagnostics and are never protocol state.

D4 executes no query evaluator and performs no automatic reference selection,
package retrieval, import, trust, evidence, recommendation, routing, expiry,
garbage collection, authentication, or background retry.
