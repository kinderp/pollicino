# UC-223 — School Courtyard Shade-vs-Sun Paired Microclimate Experiment Ferry

## Problem and educational value
A class wants to investigate how two nearby courtyard locations differ in measured temperature under sun/shade, but the sensors are not always online and the observations may arrive after school. Missing readings, different sensor shielding or time misalignment can create a false difference. We want defensible **paired experimental evidence**, not a heat-health rating or weather service.

## Actors and Messina scenario
Two school groups, 4–8 LoRa boards/relay nodes, at least two shielded temperature/humidity probes, a comparison/reference instrument if available, teacher data reviewer and a lab collector. Use authorized locations in school grounds around Messina, Villafranca, Rometta or Venetico; if only one school participates, emulate separated sites inside the same campus. Students can ferry bounded observations through store-and-forward relays without collecting their routes.

## Why PollicinoNet; bearers
Each observation batch has tiny useful metadata: site category (sun/shade, no precise coordinates), sensor ID/pseudonym, calibration/siting revision, interval ID, sample count, uncertainty, missing-data count and exact log hash. Delayed relays preserve provenance and enable later paired comparison.
- **LoRa:** compact paired interval summaries, data-gap notices, exact batch/hash IDs.
- **BLE:** sensor setup and nearby log access.
- **Wi-Fi/LAN:** complete time series, configuration photos without people, analysis and plots.
- **Internet:** optional public reference weather data or secure transfer to school.
- **Physical USB/SD:** complete offline time-series archive.
Never broadcast precise student routes, faces or private schedules.

## Software-only experiment (proposed, not executed)
Generate 48 aligned synthetic time bins with known controlled sun/shade difference plus sensor offsets and random noise. Inject clock offset, uneven shade exposure, sample dropouts, sensor swaps, shielding errors, stale calibration, one corrupted batch and late duplicate arrival. Pair only bins with compatible duration, calibration and observation conditions. Report: matched pairs, excluded pairs with reasons, uncertainty, estimated paired difference and sensitivity to missingness. An intentionally wrong pipeline that treats missing as zero must fail validation.

## Future physical experiment and boundaries
Begin with 4–8 LoRa boards, two similar sensors in radiation shields, reference thermometer and two authorized fixed school sites. Run crossover: swap sensors between positions on different sessions while preserving siting records. Log local temperature/humidity, ambient exposure description and actual packet transfers independently. Compare **measured** paired differences, batch completeness and received bytes. For any climatological inference, examine siting, exposure and calibration using WMO-No. 8 measurement guidance. Ordinary low-cost unshielded sensors must not be presented as meteorological-grade or sufficient to certify human heat safety.

## Privacy/security and difficulty
**Medium.** Approvals for installations and electrical/weatherproofing; avoid images of people and home coordinates; sign/MAC data batches; flag unknown calibration; prefer site-role labels to precise locations; short retention of raw network contact logs. If personal comfort feedback is ever collected, it is a separate consent/governance study and is out of scope here.

## Nonduplication check
UC-197 ferries general fire-weather station readings; UC-037 follows a mobile environmental transect; UC-166 handles opportunistic sensor cross-calibration; UC-187 coordinates generic science rounds. UC-223 specifically tests **paired shade/sun causal-comparison hygiene with sensor crossover, asynchronous time alignment and exclusion accounting** at fixed school courtyards. Results are experiment-specific, not a universal cooling benefit.

Reference: WMO Guide to Instruments and Methods of Observation (WMO-No. 8), https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8
