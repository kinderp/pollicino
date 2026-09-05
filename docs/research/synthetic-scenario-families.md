# Deterministic synthetic scenario families

## Purpose

PollicinoNet can now generate a reproducible family of synthetic routing scenarios instead of hand-authoring every contact graph.

The generator is intended for controlled software experiments before a real distributed LoRa testbed exists. It can create many independent scenarios containing pseudonymous peers, gateway peers, bundles, priorities, TTLs, multi-bearer contact windows and scenario-specific static gateway ranks.

The generator is deliberately **not** a radio propagation model.

## Reproducibility contract

A family is identified by a configuration and an integer seed.

With the same:

- family configuration;
- explicit bearer templates;
- strategy factory;
- seed;

PollicinoNet generates the same:

- scenario seeds;
- peer IDs;
- gateway IDs;
- contact-window endpoints and order;
- bearer selections;
- synthetic window durations;
- logical source-byte budgets;
- bundle contents and bundle identities;
- priorities and TTLs;
- static synthetic gateway ranks.

Changing the seed creates a different family.

This makes benchmark campaigns repeatable and reviewable.

## No invented bearer performance

The generator contains no built-in statement such as:

- "LoRa carries N bytes in 30 seconds";
- "Wi-Fi has X times the capacity of LoRa";
- "a wall reduces LoRa capacity by Y percent".

Every bearer must be supplied through an explicit `SyntheticBearerTemplate`.

A template contains two different classes of input:

1. an existing `BearerProfile` plus scheduling policy;
2. synthetic scenario-generation ranges for duration and logical byte budget.

Duration and logical byte budget are drawn independently. A generated 30-second window with a 128-byte logical budget means only:

> this synthetic encounter lasts 30 scenario seconds and the experiment author allowed the scheduler to select at most 128 authoritative source bytes.

It does **not** mean that a physical LoRa link was measured at 128 bytes per 30 seconds.

## Pseudonymous nodes

Generated peers use neutral IDs such as:

- `node-000`;
- `node-001`;
- `node-002`.

Gateways are selected from those same pseudonymous peers. The generator does not require names, home addresses, precise student locations, GPS coordinates or other personal data.

This is the intended format for preparing the future student-network experiments.

## Static gateway rank

For the core gateway-progress benchmark strategies the generator computes a synthetic static rank from the complete undirected generated contact graph.

Gateway peers have rank `0`. Other peers receive the minimum hop distance to any gateway in the whole generated graph. Disconnected peers receive a deliberately bad rank.

This rank is useful as a controlled benchmark baseline, but it is **oracle-like metadata** because it sees the whole generated scenario. A real relay must not be assumed to know it.

Future experiments should compare this baseline with online/local routing knowledge learned only from past contacts.

## Generated traffic

Each synthetic bundle receives:

- one pseudonymous non-gateway origin;
- deterministic generated content;
- a bounded PND1 rendezvous key;
- TTL;
- hop limit;
- priority (`BULK`, `NORMAL`, `HIGH`, `EMERGENCY`);
- chunk count and object size.

The priority distribution is configured explicitly through relative weights. No fixed application workload is embedded in the generator.

## Scenario family -> benchmark

`generate_synthetic_scenario_family(...)` returns a `SyntheticScenarioFamily`.

The family contains independent `RoutingBenchmarkScenario` objects and compact scenario summaries. Calling `family.run_benchmark()` runs the existing multi-scenario routing benchmark over the generated scenarios.

Therefore the experiment pipeline is now:

```text
explicit synthetic configuration
        |
        v
seeded scenario-family generator
        |
        +--> scenario 0000
        +--> scenario 0001
        +--> scenario 0002
        +--> ...
        |
        v
routing benchmark
        |
        v
separate delivery / latency / traffic / bearer metrics
```

There is still no hidden global winner score.

## Example: student-network laboratory family

The following is a **synthetic recipe**, not a claim about coverage in Messina province:

```text
family: student-testbed-v1
seed: 20260825
scenarios: 100
peers per scenario: 30
gateways: 2
bundles per scenario: 10
contact windows per scenario: 500
horizon: one synthetic day
bearers: explicit LoRa + Wi-Fi templates
traffic mix: mostly NORMAL, some HIGH, some EMERGENCY, some BULK
```

This can be used to study questions such as:

- how much redundancy helps EMERGENCY traffic;
- when flooding wastes scarce bearer budget;
- whether large objects should wait for Wi-Fi;
- how many gateways materially change delivery probability;
- how fairness affects low-priority traffic;
- how routing behaves when contacts are sparse or dense.

The recipe must be rerun with many seeds before treating a result as robust even within the synthetic model.

## What remains synthetic

Until physical evidence is collected, all of the following remain model inputs:

- contact occurrence;
- contact duration;
- bearer availability;
- logical byte budget;
- gateway rank;
- topology density;
- mobility/contact pattern;
- link loss/retry profile when not replaying recorded evidence.

The generator exists to compare algorithms under controlled assumptions, not to predict real geographic coverage.

## Physical evidence gate

HW-006 becomes necessary before generated LoRa contact windows are calibrated from real geometry, distance, obstruction and duration.

The physical campaign must first establish measured evidence for:

- contact availability at distance/NLOS;
- useful contact-window duration;
- actual governed PNB1/PNC1/PCM1/PNA1/data frame sizes;
- loss/retry behavior in the transition region;
- useful bytes/chunks delivered per encounter.

Only after that can a measured adapter map physical contact evidence into scheduling budgets used by these scenario families.

The frozen first campaign remains 42-byte frames at 2 dBm and does not change merely because the synthetic generator now exists.
