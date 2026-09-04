# UC-009 — Signed Firmware and Configuration Ferry

## Idea

Maintain isolated sensors, gateways or robots that do not have permanent Internet access. A trusted release node publishes a **signed version manifest**; PollicinoNet announces which version exists and which device needs it. The actual firmware/configuration can travel over Wi-Fi/BLE, by physical carry, or—only for sufficiently small deltas—over the scarce link.

A concrete school experiment could update a spare field sensor in a disconnected classroom/courtyard: a student-carried node learns that the sensor is on version `N`, later obtains version `N+1` from the school server, and delivers the signed update during a later encounter.

## Problem solved

Remote devices become hard to maintain when they have no stable backhaul. Full firmware images may also be much larger than a scarce radio link can reasonably carry. The system needs secure version discovery, staged delivery and safe recovery rather than blind retransmission.

## Actors / nodes

- trusted build/release signer;
- school server or repository mirror;
- isolated sensor/robot/gateway;
- student-carried relay/data mule;
- optional home or lab cache.

## Why PollicinoNet fits

The use case matches PollicinoNet's `DISCOVERY` + `EXACT` split: LoRa can advertise version, update coordinate, expiry and capability hints; the exact signed artifact is resolved and verified later. Content-addressed chunks and previous versions also make differential delivery possible without changing the frozen LoRa PHY.

## Possible bearers

- **LoRa:** current-version beacon, update availability, compact manifest coordinate, status/ack;
- **BLE/Wi-Fi/LAN/Internet:** signed manifest, firmware image, delta patch and logs;
- **physical transport:** student-carried cache, SD card or local device storage when no network path exists.

## What we can test now in software

- signed release manifests and exact hash verification;
- synthetic devices with different installed versions;
- full-image vs chunk/delta delivery planning;
- resume after interrupted transfer;
- staged rollout, expiry and rollback policy;
- power-loss/failure injection during the simulated update state machine;
- anti-replay and anti-rollback checks.

Recent research on incremental LoRa/LoRaWAN firmware updates shows why small deterministic deltas are worth studying, but those results are prior art only and are not evidence for PollicinoNet's frozen bare-LoRa PHY.

## What requires real hardware

- update a **spare/non-critical** board first;
- measure actual bytes, airtime, retries, energy and completion time for the chosen bearer;
- test interrupted transfer and reboot recovery;
- verify rollback on an intentionally invalid or incomplete image;
- never use an unvalidated path for safety-critical field equipment.

## Privacy / security

Firmware/configuration is a high-integrity object. Require authenticated release signing, full cryptographic hash verification, anti-rollback counters, replay protection and authorization per device class. Do not put signing private keys on relay nodes. Treat configuration as potentially sensitive because it can reveal network topology, credentials or device behavior.

## Difficulty

**High.** The data-mule and manifest logic is moderate; safe firmware application, rollback and key management require careful engineering.
