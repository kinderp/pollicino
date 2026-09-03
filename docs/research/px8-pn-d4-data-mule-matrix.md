# PX8-PN-D4 data-mule matrix

| Scenario | Persist/carry boundary | Outcome |
|---|---|---|
| A→C query Q | close/reopen C | C→B transfers exact Q |
| B evaluates Q | explicitly outside contact | B stores R |
| B→C result R | close/reopen C | C→A transfers exact R |
| result before query at C | close/reopen C | orphan remains non-actionable; later Q correlates |
| duplicate A→C→B→A loop | repeated encounters | zero missing retransfers after convergence |
| B→C reference X | explicit selection; close/reopen C | explicit C→A selection yields identical key/bytes |
| no D2 selection at either hop | none | zero reference transfer |
| conflicting query identity | C already holds different bytes | `QUERY_CONFLICT`, C unchanged |
| conflicting result identity | C already holds different keys | `RESULT_CONFLICT`, C unchanged |
| conflicting reference key | C already holds different bytes | `REFERENCE_CONFLICT`, C unchanged |

C uses only `ContactNode`, persistent D2, and persistent D3. It has no evaluator
and no FARO logic. Multi-hop topology is selected by the test harness; D4 does
not select a route. Forwarding copies state and never deletes the sender's copy.
