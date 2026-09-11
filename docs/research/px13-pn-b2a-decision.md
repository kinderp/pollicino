# PX13-PN-B2A decision

GATE: PX13-PN-B2A

IDENTIFIER PROVENANCE: candidate derived from the PX12 closure; no later
authoritative identifier was found.

CLASSIFICATION: POLLICINO_BOUNDED_ADAPTIVE_RECONCILIATION_READY_WITH_LIMITS

CONFIDENCE: HIGH

DECISION: admit the oracle-blind, one-probe capacity-10 policy with same-contact
PX11 exact fallback as the simplest validated byte-first policy. Retain all
other policies as experiment configurations, not production defaults.

The originally preregistered `(10, 100, exact)` candidate is rejected for
exceeding the registered large-difference ratio. The capacity-1 strategy is 252
bytes cheaper when it peels, but is less robust at 20 differences. Multi-level
and capacity-1,000 ladders accumulate excessive bytes.

Hard results:

```text
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
UNBOUNDED_ESCALATIONS = 0
PERSISTENT_PEER_POLICY_STATE = 0
PERSISTENT_ESCALATION_STATE = 0
APPLICATION_SPECIFIC_POLICY_BRANCHES = 0
DIRECT_REMOTE_STORE_READS = 0
```

Limits are experimental in-memory B1/B2 transport, a deliberately conservative
exact-cost bound, small-state equality overhead, no fragmentation/MTU proof, no
authentication/privacy property, and no persistent peer learning.

PX3 through PX12 remain valid unchanged.

The smallest evidence-justified next experiment is independent-process byte I/O
using the already bounded B2/B2F/B2C/B2A messages. Fragmentation remains a
separate pressure because the selected default avoids near-ceiling sketches.
