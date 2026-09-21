# UC-097 — Distributed Experiment Campaign and Evidence-Pack Courier

## Idea

Use PollicinoNet itself to coordinate **reproducible physical experiments** across many student nodes that are not simultaneously online. A coordinator publishes one exact signed experiment manifest; nodes receive assignments, execute only the declared safe procedure, preserve raw evidence locally, and later ferry compact result summaries plus evidence-pack hashes back to school.

This turns the future Messina student network into a distributed networking/IoT testbed rather than a collection of manually configured boards.

## Problem solved

Once 10, 20 or more boards are distributed, a physical experiment becomes hard to trust if configuration happens by chat or memory:

- nodes may run different firmware/config versions;
- one group may start a different test window;
- results may arrive without enough metadata to reproduce them;
- failed nodes may silently disappear from the dataset;
- manual copy/paste can detach measurements from their exact experiment definition;
- direct Internet connectivity may be unavailable exactly where the experiment is interesting.

We need a machine-readable answer to:

> Which exact nodes attempted which exact experiment profile, what happened, and where is the supporting evidence?

## Actors / nodes

- experiment coordinator at school;
- distributed student PollicinoNet nodes;
- optional sensors/robots/gateways used by the experiment;
- student relay/store-and-forward nodes;
- evidence collector/analysis workstation;
- optional verifier for firmware/config identity and signatures.

## Why PollicinoNet fits

Experiment manifests and status transitions are small, while raw traces are often large. That maps directly onto the control-plane/bulk-data split.

- **DISCOVERY:** node supports experiment capability/profile X and is eligible for campaign C;
- **EXACT:** campaign ID, manifest hash, software/config hashes, assignment, attempt ID, evidence-pack hash and result schema;
- **SEMANTIC:** labels such as `completed`, `failed`, `partial`, `not-attempted` or `invalid-config` derive from exact evidence.

The same relay mechanism being studied can carry the experiment control/evidence, which is useful but must be documented to avoid circular claims.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** campaign announcement, manifest hash, capability/assignment, start-window token, status, compact summary and evidence-pack hash;
- **BLE:** nearby configuration/status exchange;
- **Wi-Fi/LAN:** full manifest, firmware/config bundles and raw evidence packs;
- **Internet:** optional coordination/upload fast path when available;
- **physical transport:** student laptop/phone/SD carries large traces back to school.

## What we can test now in software

Define an `ExperimentManifest` such as:

```text
campaign_id
manifest_version
purpose
required_capabilities[]
software_hash
config_hash
procedure_id
allowed_actions[]
start_window
stop_conditions
result_schema
evidence_requirements
privacy_class
signature
```

Each execution produces an `ExperimentAttempt`:

```text
campaign_id
manifest_hash
node_id_or_pseudonym
attempt_id
boot_id
software_hash
config_hash
status
summary_metrics
evidence_pack_hash
error_code_optional
```

Test:

- 20 virtual nodes receiving the manifest at different times;
- node running stale firmware/config and being rejected from the result set;
- duplicate assignment and duplicate result delivery;
- node joining after the campaign window;
- interrupted experiment and partial evidence pack;
- campaign cancellation arriving late;
- one result summary whose evidence pack never arrives;
- evidence pack arriving through a different relay from the summary;
- node reboot during an attempt;
- two attempts by the same node with distinct attempt IDs;
- manifest fork/equivocation and optional detection through UC-064;
- comparison of expected participants with `completed / failed / not-attempted / unknown`.

Useful metrics include assignment propagation delay, participation/completion fraction, invalid-configuration count, evidence-pack retrieval delay, bytes of control traffic, missing-evidence rate and reproducibility of analysis from the stored manifest + evidence.

A key rule is:

> Missing nodes and missing evidence must stay visible in the dataset; they must not be silently dropped to make an experiment look cleaner.

## What requires real hardware

A first physical campaign should use 5–10 boards and a harmless procedure such as:

- exchange a fixed set of discovery messages;
- record contact opportunities for a bounded window;
- perform a known BLE/Wi-Fi handoff attempt;
- log RSSI/SNR/PDR only where already supported by the frozen implementation;
- return the raw trace as an evidence pack.

Every physical measurement remains empirical. The campaign system may improve reproducibility and provenance, but it does not make the measured radio results universally valid.

After this works locally, distribute nodes across controlled school/public checkpoints and repeat the same signed campaign.

## Messina teaching scenario

A coordinator at school publishes one campaign to groups in Messina, Villafranca, Rometta/Venetico and Spadafora. Student relay nodes propagate the manifest even if some groups have no simultaneous Internet path.

A dashboard can eventually show:

```text
campaign C17
  Messina       3/3 completed
  Villafranca   2/3 completed, 1 partial
  Rometta       2/2 completed
  Spadafora     1/2 completed, 1 not yet observed
```

Every row links to exact manifest/config hashes and, when recovered, the corresponding evidence packs. This gives students a real lesson in experimental method, missing data and reproducibility.

## Privacy / security

- use coarse checkpoint IDs and experiment-scoped pseudonyms;
- do not encode home addresses or private schedules in assignments;
- sign experiment manifests and enforce an allow-list of safe actions locally;
- a remote manifest must never override physical/safety limits on the node;
- include explicit start/stop windows and cancellation semantics;
- separate `not observed` from `failed` and `did not participate`;
- minimize personal metadata in evidence packs;
- hash/sign evidence manifests so relays cannot silently alter them;
- require consent before assigning student-owned devices to experiments that consume noticeable battery/storage/data;
- emergency/civil-protection profiles remain drills until independently validated.

## Difficulty

**Medium-high.** The envelope/state machine is manageable; the challenge is strict provenance, late/cancelled campaigns, heterogeneous capabilities and making missing evidence explicit.

## Why this is distinct from nearby use cases

- **UC-053:** tasks sensors to collect observations; UC-097 orchestrates arbitrary safe PollicinoNet experiments with exact manifests and evidence packs.
- **UC-069:** stages firmware rollout; UC-097 may reference firmware hashes but its goal is experimental reproducibility, not update deployment.
- **UC-081:** distributes software CI/test jobs; UC-097 coordinates physical/network experiments on distributed hardware.
- **UC-008:** is one specific observatory experiment; UC-097 can become the generic mechanism used to run future UC-008 campaigns reproducibly.

## Research / implementation signal

The networking community is placing renewed emphasis on testbed-driven, reproducible and hardware-in-the-loop validation. ERN 2026, colocated with NoF 2026, explicitly focuses on experimental networking, reproducible methodologies and real hardware/testbeds. A 2026 Experiment-as-a-Service research platform likewise uses machine-readable experiment descriptors to support reproducible wireless trials. These are strong signals that experiment description, orchestration and evidence provenance are first-class infrastructure, not administrative afterthoughts.

References:

- https://andreamarotta.github.io/ern-workshop/
- https://arxiv.org/abs/2603.16356
