# UC-146 — Rural Irrigation Need and Water-Budget Courier

## Problem solved
Rural sensor zones may have soil-moisture data and different irrigation needs without permanent Internet access. A shared water budget and recent observations can arrive later through store-and-forward relays.

## Actors / nodes
Soil/environment sensor, optional tank-level sensor, local rule engine, student or vehicle relay, school gateway and experiment observer.

## Why PollicinoNet fits
Small records such as zone ID, measurement summary, calibration ID, need class, water-budget epoch and acknowledgement fit the control plane. High-resolution histories, models and photos can move later on richer bearers. The frozen LoRa PHY is unchanged.

## Possible bearers
LoRa for compact need/status and water-budget metadata; BLE for nearby maintenance; Wi-Fi/LAN for histories and dashboards; Internet when available; physical transport by student/vehicle data mule.

## What we can test now in software
Simulate 3–5 zones with delayed contacts, changing soil state and one shared water budget. Compare timer-only scheduling, local threshold decisions and delayed coordination. Inject duplicated records, old budget epochs, missing tank observations and sensor-calibration changes.

No water-saving claim should be made from simulation.

## What requires real hardware
Start with a harmless tabletop rig using moisture sensors or potentiometers, optional water-level sensing and LEDs as action indicators. Use 4–6 LoRa boards. Later place environmental sensors only at approved school/public test sites.

Any real pump or valve experiment should remain a separately reviewed low-voltage demonstration with local manual limits.

## Messina teaching scenario
School plots or demonstration gardens around Messina, Villafranca and Rometta/Venetico can act as separate zones. Student nodes ferry compact observations between zones and a school coordinator even when no direct Internet path exists.

## Privacy / security
Use public/school sites or coarse zone IDs, not private-property tracking. Preserve sensor calibration provenance, bound the lifetime of coordination records and keep physical actions locally limited.

## Difficulty
**Medium–High.**

## Why this is distinct
UC-003 collects rural sensor data, UC-052 coordinates energy budgets, UC-053 tasks sensors and UC-074 changes sampling policy. UC-146 is a concrete rural water-allocation scenario combining intermittent sensing, shared budget state and later reconciliation.

## Research signal
LoRa/LoRaWAN irrigation and edge-first agriculture remain active research areas in 2026. Those studies motivate the application area but do not establish PollicinoNet range, reliability or water savings.

References:
- https://doi.org/10.65568/gujes.2026.020103
- https://doi.org/10.23939/mmc2026.02.351
- https://agris.fao.org/search/en/providers/122436/records/69958bbfe6c33ba92ad59c65
