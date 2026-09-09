# UC-035 — Federated Sketch / Aggregate Courier

## Idea

Let nodes keep raw observations locally and exchange only **small mergeable summaries**: counters, histograms, HyperLogLog-like cardinality estimates, quantile summaries, Count-Min sketches or other bounded aggregates.

A relay can merge or carry these summaries across disconnected islands until a global aggregate becomes available without collecting every raw record.

## Problem solved

Many questions do not require all raw data.

Examples:

```text
How many unique nodes were seen today?
How many sensor events fell in each coarse category?
What is the approximate distribution of queue delay?
How many students selected each synthetic classroom option?
```

Sending every individual observation wastes scarce bandwidth and can expose unnecessary personal or operational details.

## Actors / nodes

- student PollicinoNet nodes;
- school/server aggregate node;
- IoT/sensor nodes;
- student relay/store-and-forward nodes;
- optional UC-008 observatory data source;
- optional edge analytics process.

## Why PollicinoNet fits

Many useful sketches are small and have merge operations that tolerate reordered delivery.

- **DISCOVERY:** which aggregate/sketch families and epochs a node holds;
- **EXACT:** sketch type/version, epoch, parameters, contributor-set identity or deduplication metadata;
- **SEMANTIC:** human meaning such as `contact-count distribution` or `temperature histogram`.

LoRa can often carry an aggregate that is much smaller than the raw observations that produced it. Richer bearers remain available when exact evidence is needed.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** compact sketch/aggregate metadata and, only when measured practical, the sketch itself;
- **BLE:** nearby aggregate reconciliation;
- **Wi-Fi/LAN:** larger aggregate states or exact audit samples;
- **Internet:** optional central aggregation when available;
- **physical transport:** student relay carries aggregate state between disconnected islands.

## What we can test now in software

Start with fully synthetic data and two or three mergeable summary types.

Test:

- merge order invariance where the chosen sketch supports it;
- duplicate delivery and contributor deduplication;
- delayed/out-of-order epochs;
- node dropout and later reappearance;
- bounded sketch size while raw record count grows;
- exact baseline comparison for error measurement;
- malicious/outlier contributor injection;
- per-epoch reset and retention;
- raw-data deletion while retaining an authorized aggregate;
- combining UC-008 contact traces into privacy-reduced network statistics;
- optional differential-privacy noise only as a separate, measurable policy layer rather than an automatic privacy claim.

Useful metrics include encoded sketch bytes, merge CPU time, approximation error against the exact synthetic baseline, duplicate overhead and convergence delay.

## What requires real hardware

- 4–6 boards generating independent small event streams;
- one moving relay that merges/carries summaries;
- measured sketch/control airtime and delivery behavior;
- one experiment comparing raw-event forwarding against aggregate forwarding on the same controlled workload;
- optional sensor inputs after the software semantics are stable.

## Messina teaching scenario

Students can first use **network-observatory data**, not personal data.

Each board counts privacy-safe encounter statistics over a fixed classroom exercise. Separate groups are disconnected. A moving relay carries mergeable summaries until the school node reconstructs an approximate global view such as encounter-count distribution or unique rotating-ID cardinality.

A later environmental version can aggregate coarse sensor statistics per declared public test zone without retaining each student's route.

## Privacy / security

Aggregation is not automatically anonymous.

A small group's histogram or unique-count estimate may still reveal individuals, especially when compared across epochs. Therefore:

- use synthetic or non-personal data first;
- enforce minimum cohort/zone sizes where relevant;
- avoid contributor identities in the user-visible aggregate unless necessary;
- separate aggregate integrity from privacy guarantees;
- authenticate contributors/merge operations when the result is security relevant;
- do not call a sketch "privacy preserving" merely because it is compact;
- define retention for raw local observations and aggregate epochs.

## Difficulty

**Medium.** Mergeable sketches are well understood and highly testable. The hard part is choosing semantics that remain correct under duplication/partition and making privacy claims only when the chosen mechanism actually supports them.

## Research signal

Current edge/federated analytics research continues to emphasize local data retention, communication reduction and verifiable aggregation. PollicinoNet can study a much simpler and more LoRa-native slice of that problem using deterministic mergeable summaries rather than model gradients.

References:

- https://doi.org/10.1016/j.comcom.2026.108575
- https://doi.org/10.1109/JIOT.2026.3680237
- https://link.springer.com/article/10.1186/s13638-025-02545-x
