# PX9-PN-B1 preregistration

Baseline: exact `checkpoint/px8-pn-d4` commit
`e5cd094677e36e9f4b7a58c2aa81c897e7f43dc9`.

## Hypothesis

A minimal bearer adapter that attempts one complete bounded D4 record at a
time, plus an ephemeral deterministic lossy in-memory link, is sufficient.
The receiver's durable D2/D3 state remains the sole progress authority. A new
contact derives missing work by fresh reconciliation, including when the
sender is uncertain whether an earlier attempt committed.

## Models considered

1. **Complete-record B1 contract.** Expose one bounded, opaque transferable
   unit and one delivery attempt result. No framing, retry, ACK, or persistence.
2. **Thin reuse of `link.py`.** Rejected provisionally because its PNF1
   fragmentation, stop-and-wait retry, ACK loss, bitrate, and exact-content
   reconstruction are broader than D4 requires.
3. **Direct coupling to `transmit_exact()`.** Rejected provisionally because it
   would import deferred fragmentation/retry semantics and bind B1 to an older
   exact-content experiment.

Select model 1 only if the adversarial matrix passes without adding another
correctness authority. Models 2 and 3 remain candidates for a later adapter
conformance experiment, not implicit B1 requirements.

## Success criteria

- loss before apply leaves the receiver unchanged;
- commit followed by sender uncertainty is resolved by the next reconciliation;
- duplicate complete records are idempotent;
- conflicting duplicates fail closed without overwrite;
- disconnect preserves bounded partial durable progress;
- restart preserves committed progress and missing work remains eligible;
- deliverable later contacts converge canonically;
- permanent loss returns bounded non-convergence, never false success;
- no persistent contact cursor, ACK state, peer journal, or custody log;
- application-specific bearer-core branches are zero;
- concrete-bearer branches in D4 core are zero.

## Bounds preregistration

One invocation is bounded by the existing D4 item and logical-byte budgets and
by a separate positive bearer-attempt limit no greater than the D4 item ceiling.
The scripted link has no queue: at most one complete unit is in flight. Its
event trace is capped by the attempt limit. There is no internal retry loop.

## Kill criterion

If any registered loss, uncertainty, disconnect, restart, or recontact case
requires a persistent ACK database, contact/session cursor, peer-progress
journal, custody log, or ambiguous partial record state, stop. Classify the
candidate as a missing generic capability or as falsification of PX8 durable
reconciliation; do not add that state to make the test pass.

