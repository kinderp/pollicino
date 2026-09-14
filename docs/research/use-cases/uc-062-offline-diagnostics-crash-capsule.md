# UC-062 — Offline Diagnostics and Crash Capsule

## Idea

Let deployed PollicinoNet nodes report **small health/crash summaries immediately when a relay appears**, while keeping full logs, core dumps and traces locally until a richer bearer is available.

This is a practical network-operations use case for the PollicinoNet deployment itself: when student-carried boards are distributed across Messina province, some will reboot, crash, fill storage, lose configuration or run an old firmware build. We need to learn what happened without assuming Internet or a technician is physically present.

## Problem solved

A sparse field deployment is hard to debug. By the time a board returns to the lab, volatile information may be lost and the developer may not know:

- which firmware/build was running;
- why the node reset;
- whether a stored crash dump exists;
- queue/storage pressure at failure time;
- battery/power-reset symptoms;
- radio/application error counters;
- which exact larger log artifact should be retrieved later.

Streaming logs continuously would waste bandwidth and energy. PollicinoNet can instead carry a compact `DiagnosticCapsule` and fetch full evidence only when useful.

## Actors / nodes

- deployed LoRa board/sensor/robot node;
- student relay/store-and-forward nodes;
- teacher/developer diagnostic workstation;
- optional school server storing firmware symbols/build artifacts;
- optional rich-bearer collector;
- optional UC-039 advisory/remediation workflow and UC-009 signed update workflow.

## Why PollicinoNet fits

Diagnostics naturally separate into a tiny summary and a larger evidence object.

- **DISCOVERY:** `fault pending`, crash signature, firmware/build ID, severity class and evidence-available bit;
- **EXACT:** boot/crash ID, firmware hash, reset reason, coredump/log object hash, configuration root and diagnostic schema version;
- **SEMANTIC:** labels such as `watchdog`, `assert`, `storage-full`, `unexpected-reset`, useful for triage but not a substitute for exact evidence.

LoRa moves compact fault state; full logs/core dumps move later over BLE/Wi-Fi/LAN/Internet or physical carry.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** diagnostic capsule, boot counter, build ID, reset reason, queue/storage summary and evidence hash;
- **BLE:** nearby diagnostic fetch from a technician/student phone or laptop;
- **Wi-Fi/LAN:** complete coredump, trace, log bundle, symbols or remediation artifact;
- **Internet:** optional remote issue/telemetry upload when available;
- **physical transport:** board/SD card/relay carries the stored dump back to the lab.

## What we can test now in software

Use an emulator or a small test firmware that deliberately generates harmless failures.

Implement:

- canonical `DiagnosticCapsule` with boot ID, build hash, reset reason and evidence references;
- persistent monotonic boot/crash counter where hardware permits;
- deliberate assert/watchdog/reboot/storage-pressure simulations;
- duplicate/reordered capsule delivery;
- one crash summary linked to one exact full log/core-dump object;
- symbol/build mismatch rejection when decoding evidence;
- retention limits for old dumps;
- repeated identical crash signatures aggregated without losing exact event IDs;
- health heartbeat distinguished from fault report;
- remediation state that links UC-039 advisory or UC-009 firmware update to the observed fault without silently declaring it fixed;
- privacy scan ensuring logs do not leak unrelated credentials/user content;
- metrics: fault-to-summary delay, fault-to-evidence delay, diagnostic bytes per bearer, repeated-crash count, evidence retrieval success and time-to-reproduction.

A useful invariant is:

> a compact crash label helps triage, but the exact firmware/config identity and retained evidence remain necessary for diagnosis.

## What requires real hardware

- 3–5 real development boards;
- one or more deliberately injected harmless faults/reboots;
- local non-volatile storage for at least a small diagnostic artifact on some nodes;
- a moving student relay;
- real LoRa crash-summary transfer;
- at least one BLE/Wi-Fi/LAN retrieval of the exact stored evidence;
- measured effect of diagnostic traffic on ordinary queue/backlog behavior.

Do not intentionally stress batteries, power electronics or hardware beyond safe vendor limits. Fault injection should remain software-level or use controlled normal resets.

## Messina teaching scenario

Distribute several development nodes among student groups in coarse areas such as `Messina`, `Villafranca/Rometta` and `Spadafora/Venetico`. Each board runs a known test build. One node is configured to trigger a harmless assertion after a scripted event; another experiences an ordinary controlled reboot; another stays healthy.

A relay later encounters the nodes and brings back only their `DiagnosticCapsule`s. The class identifies which exact evidence objects are worth retrieving. During a later rich-link contact, only the selected coredump/log bundle is transferred to the lab and decoded against the matching firmware build.

This is valuable even before PollicinoNet becomes an application platform because it directly improves the maintainability of the real teaching network.

## Privacy / security

Diagnostic artifacts can be extremely sensitive.

- never broadcast raw memory/core dumps over LoRa;
- minimize the capsule to fault metadata and opaque evidence hashes;
- encrypt private diagnostic bundles at rest/in transit where appropriate;
- redact credentials, tokens, personal messages and unrelated user data from logs;
- sign/authenticate build identity and diagnostic schema;
- restrict who may retrieve full evidence;
- rate-limit fault storms so a crashing node cannot monopolize storage/radio queues;
- preserve the distinction between `observed`, `suspected cause` and `confirmed fix`;
- treat malformed dumps as untrusted input to host-side parsers.

## Difficulty

**Medium–High.** Compact fault reporting is straightforward; durable crash capture, privacy-safe evidence, build/symbol provenance and reliable retrieval after repeated failures require care.

## Research / deployment signal

Modern embedded RTOS tooling already supports storing crash evidence for later offline debugging. Zephyr's coredump subsystem can capture registers/memory to backends including flash and later feed the dump to a debugger. UC-062 adds a delay-tolerant discovery/retrieval layer around that established diagnostic pattern so distributed nodes can announce a fault before the full dump is physically or richly reachable.

References:

- https://docs.zephyrproject.org/latest/services/debugging/coredump.html
- https://docs.zephyrproject.org/latest/doxygen/html/group__coredump__apis.html
