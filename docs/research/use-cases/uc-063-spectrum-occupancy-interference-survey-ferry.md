# UC-063 — Spectrum Occupancy and Interference Survey Ferry

## Idea

Use distributed PollicinoNet boards as a **privacy-aware RF field notebook**. Each node records small, local observations about channel activity, noise/interference indicators and the radio configuration under which the observation was made. Student relays later carry those observations back to a school analysis node.

This is different from UC-008. UC-008 asks **which PollicinoNet nodes meet and for how long**. UC-063 asks **what the local radio environment looked like**, including places/times where no useful peer contact happened.

The goal is not to change or optimize the frozen LoRa PHY during use-case work. The goal is to collect evidence that may later explain why some measured contacts work better than others.

## Problem solved

When a real student network behaves differently across Messina province, a contact trace alone may not explain why. A weak or failed contact could be associated with:

- different local RF activity;
- a noisy location;
- temporary interference;
- indoor/outdoor context;
- antenna orientation or placement;
- a different configured channel/SF/BW observation context;
- simply no transmitting PollicinoNet peer being present.

Without separate RF-environment observations it is easy to over-interpret one failed packet as a range limit.

## Actors / nodes

- student-carried PollicinoNet boards;
- optional fixed reference nodes at school or controlled test locations;
- a school-side analysis node;
- optional student relay/store-and-forward nodes that carry observation batches;
- synthetic RF-observation generators for software-only testing.

## Why PollicinoNet fits

RF observations are small, naturally delay tolerant and useful even if uploaded hours later.

- **DISCOVERY:** `survey batch available`, coarse zone, measurement profile and observation count;
- **EXACT:** exact radio profile/config ID, timestamp/time-uncertainty, observation IDs and signed/hash-bound survey batch;
- **SEMANTIC:** labels such as `quiet`, `busy`, `suspected-interference`, useful only as derived interpretation and never a replacement for raw measured fields.

LoRa can transport compact summaries or request missing survey batches. Larger logs can wait for BLE/Wi-Fi/Internet or physical return to school.

Nothing in this use case modifies the frozen LoRa PHY.

## Possible bearers

- **LoRa:** batch ID, coarse zone, radio-profile ID, compact occupancy/noise summary and `survey available` metadata;
- **BLE:** local survey-log retrieval from a student phone/laptop;
- **Wi-Fi/LAN:** complete observation batch upload and analysis;
- **Internet:** optional central dashboard synchronization;
- **physical transport:** a student device carries the stored measurement log until it reaches school.

## What we can test now in software

Create a synthetic `RfObservation` contract containing only fields the target radio/firmware can actually obtain, for example:

```text
observation_id
radio_profile_id
coarse_zone
time_checkpoint + uncertainty
measurement_type
measured_value(s)
measurement_duration
firmware/build_id
```

Then test:

- synthetic quiet/busy/intermittent RF traces;
- delayed and duplicate observation batches;
- aggregation by coarse zone and time window;
- strict separation between measured values and derived labels;
- joining UC-063 observations with UC-008 contacts without requiring precise student trajectories;
- missing measurements and heterogeneous board capabilities;
- clock uncertainty and rebooted nodes;
- detection of impossible/malformed values;
- comparison of compact summaries with exact retained observations;
- retention policies that discard old raw traces while preserving aggregate teaching datasets.

Useful software metrics include batch size, observation backlog age, missing-observation rate, aggregate error versus the synthetic ground truth and correlation with synthetic contact failures.

A key invariant is:

> absence of a detected signal is not automatically evidence of an empty spectrum, and a failed peer contact is not automatically a range measurement.

## What requires real hardware

Any statement about real RF conditions requires real boards and controlled measurements.

A useful first campaign needs:

- 3–6 boards with the exact target radio hardware;
- a frozen, documented observation profile;
- repeated measurements at controlled checkpoints;
- a few known test transmissions plus periods with no planned transmitter;
- measured RSSI/SNR and/or CAD/activity fields only where the hardware exposes them correctly;
- one student relay that carries stored survey batches back to the collector;
- repeated observations at different times before drawing conclusions.

Record antenna, board revision, firmware build and configuration. Do not convert these observations into coverage/range claims unless paired with the appropriate transmission/contact measurements.

## Messina teaching scenario

Define a small set of coarse, public test zones such as `school`, `Villafranca checkpoint`, `Rometta checkpoint`, `Spadafora/Venetico checkpoint` and one indoor location. Student groups run the same short observation script at agreed times.

The boards do not upload continuously. They retain the survey locally; later student relays or a school Wi-Fi contact return the batch. The class overlays UC-063 RF-environment observations with UC-008 contact traces and asks questions such as:

- did a repeatedly poor contact coincide with a consistently different RF environment?
- did results change between indoor and outdoor checkpoints?
- are apparent differences repeatable on another day?

The exercise is about measurement discipline, not about declaring a best LoRa configuration.

## Privacy / security

RF logs become privacy-sensitive if they are tied to precise locations and persistent student identities.

- use coarse named checkpoints, not home coordinates;
- avoid stable student identity in survey payloads;
- do not record unrelated BLE/Wi-Fi device identifiers;
- keep raw timing/location data for the minimum necessary period;
- authenticate survey batches so fabricated measurements are distinguishable;
- preserve firmware/radio-profile provenance;
- treat interference/jamming labels as hypotheses unless independently verified.

## Difficulty

**Medium.** The data model and store-and-forward path are straightforward. The difficult part is measurement discipline: understanding what the radio actually measures, keeping configurations comparable and resisting the temptation to turn a few observations into unsupported physical claims.

## Research / deployment signal

Recent LoRa work continues to emphasize measurement-based characterization, interference/robustness and channel-activity mechanisms. CAD can detect LoRa preamble activity under a configured radio profile, while RSSI/SNR measurements are strongly environment- and configuration-dependent. UC-063 therefore treats these as field observations whose meaning is bound to exact measurement context, not as universal coverage estimates.

References:

- https://www.mdpi.com/1424-8220/25/5/1602
- https://www.mdpi.com/2673-8732/6/3/47
- https://www.mdpi.com/1424-8220/26/4/1152
