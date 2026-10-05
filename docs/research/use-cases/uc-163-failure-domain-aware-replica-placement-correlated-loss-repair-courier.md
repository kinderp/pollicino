# UC-163 — Failure-Domain-Aware Replica Placement and Correlated-Loss Repair Courier

## Problem solved
Replicas can share one operational domain and become unavailable together. Spread exact copies across coarse domains.

## Actors / nodes
Content owner, cache nodes, student relays, placement planner and repair worker.

## Why PollicinoNet fits
LoRa carries compact replica intent and domain state; bulk data uses richer bearers. Frozen PHY unchanged.

## Bearers
LoRa for placement metadata; BLE/Wi-Fi/LAN for chunks; Internet optional; physical transport for large repairs.

## Software test now
Compare random, mobility-aware and domain-aware placement in simulated domains. Temporarily hide one domain and measure surviving copies and repair work.

## Real hardware
Use 6–10 boards plus several storage hosts with public data and controlled availability windows.

## Province scenario
Use several school/public test islands as coarse replica domains and let student nodes relay repair state between them.

## Privacy / security
Use only coarse domain labels and verify hashes before counting replicas.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-040 covers mobility/demand placement, UC-109 safe retirement and UC-012 backup/restore. UC-163 targets correlated-domain resilience.
