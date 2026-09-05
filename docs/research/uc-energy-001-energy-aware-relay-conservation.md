# UC-ENERGY-001 — Energy-aware relay conservation

Status: PROTOTYPE-DRIVING INFRASTRUCTURE / software-first until measured power data exists

## Problem

A student-carried Pollicino node may be useful precisely because it relays other people's traffic for many hours. That same behavior can drain a small battery, punish the most central carriers and make the network unusable before the student returns home.

The concrete question is:

> can PollicinoNet preserve useful delivery while respecting a local energy reserve and distributing relay work more fairly across available carriers?

This is distinct from `UC-OPS-001`: OPS reports/configures node health. ENERGY treats battery as a scarce forwarding resource and asks how relay decisions should degrade gracefully when energy becomes limited.

## Actors / nodes

- battery-powered student Pollicino nodes;
- school or home nodes with plentiful power;
- optional vehicle/fixed relays with larger batteries;
- routing/scheduling logic using only explicitly available local energy state;
- experiment recorder tracking delivery and modeled/real energy.

## Why PollicinoNet fits

Store-carry-forward creates a real energy-allocation problem: every scan, receive, store and retransmission has a cost, and different nodes may be asked to relay very different amounts.

PollicinoNet already has finite contacts, routing baselines, duplicate suppression, TRC accounting and node lifecycle state. Energy can therefore begin as a **local admission constraint**, not as a new network-wide routing protocol.

The adoption ladder should be intentionally simple:

1. baseline: ignore battery;
2. minimum reserve threshold: stop accepting non-critical relay work below a configured reserve;
3. bounded daily relay budget;
4. priority-aware reserve for urgent/test traffic;
5. only if the simple policies fail, compare routing decisions that use measured residual energy.

## Possible bearers

- LoRa: main scarce radio whose TX/RX/listen energy must eventually be measured;
- BLE: nearby discovery or companion-device work with its own energy budget;
- Wi-Fi: rich synchronization when power/connectivity are available;
- physical carry: moves data at almost no radio cost while the node is simply being carried.

## What we can test immediately in software

Use synthetic battery models first. Every action consumes explicit modeled units for:

- idle/listen;
- discovery/probe;
- RX;
- TX;
- local flash/storage activity;
- optional BLE/Wi-Fi transitions.

Compare:

```text
ignore energy
reserve threshold
daily relay-byte budget
priority-aware reserve
```

on the same school-morning / territorial-afternoon contact traces.

Track:

- delivery ratio and deadline success;
- modeled energy consumed per node;
- minimum remaining energy across the fleet;
- relay-load inequality/fairness;
- number of nodes that become unavailable;
- useful delivered bytes per modeled energy unit;
- traffic rejected because of reserve policy.

Do not claim joules or battery lifetime from a synthetic model.

## Messina student-network scenario

A dense morning school phase loads many nodes with candidate bundles. In the afternoon, a few students become bridge nodes between logical territorial clusters. Without a reserve policy those central carriers may perform most of the forwarding.

A useful synthetic experiment gives every student node the same starting battery and compares whether a simple reserve threshold prevents a small number of bridge nodes from being exhausted while preserving most deliveries to the next school/home contact.

Public town names may label logical clusters only; no real route energy or contact capacity is assumed.

## What requires real hardware

After HW-006, ENERGY needs a dedicated measurement campaign for the actual board/power configuration:

- idle and sleep current;
- LoRa RX/listen current;
- LoRa TX current at the frozen test configuration;
- flash/write cost;
- BLE/Wi-Fi transition cost if used;
- battery voltage/capacity curve;
- restart/brownout behavior;
- whole-day duty-cycle trace under a realistic pilot workload.

Only measured values may calibrate later energy-aware routing comparisons.

## Privacy and security

Battery state can reveal behavior if exposed unnecessarily. Prefer local decisions or coarse capability classes rather than broadcasting exact battery telemetry.

- do not associate energy logs with named students;
- avoid continuous personal-device battery collection;
- authenticate any remote policy that can disable/limit relaying;
- prevent a peer from forcing another node to spend energy through repeated bogus requests;
- reserve abuse/denial-of-service testing for synthetic fixtures first.

## Difficulty

**Medium in software; medium-high for trustworthy physical calibration.**

## Success / kill criteria

Promote an energy-aware policy only if it improves a preregistered fleet-level objective such as minimum remaining energy, alive-node count or fair relay load without an unacceptable loss in delivery/deadline success compared with simpler baselines.

If a simple local reserve threshold is sufficient, do not add complex energy gossip or routing state.

## Related-work note

Energy-aware DTN/DTWSN routing is established prior art. For example, Kang and Chung (2017, DOI `10.1177/1550147717717389`) explicitly study forwarding using remaining battery and delivery predictability in intermittently connected sensor networks. PollicinoNet should treat those ideas as baselines, not novelty claims.

## Physical evidence boundary

No battery-life, current, energy-per-message or network-lifetime claim is valid until measured on the actual Pollicino hardware. The frozen LoRa PHY remains unchanged.