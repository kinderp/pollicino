# UC-003 — Rural Sensor Courier

## Idea

Use low-power sensor nodes in rural, hilly or coastal areas to collect environmental measurements locally. When a student, teacher or mobile gateway passes nearby, PollicinoNet exchanges a compact backlog summary and carries the missing measurements onward until they reach the school server.

## Problem solved

A sensor can be useful even when it has no permanent Internet path. Continuous infrastructure is replaced by local storage plus opportunistic collection.

## Actors / nodes

- fixed sensor nodes (temperature, humidity, pressure, soil moisture or other non-sensitive measurements);
- student-carried relay nodes;
- school gateway/server;
- optional home/field gateway;
- PollicinoStore caches.

## Why PollicinoNet fits

Sensor streams are naturally chunkable, resumable and often highly redundant. PollicinoNet can advertise what time ranges are available, avoid retransmitting known batches and select between compact summaries, exact missing chunks and richer-link retrieval.

## Possible bearers

- **LoRa:** sensor summaries, backlog inventory, small exact batches and requests;
- **BLE/Wi-Fi:** faster dump when a collector is nearby;
- **Internet:** later upload to the school server;
- **physical transport:** a relay carries stored measurements across disconnected areas.

No PHY change is required or proposed.

## What we can test now in software

- generate synthetic environmental time series;
- batch measurements into content-addressed chunks;
- compare raw, delta and compressed exact representation;
- simulate missed contacts, backlog growth and resumable collection;
- prioritize fresh alarms vs old archival samples without changing the transport PHY;
- measure TRC, delivery latency, storage pressure and reconstruction correctness.

## What requires real hardware

- real sensor + LoRa board integration;
- controlled outdoor collection with a moving relay;
- measured packet loss, RSSI/SNR, timing, battery/energy proxy and recovered sample completeness.

No field result should be inferred from the simulator.

## Privacy / security

Prefer non-personal environmental measurements. Avoid precise private-property coordinates unless explicitly authorized. Sign or authenticate sensor batches where provenance matters, and distinguish missing data from a real physical zero/readout.

## Difficulty

**Low to medium.** It is a strong first real-world case because the payload semantics are simple and most of the protocol can be exercised before field deployment.
