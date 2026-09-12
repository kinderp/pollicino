# BPv7 semantic mapping notes — no integration decision

Status: research-only checkpoint, 2026-08-25

The Use-Case Justification Gate does not currently justify implementing BPv7 interoperability. These notes exist only to prevent semantic reinvention and to identify future interop questions.

## Mapping

| PollicinoNet | BPv7 / DTN analogue | Same? |
| --- | --- | --- |
| PNB1 bundle envelope | BP bundle / primary + canonical blocks | No, only conceptual overlap |
| TTL / expiry | bundle lifetime / age | Similar purpose, different wire/semantics |
| hop limit | Hop Count extension block | Similar safeguard |
| persistent relay | store-carry-forward node | Strong architectural overlap |
| LoRa/BLE/Wi-Fi/Internet bearer | convergence-layer concept | Similar separation of overlay from underlying transport |
| PNC1 custody | historical DTN custody/BIBE-family ideas | Do not call it BPv7 custody |
| PCM1 content chunks | BP fragmentation only partially overlaps | Pollicino chunks are content-addressed/reusable receiver-knowledge units |
| PNA1/PNA2 | no direct BPv7 equivalent | Pollicino reconciliation-specific |
| per-bearer TRC/evidence class | implementation/research instrumentation | Pollicino-specific |

## Key architecture lesson

BPv7 does not prescribe the routing algorithm. Therefore canonical DTN routing experiments remain useful whether PollicinoNet stays independent or later gains a BPv7 adapter.

BP fragmentation should be treated as the baseline for splitting transport around contact limitations. PCM1 should be retained only where content identity, receiver reuse or resumability provides measurable value beyond ordinary fragmentation.

## Gate

No active external BPv7 node/application currently requires interoperability.

**Decision: RESEARCH ONLY.**

Do not modify PNB1 or add a BP implementation until a concrete interop use case appears.

Potential gate-reopening cases:

- external BPv7 testbed/tool requirement;
- NASA/IETF-compatible DTN experiment;
- use of a mature BP stack below Pollicino reconciliation;
- security/management ecosystem advantage proven to reduce total complexity.
