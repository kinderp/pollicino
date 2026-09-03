# PX6-PN-D3 local multi-node matrix

All interactions are ordinary method calls between independent stores and directories.

| Case | Result |
|---|---|
| A creates/persists Q, stops, restarts | PASS |
| B starts later and pulls Q | PASS |
| B application evaluates Q externally | PASS |
| B persists R, stops, restarts | PASS |
| A returns later and pulls R | PASS |
| A → B query | PASS |
| B → A delayed result | PASS |
| A → C query | PASS |
| C → A delayed result | PASS |
| query A → B → C → A loop | idempotent convergence |
| result B → A → C → B loop | idempotent convergence |
| B returns `[X,Y]`, C returns `[Y,Z]` in differing orders | byte-identical final state |
| result arrives before query | bounded persistent orphan; correlates later |
| A/B/C stop and reopen independently | query, result and catalog state preserved |
| reconciliation after restart | PASS |

Different delivery orders, generation numbers and restart histories do not affect logical state identity. Multiple result records containing the same key are not aggregated into authority or ranking. There is no consensus or delivery guarantee.
