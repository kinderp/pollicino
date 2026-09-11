# PX12-PN-B2C disclosure model

PX12 says **metadata disclosure reduction**, not privacy preservation.

The compact summary exposes cardinality, a full-state SHA-256 digest, configured
capacity, and IBLT cells containing signed counts, XORed 64-bit fingerprints,
and 32-bit peel checksums. A successful difference exchange additionally exposes
requested short fingerprints, then the full identities and native record digests
needed for ordinary B2 retrieval.

It does not initially disclose every exact identity or every per-record digest.
It nevertheless leaks membership-correlated sketch material and set cardinality.
There is no PSI, anonymity, zero knowledge, authentication, or confidentiality
claim.

At 10,000 identities, exact identity occurrences fell from 503 to 2 for one
missing item, 512 to 20 for ten, 1,109 to 202 for one hundred, and 7,895 to 2,020
for one thousand. The last regime saves disclosure but increases control bytes.
