# PX12-PN-B2C workload matrix

The deterministic matrix covers 100, 1,000, and 10,000 query identities at 0%,
50%, 90%, 99%, and 99.9% overlap where meaningful. Difference shapes include
single late item, prefix, suffix, sparse, alternating, contiguous, many, and
symmetric differences. Critical 10,000-state cases use 1, 10, 100, and 1,000
missing records.

The selected candidate is also exercised with capacities 1, 10, 100, and 1,000;
with corruption; above capacity; across loss, duplicate, disconnect and sender
uncertainty; after durable restart; and over a semantic-blind mule.

All runs are complete-record, in-memory experiments. Timing is model-level
diagnostic data, not a network or RF benchmark.
