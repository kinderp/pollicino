# PX13-PN-B2A exact-cost estimator

The deployable estimator uses only local cardinality and inherited B2/B2F
bounds. It computes a conservative all-pages-divergent upper bound containing
directory and page-request envelopes plus maximum advertisement/request units.

| Local records | Upper bound | Measured exact range | Overestimate at largest difference |
|---:|---:|---:|---:|
| 100 | 113,980 | 182–8,859 | 12.87x |
| 1,000 | 640,390 | 1,010–97,950 | 6.54x |
| 10,000 | 5,959,980 | 9,380–1,675,708 | 3.56x |

There were no underestimates in the registered matrix, but the bound is too
loose to predict the crossover precisely. Consequently the selected policy uses
it only as a safety comparison and relies primarily on a single small probe,
explicit byte/summary caps, and an exact-progress attempt reserve. No runtime
decision sees measured PX11 cost.
