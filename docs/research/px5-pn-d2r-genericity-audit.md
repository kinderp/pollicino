# PX5 PN-D2R genericity audit

Core persistence has zero references or branches for `faro`, `evidence`,
`publisher`, `recommendation`, `machineprofile`, `dna`, `travel`, `torrent` or
`magnet`. It contains no `NodeRuntime`, DirectoryPollicinoStore, PNB1, PNC1,
custody, bearer, socket or HTTP dependency.

`APPLICATION_SPECIFIC_PERSISTENCE_BRANCHES = 0`.

The implementation uses only the Python standard library and PX3 catalog
module. FARO exists solely in an optional test module. The native
`catalog.py` is unchanged; staging and load both call its canonical decoder and
native mutations. Reconciliation delegates to native `reconcile_and_pull` on
a staged native receiver before atomically persisting the exact pulled set.

Committed artifacts contain no test paths, usernames, hostnames, IP/MAC
addresses, private keys, trust stores or application metadata.
