# UC-037 — Privacy-Safe Mobile Environmental Transect

## Idea

Use student-carried PollicinoNet nodes as **mobile environmental samplers** during controlled activities, then reconstruct only a coarse spatial/temporal environmental picture instead of storing each student's continuous route.

The first sensors should be harmless teaching sensors such as temperature/humidity. Air-quality or other sensors can be added only after calibration/provenance is handled explicitly through UC-031.

## Problem solved

Fixed sensors provide good time series at one location but poor spatial coverage. Student nodes already move through different areas, so controlled mobility can sample a wider region without installing permanent infrastructure everywhere.

The challenge is to obtain useful environmental coverage without turning the exercise into student tracking.

## Actors / nodes

- student-carried LoRa boards;
- temperature/humidity or other calibrated teaching sensors;
- school/lab base node;
- student relay/store-and-forward nodes;
- optional fixed reference sensor;
- optional map/visualization node.

## Why PollicinoNet fits

The network already treats mobility as a bearer rather than a failure.

- **DISCOVERY:** coarse test-zone/epoch coverage and which batches exist;
- **EXACT:** sensor ID, calibration/config version, sample batch hash and exact evidence object;
- **SEMANTIC:** environmental interpretation, labels and map visualization.

LoRa can advertise small batch summaries or coverage needs. Full sample batches can move later over BLE/Wi-Fi or by physical carry.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** coarse cell/epoch summary, batch availability, missing-zone request and small sensor status;
- **BLE:** nearby batch sync;
- **Wi-Fi/LAN:** full sample-batch upload at school/home/lab;
- **Internet:** optional final aggregation/public-data enrichment;
- **physical transport:** student node carries stored batches until it reaches another PollicinoNet or school node.

## What we can test now in software

Create synthetic routes that traverse **coarse public test cells**, not home addresses.

Test:

- sample batching by coarse cell + time window;
- delayed store-and-forward delivery;
- duplicate batch suppression;
- missing-cell discovery;
- map reconstruction from incomplete batches;
- deliberate sensor drift and integration with UC-031 calibration manifests;
- uncertainty/error fields instead of treating every reading as equally trustworthy;
- rotating node identity so the final dataset cannot trivially reconstruct one student's whole trajectory;
- comparison of fixed-sensor-only coverage against controlled mobile-sampling coverage in simulation;
- aggregate-only publication using UC-035 when raw per-sample data is unnecessary.

Useful metrics include coarse-cell coverage, sample freshness, backlog delay, duplicate traffic, calibration-version freshness and privacy leakage tests on synthetic trajectories.

## What requires real hardware

- 3–6 boards with simple temperature/humidity sensors;
- one fixed reference sensor where practical;
- controlled repeated walking routes or school-area test zones;
- measured contact/store-and-forward behavior;
- real sensor calibration/co-location before claiming accuracy;
- explicit comparison between raw routes and privacy-reduced cell batches to ensure the latter does not trivially reconstruct participant movement.

No environmental accuracy, geographic coverage or LoRa range claim should be made from the simulator.

## Messina teaching scenario

A good first field exercise is not province-wide tracking. Define a few **public/coarse test zones** around the school or another authorized area and let small student groups walk different controlled paths during a lesson.

Each node stores temperature/humidity samples locally, binds them to the current sensor calibration version, and emits only coarse coverage/batch metadata through LoRa. Full batches arrive at the school node later through Wi-Fi or physical carry.

A later, opt-in research exercise could compare different coarse environments across the Messina hinterland—coastal, urban and hillside—without storing home-level coordinates or continuous individual trajectories.

## Privacy / security

Location is the main risk.

Requirements should include:

- opt-in participation for real mobility experiments;
- coarse public test cells instead of precise home/route locations;
- rotating/pseudonymous node identifiers;
- no continuous individual trajectory in the central dataset;
- short retention for raw local location where location is needed at all;
- aggregate publication rather than raw person-linked samples;
- calibration/provenance attached to environmental claims;
- separate authorization for any richer sensor that could capture personal information.

A mobile crowdsensing dataset can still leak identity/location even when names are removed, so "pseudonymous" must not be described as anonymous.

## Difficulty

**Medium.** The networking and batching are straightforward. The difficult parts are privacy-safe geospatial design, sensor calibration and disciplined interpretation of noisy environmental data.

## Research signal

Mobile crowdsensing remains useful for socio-environmental data but current work continues to emphasize geoprivacy and location masking. Recent environmental IoT research also combines LoRa and Wi-Fi for self-organizing monitoring. These are useful design signals for a teaching experiment, not evidence of PollicinoNet's field accuracy.

References:

- https://www.tandfonline.com/doi/abs/10.1080/00330124.2026.2656680
- https://doi.org/10.1016/j.pmcj.2025.102125
- https://eprints.whiterose.ac.uk/id/eprint/236382/
