# PX11-PN-B2F scale matrix

All counts below are local experimental protocol accounting, not throughput or
RF measurements. Each contact creates a fresh B2F protocol plan.

## Static query convergence

| Records | Initially missing | Attempts/contact | Contacts | Commits | Starved |
|---:|---:|---:|---:|---:|---:|
| 100 | 100 | 25 | 5 | 100 | 0 |
| 101 | 101 | 25 | 6 | 101 | 0 |
| 1,000 | 1,000 | 25 | 50 | 1,000 | 0 |
| 10,000 | 10,000 | 100 | 109 | 10,000 | 0 |

The 10,000 case exercises the native maximum of 100 pages. It is deliberately
inefficient but fair. A 10,000-record source with a receiver missing only the
last 1,000 converged in 11 contacts; a receiver missing only the final identity
committed it in one default-budget contact.

## Late and sparse shapes

| Shape | State | Result |
|---|---:|---|
| final identity only | 10,000 | pass, one commit |
| late suffix | 9,000 known / 1,000 missing | pass, 11 contacts |
| alternating identities | 1,000 / 50% missing | pass |
| sparse final identity | 1,000 / 99.9% overlap | pass |
| early and late gaps through full convergence | 1,000 | pass |

## Generic record categories

- Queries: complete 10,000-record and late-page experiments passed.
- Results: 1,000 orphan-safe bounded results crossed repeated contacts; the
  candidate keys remained only candidate keys.
- References: 250 selected references crossed multiple pages; the final
  selected reference at a 10,000-item catalog boundary was reachable.
- Mixed: 1,000 queries, 1,000 results, and 1,000 explicitly selected references
  all first progressed in contact one and converged in 36 contacts.

D2 remained explicit. Merely carrying a result never started the reference
directory lane.

## Direction fairness

Two endpoints each began with 1,000 disjoint queries and shared a 100-attempt
contact ceiling. They converged in 23 contacts with 1,000 commits each way.
Every contact made progress in both directions. Canonical final bytes matched.

## Restart scale

The persistent restart-after-every-contact case transferred 250 queries in 13
contacts and 315 attempts. A separate-process test wrote 105 queries plus 105
results, transferred them through B2F/B1, closed the receiver, and verified all
210 records in another process. No peer-progress file was present.
