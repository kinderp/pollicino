# PX13-PN-B2A policy model

PX13 adds no reconciliation algorithm. It composes the unchanged PX12 compact
attempt and PX11 exact fair contact behind one bounded current-contact policy.

The selected byte-first policy is:

```text
if the contact cannot preserve eight exact-path attempts:
    exact immediately
else:
    one digest-bound IBLT probe at capacity 10
    success -> normal B2 record path
    delivered decode failure -> PX11 exact in the same contact
    transport loss/corruption/disconnect -> stop; do not infer capacity failure
```

Capacity 100 remains available for registered competitor policies but was
removed from the default after the preregistered two-probe candidate exceeded
the 1.25 large-difference threshold. Capacity 1,000 is never selected by the
default because its 28,517-byte summary is near the 29,245-byte B2 ceiling.

The policy receives local endpoint state, record kind, selected references,
current budget, bearer, and policy configuration. It receives no difference,
overlap, oracle, or fixture label. All escalation variables are ephemeral.

An outer bearer wrapper accounts for cumulative compact and exact attempts and
bytes. Thus fallback cannot reset or bypass the contact budget.
