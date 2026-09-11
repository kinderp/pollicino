# PX13-PN-B2A workload and regret

The oracle-blind matrix covers local sizes 100, 1,000, and 10,000; differences
0, 1, 2, 5, 10, 20, 50, 100, 250, 500, 1,000, 2,000, 5,000, and 10,000 where
lawful; and prefix, suffix, sparse, alternating, contiguous, deterministic-random,
and symmetric directional shapes.

The hindsight-only perfect selector is the minimum complete control cost among
PX11 exact and the registered safe compact policies. The nine-policy comparison
panel produced selected-policy median regret 1.196875 and maximum regret
1.462385. The runtime never receives those oracle values.

At 10,000 records, selected/exact control bytes were:

| Difference | Selected | Exact | Ratio |
|---:|---:|---:|---:|
| 0 | 797 | 9,380 | 0.085 |
| 1 | 992 | 13,367 | 0.074 |
| 10 | 1,532 | 13,421 | 0.114 |
| 100 | 16,124 | 27,318 | 0.590 |
| 1,000 | 201,174 | 190,785 | 1.054 |
| 5,000 | 1,017,438 | 966,636 | 1.053 |
| 10,000 | 1,763,556 | 1,675,708 | 1.052 |

The 100-record equality case is a negative control: the 797-byte compact probe
costs more than the 182-byte exact directory. This is a quantified small-state
limit, not a correctness error.
