# PX8-PN-D4 interruption matrix

Fault model: `CONTACT_INTERRUPTION_MODEL`, not a real network failure test.

| Boundary | Observed result |
|---|---|
| before first apply | receiver byte-identical to pre-contact state; next contact transfers record |
| after query apply | query durable after close/reopen; next contact transfers zero copies of it |
| before result phase | completed query remains; result/reference remain absent |
| after result apply | result durable after close/reopen; next contact transfers zero copies of it |
| before reference phase | completed query/result remain; unselected reference remains absent |
| after selected reference apply | reference durable after close/reopen; next contact transfers zero copies of it |
| before next record | all earlier complete records remain; next record remains missing |
| item budget exhausted | outcome `BUDGET_EXHAUSTED`; partial convergence valid |
| byte budget cannot fit next record | no partial record; outcome `BUDGET_EXHAUSTED` |
| receiver query quota | outcome `ERROR/QUERY_RESULT_BOUNDS_ERROR`; prior record remains |
| receiver catalog quota | outcome `ERROR/CATALOG_BOUNDS_ERROR`; state unchanged |
| sender restart | fresh reconciliation succeeds from durable state |
| receiver restart | applied records remain known |
| mule restart | query, result, orphan result, and selected reference remain forwardable |
| real subprocess exit/reopen | query survives and forwards in a new process |

Interruption points are deterministic local inputs. There are no timers,
background retries, partial frames, or wall-clock assumptions.
