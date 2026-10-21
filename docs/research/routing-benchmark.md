# Multi-scenario routing benchmark

PollicinoNet can now compare the same stable routing strategy IDs across multiple independent synthetic network scenarios.

The purpose is to stop drawing conclusions from one hand-picked topology. Each scenario may define its own peers, contact windows, synthetic gateway ranks, bundle mix, priorities and destinations. Strategy instances may therefore carry scenario-specific metadata while retaining the same `strategy_id` for aggregation.

## What the benchmark measures

For each strategy, the benchmark aggregates independent dimensions rather than inventing one global score:

- bundle delivery opportunities and delivered bundles;
- delivery rate;
- EMERGENCY opportunities, deliveries and delivery rate;
- bundles that expired without delivery by scenario end;
- synthetic delivery-latency samples, mean and median;
- authoritative source bytes selected for transfer;
- modeled total wire bytes;
- skipped contact windows;
- per-bearer window count, source bytes and modeled wire bytes.

This lets us state trade-offs explicitly, for example:

```text
strategy A: more deliveries, more LoRa traffic
strategy B: fewer bytes, but misses a detour scenario
```

instead of hiding both facts behind a single arbitrary score.

## Independence

Each scenario is passed to the existing routing comparator. Every strategy run receives cloned peer stores, cloned custody state and cloned fair-scheduler state. Benchmark execution therefore does not mutate the scenario's original input network, and one strategy cannot benefit from data transferred by another strategy.

## Scenario-specific strategy metadata

A `GatewayProgressStrategy` may use different synthetic peer ranks in different scenarios. The benchmark only requires the same unique strategy IDs across all scenarios. This is intentional: a rank map belongs to one scenario topology, not to the strategy identity globally.

## Latency semantics

Delivery latency is calculated from the bundle's synthetic creation time to the end of the first contact window in which a destination holds the complete SHA-256-verified object.

These are **synthetic scenario seconds**. They are not measured physical LoRa delay.

## Evidence boundary

The benchmark is a software-policy experiment. It does not convert:

- synthetic contact duration into bearer capacity;
- synthetic peer rank into measured geographic/RF progress;
- logical byte budget into measured LoRa throughput;
- modeled wire bytes into a deployment reliability claim.

A future physical-evidence adapter may replace some scenario inputs with measured observations, but the benchmark must continue to report their provenance explicitly.

## Initial validated two-scenario example

The first benchmark fixture uses two scenarios with the same strategy IDs:

1. a normal chain where both flooding and gateway-progress deliver, while progress avoids an unhelpful contact;
2. an EMERGENCY detour where a synthetic progress hint rejects the only useful intermediate node.

Across the two scenarios:

- `flood-all` delivers both bundles;
- `gateway-progress` delivers one of two;
- flooding uses more modeled traffic;
- gateway-progress misses the EMERGENCY detour.

These numbers are test fixtures, not claims about the future student LoRa network.

## Next step

The next research step is deterministic **scenario-family generation**: produce many reproducible synthetic topologies/contact schedules from explicit seeds and parameter ranges, then feed them into this benchmark. The intended outputs are distributions across scenario families rather than conclusions from isolated examples.

For a future student network in Messina province, scenario generators should use pseudonymous peer IDs and abstract topology/mobility classes rather than publishing students' precise home locations.
