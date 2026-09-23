# UC-105 — Offline Threat-Indicator Match and Incident-Triage Courier

## Idea

Let disconnected lab, robot and IoT nodes receive small signed **threat-indicator bundles**, match them locally against their own recent telemetry/logs, and return only a bounded triage result unless richer evidence is explicitly requested.

The first profile is defensive and synthetic. It is not an exploitation or remote-scanning system.

```text
indicator bundle -> local match -> compact result -> optional evidence request
```

## Problem solved

UC-039 answers a mainly inventory-oriented question: *is this device/software version affected by a known vulnerability?*

A different problem appears after suspicious activity is discovered:

- a hash, domain, process name or other indicator becomes relevant;
- some devices are currently disconnected;
- their raw logs may be large and privacy-sensitive;
- we want to know which nodes have a possible local match before collecting detailed evidence.

UC-105 moves the **question to the logs**, rather than centralizing every log first.

## Actors / nodes

- school/lab security coordinator;
- student/lab PCs used only with synthetic test data;
- robot/IoT nodes;
- student relay/store-and-forward nodes;
- local matcher;
- optional incident-review workstation;
- optional Internet gateway importing authoritative machine-readable indicators.

## Why PollicinoNet fits

Indicator identifiers, validity windows and match summaries can be much smaller than the underlying logs.

- **DISCOVERY:** `indicator-set epoch E available`, `triage result ready`;
- **EXACT:** indicator-set hash/signature, matcher version, observation-window ID, result/evidence hash;
- **SEMANTIC:** categories such as `suspicious-domain` or `unexpected-binary`, used for explanation and prioritization only.

LoRa carries compact advisory/control state. Detailed logs or forensic bundles move only through BLE/Wi-Fi/LAN/physical transport after policy and authorization permit it.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** indicator-set ID/hash, validity/expiry, compact `NO_MATCH / MATCH / UNKNOWN`, evidence-ready status;
- **BLE:** local retrieval of a bounded evidence capsule;
- **Wi-Fi/LAN:** full indicator bundle, larger logs and review artifacts;
- **Internet:** import of trusted CTI feeds at connected gateways;
- **physical transport:** encrypted USB/SSD or returned device when richer evidence must be reviewed offline.

## What we can test now in software

Create a harmless synthetic telemetry corpus containing:

- made-up domains/IPs;
- known demo file hashes;
- synthetic process names;
- timestamps inside/outside validity windows;
- missing log periods;
- one deliberately forged indicator bundle.

Implement an intentionally small indicator subset inspired by STIX concepts, then test:

- exact hash/domain match;
- indicator expiry;
- superseded/revoked indicator set;
- `NO_MATCH` versus `UNKNOWN` when telemetry is incomplete;
- duplicate indicator delivery;
- delayed result arriving after a newer indicator revision;
- false-positive triage labels;
- evidence request bound to the exact result and observation window;
- privacy-preserving summaries that avoid returning raw browsing or process histories;
- rate limits against a coordinator that asks overly broad questions.

Useful metrics include indicator propagation delay, nodes reaching a determinate triage state, false-positive/false-negative rate on the **synthetic labelled corpus**, evidence bytes requested and amount of raw telemetry kept local.

## What requires real hardware

The first hardware stage should remain a benign lab drill:

- 3–5 PollicinoNet boards;
- 2–3 PCs/Pi devices producing scripted synthetic logs;
- an isolated school/lab network;
- one signed indicator set;
- one node deliberately containing a known demo match;
- delayed relay propagation and optional retrieval of an encrypted evidence capsule.

Do not deploy malware, intentionally vulnerable Internet-facing services, credential stealers or other harmful payloads. The physical experiment is about **distributed triage semantics**, not offensive security.

## Messina teaching scenario

A coordinator at school publishes a signed synthetic indicator set after a classroom incident exercise. Nodes in Messina, Villafranca and Rometta/Venetico are not all online simultaneously.

Each device matches the indicators against a pre-generated local dataset and returns one compact result:

```text
MATCH: 1
NO_MATCH: 2
UNKNOWN_INCOMPLETE_LOG: 1
NOT_SEEN: 2
```

Only the matching node is later asked for the exact small evidence capsule over Wi-Fi. Students can compare this with the privacy cost of uploading every log from every node.

## Privacy / security

Security telemetry is highly sensitive.

- never broadcast raw browsing, DNS, process or file histories over LoRa;
- use synthetic data for classroom experiments;
- authenticate and version indicator publishers;
- support revocation/expiry and reject rollback;
- keep `UNKNOWN` distinct from `NO_MATCH`;
- encrypt results when device identity is sensitive;
- minimize observation windows and retained telemetry;
- do not expose student identities on incident dashboards;
- require explicit authorization before richer evidence retrieval;
- do not make automated punitive or disciplinary decisions from a triage match.

## Difficulty

**Medium–High.** Compact distribution is straightforward; safe indicator semantics, incomplete-log handling, privacy and provenance are the important parts.

## Why this is distinct from UC-039

- **UC-039:** `known vulnerability advisory -> compare against software/device inventory -> affected/fixed/unknown`.
- **UC-105:** `observed-threat indicator -> compare against local telemetry/log window -> match/no-match/unknown -> optional evidence`.

They can compose: UC-105 may discover suspicious evidence, while UC-039 can separately determine whether a vulnerable software version explains it.

## Standards signal

STIX 2.1 defines machine-readable cyber-threat information and an `Indicator` object with structured detection patterns and explicit validity windows. The current OASIS STIX 2.1 material also includes Errata 01 published on 2 April 2025. PollicinoNet should initially implement only a tiny safe subset suitable for synthetic lab exercises, not a full CTI platform.

References:

- https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html
- https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html
