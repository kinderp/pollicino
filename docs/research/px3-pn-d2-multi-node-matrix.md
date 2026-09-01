# PX3-PN-D2 local multi-node matrix

All nodes use independent `BoundedReferenceCatalog` instances. Exchanges are
ordinary local method calls over pages of at most 100 items.

## Initial state

| Node | Logical fixture IDs | State digest |
|---|---|---|
| A | 0, 1, 2 | `26f9516204a2224288a729df32d501ad05ec5539aaa4a0cc5f79bdcfe4759422` |
| B | 2, 3, 4 | `be21f997ccdcc8850bb97c1559a3a6c9b8d00730d9083b4d582cc3f7f4385696` |
| C | 4, 5, 0 | `4be50a905faffc42a82ea2540f03885277b3130d4ddee3c0f87a406088240287` |

The three different digests confirm independent divergent local state.

## Contacts

| Contact | Direction | Operation | Result |
|---|---|---|---|
| A/B | both | sorted IDs, exact unknown IDs, pull new | A and B each hold 5 |
| B/C | both | sorted IDs, exact unknown IDs, pull new | B and C each hold 6 |
| A/C | both | sorted IDs, exact unknown IDs, pull new | A and C each hold 6 |

The `A<->B`, `B<->C`, and `A<->C` required paths all pass. Repeating any
identical offer returns `NOOP_DUPLICATE`; it does not add counters or change the
state digest.

## Final state

| Node | Item count | State digest |
|---|---:|---|
| A | 6 | `304851c725938da67de9f51a72311a495f1876699592d348954e1f51ce3b90e9` |
| B | 6 | `304851c725938da67de9f51a72311a495f1876699592d348954e1f51ce3b90e9` |
| C | 6 | `304851c725938da67de9f51a72311a495f1876699592d348954e1f51ce3b90e9` |

```text
NODE_A_B: PASS
NODE_B_C: PASS
NODE_A_C: PASS
DETERMINISTIC_CONVERGENCE: PASS
GLOBAL_CONSENSUS_CLAIM: NONE
NETWORK: NOT_USED_BY_DESIGN
```

The reproducible record is
[multi-node-fixtures.json](../../experiments/px3-pn-d2/multi-node-fixtures.json).
