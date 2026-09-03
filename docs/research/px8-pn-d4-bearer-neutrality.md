# PX8-PN-D4 bearer-neutrality audit

Automated source inspection rejects bearer, socket, address, signal, and PR #52
runtime vocabulary from `src/pollicino/net/contact.py`. The module accepts
Python objects representing existing D2/D3 stores; it has no I/O channel,
packet, frame, address, timer, retry, daemon, or background worker.

Existing Pollicino link/fragmentation modules are intentionally not imported.
Complete records are atomic at this local semantic layer. Canonical entry sizes
are used only for model accounting and do not define a D4 frame or stable wire
format.

```text
BEARER_SPECIFIC_CONTACT_CORE_BRANCHES: 0
NETWORK: NONE
PR52_DEPENDENCY: NONE
STABLE_WIRE_PROTOCOL: NONE
FRAGMENTATION: DEFERRED
```
