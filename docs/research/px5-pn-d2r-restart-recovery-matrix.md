# PX5 PN-D2R restart/recovery matrix

| Case | Result |
|---|---|
| no state | empty + `NO_DURABLE_STATE` |
| first commit / clean restart | exact native bytes, generation 1 |
| subprocess write then process reload | PASS |
| duplicate after restart | `NOOP_DUPLICATE`, no generation/write |
| conflict after restart | native conflict; disk/live unchanged |
| item/byte quota after restart | native failure; capacity unchanged |
| orphan temporary file | ignored |
| before temp / during write / before file fsync / before replace | old authority preserved |
| after replace / after directory fsync before memory swap | fail-stop, reopen required |
| truncated header/metadata/payload | fail closed |
| corrupt magic/version/generation/payload/digest | detected |
| unsupported version | `PERSISTENCE_VERSION_UNSUPPORTED` when no valid fallback |
| overbound key/reference/item/payload | `PERSISTENCE_BOUNDS_VIOLATION` |
| newest corrupt + previous valid | previous loaded with explicit recovery status |
| both generations corrupt | fail closed, never empty |
| equal generation + different valid payloads | `AMBIGUOUS_DURABLE_STATE` |
| A/B/C independent restart | PASS |
| A↔B, B↔C, A↔C native reconciliation after restart | PASS |
| equal logical states, differing paths/history | identical PX3 canonical state |
| FARO reference/variant/PX1 cases after restart | PASS |

The matrix is deterministic local correctness accounting. It is not a storage
benchmark or physical power-loss experiment.
