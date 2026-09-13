# PX19-PN-B8 decision

## Decision

```text
GATE:
PX19-PN-B8

IDENTIFIER_STATUS:
REPOSITORY_OWNER_CANDIDATE_FROM_PX18_CLOSURE_RECOMMENDATION

CLASSIFICATION:
PX19_REAL_LAN_EVIDENCE_PENDING

CONFIDENCE:
HIGH
```

## Reason

Two physical hosts and their non-loopback LAN routes were established, but the
Windows Host B cannot import the inherited `fcntl`-based durable persistence
layer. No Pollicino endpoint contact crossed the LAN. Loopback, same-host, VM,
or missing-peer traffic cannot replace the mandatory evidence.

This is classified `M.PLATFORM_PORTABILITY_LIMIT`, not a UDP/B4 correctness
failure. PX19 did not alter persistence because that would widen the gate and
invalidate its frozen variable.

## Architecture status

```text
B4_CHANGED = NO
D2_D3_D4_CHANGED = NO
B2_FAMILY_CHANGED = NO
UDP_SEMANTICS_CHANGED = NO
GENERIC_TRANSPORT_CONTRACT_CHANGED = NO
PERSISTENT_LAN_SESSION_STATE = 0
PERSISTENT_ACK_STATE = 0
PERSISTENT_FRAGMENT_STATE = 0
ROUTING_DISCOVERY_SECURITY_RELIABILITY = 0
```

The UDP adapter now admits explicit numeric IPv4 unicast, the minimum change
needed for LAN configuration. That change is locally green, but transport
sufficiency on a physical LAN remains unproven.

## Checkpoint and continuation

No `checkpoint/px19-pn-b8` is created because the gate did not close READY.
The working branch preserves preregistration, implementation and pending
evidence.

Smallest next action: rerun the exact PX19 implementation on a second physical
macOS/Linux host. If Windows support is mandatory, first authorize a separate
cross-platform durable persistence/locking gate, then resume PX19 from clean
committed code on both hosts.
