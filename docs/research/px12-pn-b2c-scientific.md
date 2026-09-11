# PX12-PN-B2C scientific report

PX12 asked whether compact reconciliation can beat PX11 exact B2F without
changing what is missing. The result is regime-specific.

The IBLT candidate passed all 81 oracle-differential pairs with zero mismatch
and zero undetected false negative. It preserved native conflict handling by
binding sketches to both identity and native record digest. Corruption and large
difference overflow failed detectably. An explicit unchanged PX11 fallback
converged after compact decode failure. Complete-record loss did not mutate state;
duplicates were idempotent; sender uncertainty was resolved by a fresh compact
equality check; persistent compact or peer state was unnecessary.

At 10,000 identities, compact/exact control bytes were 740/13,367 for one
missing, 1,532/13,421 for ten, 12,988/27,318 for one hundred, and
413,452/190,785 for one thousand. The first three reduce bytes by 94.5%, 88.6%,
and 52.5%. The last increases bytes by 116.7%, although exact identity disclosure
falls 74.4%.

Low-overlap controls show no universal win. Unknown difference size is the
dominant unresolved limitation: too-small sketches can require exact fallback,
while too-large sketches erase the byte advantage. A bounded adaptive policy is
conceptually justified but requires its own experiment.

No PX3-PX11 production file was modified. PX11 remains the exact oracle and fair
fallback.
