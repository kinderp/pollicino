# UC-070 — Physical Energy Mule and Charging Rendezvous

## Idea

Sometimes the scarce resource is not data but **energy**. A remote sensor, field kit or disconnected node may have enough battery to advertise that it is running low but no fixed power source nearby. PollicinoNet can coordinate a low-voltage energy handoff: one node advertises a need, another advertises available charging capacity, and a person/vehicle physically carries a power bank or battery pack to the right place.

The network does not transfer electrical power over LoRa. LoRa only coordinates **who needs energy, how urgent the need is and where/when a safe handoff can occur**.

## Problem solved

Rural or temporary deployments may fail because a node runs out of battery before a technician reaches it. Sending someone blindly wastes time and may deliver the wrong connector, voltage or capacity.

We want to test whether a delay-tolerant network can coordinate:

- low-battery requests;
- compatible charger/power-bank capabilities;
- estimated energy needed versus energy available;
- reservation of one portable charger for one request;
- physical delivery by a student/teacher/vehicle;
- receipt and post-charge status;
- cancellation when the node recovers or another charger arrives first.

This is deliberately a **low-voltage teaching experiment**, not a power-grid or emergency-power system.

## Actors / nodes

- battery-powered sensor/LoRa node;
- portable USB power bank or safe low-voltage battery pack;
- student/teacher data-and-energy mule;
- school/lab charger inventory node;
- optional vehicle relay;
- optional sensor gateway collecting battery-health telemetry.

## Why PollicinoNet fits

Energy requests and capability advertisements are tiny and tolerate delay.

- **DISCOVERY:** `energy needed`, coarse urgency, connector/voltage class, charger available;
- **EXACT:** node ID, request ID, battery/charger capability profile, reservation ID, measured pre/post charge state and handoff receipt;
- **SEMANTIC:** labels such as `low`, `critical-soon`, `USB-C`, useful for discovery but never sufficient for electrical compatibility by themselves.

Store-carry-forward is a natural fit because the same person who carries the message can later carry the power bank physically.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** energy-need summary, charger capability class, reservation, expiry, handoff status;
- **BLE:** close-range charger/node negotiation or detailed battery telemetry;
- **Wi-Fi/LAN:** logs and historical energy data;
- **Internet:** optional inventory synchronization;
- **physical transport:** the actual energy store moves as a power bank/battery pack with the courier.

## What we can test now in software

Create synthetic nodes with battery state, consumption rate, safe charger profiles and portable energy inventories.

Test:

- one low-battery node and one compatible charger;
- multiple requests competing for one power bank;
- incompatible connector/voltage profile;
- request expires before physical delivery;
- two couriers reserve the same charger concurrently;
- battery state changes while the request is in transit;
- node shuts down before the courier arrives and later wakes when connected;
- partial charge followed by another delivery;
- scheduling policies such as earliest-depletion-first, shortest-detour and fair-share;
- integration with UC-008 contact traces and UC-015 resource reservation;
- comparison of `data-only mule` versus `data + energy mule` in simulation.

Useful metrics include request-to-handoff delay, percentage of synthetic nodes reaching simulated depletion, wasted trips, reserved-but-unused energy, and fairness among requests.

A key invariant is:

> PollicinoNet may suggest a rendezvous, but software discovery never overrides the electrical safety limits of the physical charger and device.

## What requires real hardware

Start only with safe USB-class equipment:

- 3–5 LoRa boards;
- ordinary certified USB power banks;
- low-power sensors or dummy electronic loads;
- measured battery voltage/state where the hardware exposes it safely;
- one or two people carrying the power bank between controlled checkpoints;
- measurement of request delay, handoff success and actual delivered energy using a safe USB meter if available.

Do not connect the experiment to mains wiring, high-voltage batteries, vehicle traction batteries or improvised charging circuits.

## Messina teaching scenario

Place a battery-powered environmental node at a controlled school/outdoor checkpoint while the spare power bank remains at another checkpoint. The node advertises a signed `EnergyNeed`. A student relay from Rometta/Venetico carries the request toward school; another student later takes the reserved power bank to the node and records a handoff receipt.

A second scenario uses three coarse zones such as Villafranca, Rometta and Spadafora with two portable chargers and several synthetic low-battery requests. The class compares scheduling strategies using real contact opportunities but safe low-voltage hardware.

## Privacy / security

- do not expose student identity or exact home location in energy requests;
- use coarse named checkpoints and pseudonymous node IDs;
- authenticate reservations to prevent trivial resource hijacking;
- rate-limit fake `critical` requests;
- charger capability must be verified locally before connection;
- do not infer battery safety from a LoRa message alone;
- log physical handoff separately from person tracking;
- keep the experiment strictly within certified low-voltage equipment.

## Difficulty

**Medium.** The networking objects are simple; the main challenge is safe physical coordination, compatible capability descriptions and avoiding duplicate reservations.

## Research signal

Wireless rechargeable sensor-network research studies mobile chargers that combine energy replenishment with data collection. A 2025 Sensors paper explicitly models joint energy replenishment and data collection with mobile chargers. PollicinoNet uses a much simpler teaching interpretation: humans or vehicles physically carry certified energy stores while the DTN coordinates demand and rendezvous.

Reference:

- https://doi.org/10.3390/s25030956
