# UC-022 — Multi-Witness Event Corroboration

## Idea

Let several independent sensor/edge nodes report compact claims about the **same possible event**, then correlate those claims before escalating it. The point is to avoid treating one noisy sensor or one edge-AI inference as unquestionable truth.

Examples for controlled experiments include:

- simulated smoke/temperature rise;
- vibration at two nearby points;
- rain/water-level threshold crossings;
- a robot/vehicle observing the same synthetic marker from different positions;
- two edge-AI nodes independently classifying the same public test event.

The result is a signed, auditable `EventClaim`/`CorroboratedEvent` chain, not an operational emergency alarm.

## Problem solved

Sparse IoT networks often have unreliable sensors, false positives, drift or local obstructions. Sending all raw data continuously is expensive and may be impossible. A single semantic alert is cheap, but trusting one alert blindly is risky.

PollicinoNet can instead move compact event claims first and retrieve exact evidence later. Multiple independent witnesses can increase confidence, expose conflicts and prioritize which evidence deserves a richer bearer.

## Actors / nodes

- stationary environmental/IoT sensor nodes;
- edge-AI nodes producing local classifications;
- student relay/store-and-forward nodes;
- optional robot/vehicle/drone acting as a mobile witness or evidence collector;
- correlation node at school/server/field station;
- human operator reviewing the resulting synthetic event.

## Why PollicinoNet fits

This scenario naturally separates the information contracts:

- **DISCOVERY:** "an event claim exists for coarse area/epoch/type";
- **EXACT:** signed sensor sample, image hash, model/version, claim and provenance;
- **SEMANTIC:** local interpretation such as `possible_smoke` or `abnormal_vibration`, kept separate from authoritative evidence.

LoRa can carry compact claims, confidence classes, witness IDs/epochs and evidence hashes. BLE/Wi-Fi/Internet or physical carry can move raw samples/images/logs later. Store-and-forward allows corroboration even when witnesses never have simultaneous end-to-end connectivity.

Nothing here changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact event claims, timestamps/epochs, coarse zones, confidence class, evidence hash and priority;
- **BLE/Wi-Fi/LAN:** raw sensor windows, images, audio or detailed model output;
- **Internet:** optional dashboard and later analysis;
- **physical transport:** student/vehicle relay carries evidence between disconnected groups.

## What we can test now in software

- define signed `EventClaim` objects with source, type, coarse zone, time window, confidence and evidence hash;
- simulate 3–20 sensors with true events, false positives, drift and conflicting observations;
- correlate claims by time/space/type without requiring exact GPS coordinates;
- compare simple `2-of-3` corroboration with reliability-weighted or provenance-aware policies;
- keep `corroborated`, `conflicting`, `insufficient evidence` and `stale` as explicit states;
- replay duplicate and delayed claims through store-and-forward queues;
- attach exact evidence later and verify that it matches the earlier hash;
- model one malicious/compromised witness and ensure one identity cannot cheaply impersonate many independent witnesses;
- measure time-to-corroboration, false escalation count, missing-evidence count and scarce-link bytes;
- test whether UC-020-style time uncertainty changes correlation windows.

A key invariant is:

> semantic agreement between nodes never replaces exact provenance; the system must retain which independent evidence produced the corroborated event.

## What requires real hardware

- 3+ physical sensor/edge nodes producing controlled synthetic stimuli;
- at least one mobile relay so claims arrive with real delay/reordering;
- measured packet delivery/contact windows for the LoRa control path;
- one richer-bearer retrieval of the exact evidence referenced by a LoRa claim;
- repeatable false-positive injections, such as triggering only one sensor, to verify that policy behaves as designed.

Real wildfire, flood, landslide or rescue claims require dedicated domain validation and must not be inferred from a classroom trial.

## Messina teaching scenario

Place three safe sensor nodes in controlled school/lab locations and emulate a "rain/temperature anomaly" using test inputs. A student relay moves between two disconnected groups. One sensor reports first, a second later corroborates it, while a third deliberately disagrees. The school node should produce an auditable state showing why the event is corroborated, conflicting or still uncertain.

A later outdoor exercise can use public environmental measurements or harmless synthetic triggers along controlled routes in the Messina hinterland. Student home locations must not become part of the event dataset.

## Privacy / security

Sensor identity should be authenticated but need not expose a student's identity. Use coarse zones where exact coordinates are unnecessary. Claims require replay protection and provenance; otherwise one compromised node could fabricate many apparent witnesses. Independence assumptions must be explicit: three sensors connected to the same faulty gateway may not count as three independent witnesses.

Images/audio can contain personal data and should stay off LoRa; retrieval requires explicit authorization and minimization. Emergency labels must be clearly marked synthetic during teaching experiments.

## Difficulty

**Medium–High.** Compact claim exchange is simple; the real work is defining independence, confidence, conflict handling and provenance without creating a fake sense of certainty.

## Research signal

Current 2026 IoT work continues to combine multi-node sensing, heterogeneous LoRa/BLE links, edge AI and reliability-aware/multimodal fusion. Recent disaster-monitoring and firefighter systems reinforce the value of local sensing plus compact long-range backhaul. Those external results motivate a controlled PollicinoNet experiment but do not validate our radio range, latency or operational safety.