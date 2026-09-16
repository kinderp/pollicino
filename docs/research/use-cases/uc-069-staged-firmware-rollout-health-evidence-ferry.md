# UC-069 — Staged Firmware Rollout and Health-Evidence Ferry

## Idea

UC-009 answers **how a disconnected node can receive an authentic firmware/configuration artifact**. This use case asks the next operational question: **how do we update many student boards gradually, observe whether the first group remains healthy, pause when something looks wrong and only then continue to the rest?**

The firmware itself still moves by richer bearers whenever possible. LoRa carries compact rollout state, version identity, health summaries and stop/continue decisions.

## Problem solved

With tens of boards distributed through the province, an update that is validly signed can still contain a bug. Sending it to every node at once maximizes the blast radius.

We need to model:

- small pilot/canary groups before broad deployment;
- exact firmware version and rollout-campaign identity;
- health evidence after reboot;
- nodes that miss one phase and reappear later;
- pause/abort decisions that propagate through a sparse network;
- rollback only when explicitly authorized and safely supported;
- mixed-version operation during a long rollout.

## Actors / nodes

- authoritative release/campaign node at school;
- 5–20+ student boards divided into rollout phases;
- student relay/store-and-forward nodes;
- optional laptop/RPi caches holding the firmware artifact;
- operator/teacher who decides whether a phase may advance;
- optional diagnostics collector from UC-062.

## Why PollicinoNet fits

Rollout control messages are compact and naturally asynchronous.

- **DISCOVERY:** `campaign available`, `node needs version X`, `health report pending`;
- **EXACT:** campaign ID, firmware hash/version, target hardware class, phase, signed authorization, installed-version report and health-evidence hash;
- **SEMANTIC:** coarse health labels such as `healthy`, `degraded`, `failed`, always backed by exact evidence where policy requires it.

LoRa can propagate `PAUSE`, `CONTINUE`, `ABORT`, phase eligibility and compact post-update status even when the actual image is obtained later over Wi-Fi/BLE/LAN or by physical carry.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** campaign ID, version/hash, phase state, health summary, signed stop/continue decision, update-needed hint;
- **BLE:** nearby transfer for small firmware or metadata if measurements justify it;
- **Wi-Fi/LAN:** preferred firmware/image transfer and complete diagnostic logs;
- **Internet:** optional authoritative release source;
- **physical transport:** SD card, laptop or student-carried cache delivers the image while PollicinoNet carries control state.

## What we can test now in software

Build a simulator with 20 virtual nodes and phases such as `2 -> 5 -> 13` without assuming that this is the best real policy.

Test:

- all canaries healthy, then phase advance;
- one canary repeatedly crashes and UC-062 emits a diagnostic capsule;
- `PAUSE` reaches some relays late;
- a node receives an old `CONTINUE` after a newer `ABORT`;
- a board disappears during phase 1 and returns after phase 3;
- duplicate update reports;
- update artifact available from multiple caches;
- mixed firmware versions exchanging normal PollicinoNet traffic;
- health report bound to the wrong firmware hash;
- an attempted rollback to an older release without explicit authorization;
- campaign restart with a new campaign ID after a fixed build is published.

Useful metrics include phase-completion delay, fraction of nodes exposed before an abort converges, stale-control acceptance (which should be zero), bytes per bearer, and diagnostic evidence retrieval delay.

A key invariant is:

> a node may be late, but it must never interpret an older rollout decision as newer simply because that message arrived later.

## What requires real hardware

- at least 5 real boards, preferably identical enough for a first controlled campaign;
- two firmware builds, one of which contains a harmless deliberately detectable fault such as a controlled reboot or failed self-test;
- one or more richer-bearer firmware caches;
- real reboot/health reporting;
- measured time for pause/abort state to propagate through the student relay network;
- measured behavior when a node is absent for one or more phases.

The first hardware campaign must use harmless development firmware only. No safety-critical actuator should depend on the experiment.

## Messina teaching scenario

The school publishes firmware `vNext` for a set of boards distributed among students in Messina, Villafranca, Rometta and Spadafora. Two school-controlled boards are the first phase. One reports a synthetic health failure after reboot. A signed `PAUSE` object is created before the wider phase is authorized.

Student relays then carry that compact decision toward other zones. Boards that later encounter the firmware cache must refuse to join the next phase while the campaign is paused. After a corrected image receives a new exact hash/campaign state, the exercise resumes.

A second campaign can compare a naive all-at-once rollout against staged rollout using the same measured UC-008 contact trace, while keeping simulation results separate from physical claims.

## Privacy / security

- firmware and campaign metadata must be authenticated;
- health reports should identify devices pseudonymously, not students;
- do not place stack traces, memory dumps, credentials or personal data in LoRa health messages;
- bind every report to exact device identity, firmware hash and boot/session ID;
- prevent downgrade/replay with monotonically advancing campaign/trust state;
- pause/abort authority must be explicit and role-scoped;
- a relay carrying an update or decision is not thereby authorized to create one;
- rollback is a separate privileged action and must not be inferred automatically from a failure.

## Difficulty

**High.** The individual messages are small, but safe distributed rollout semantics, stale decisions, mixed versions and recovery behavior need careful state-machine design.

## Research / standards signal

Uptane is a mature secure software-update design that explicitly protects against rollback/replay and binds update metadata to device/version state. Current Mender documentation supports phased deployments, and in May 2026 Mender announced general availability of its MCU client for constrained devices such as Zephyr-based microcontrollers. These systems show that staged rollout and post-update state are operationally important; PollicinoNet's research question is how the control loop behaves when contact itself is delay-tolerant.

References:

- https://uptane.org/docs/2.0.0/standard/uptane-standard
- https://uptane.org/docs/1.1.0/deployment/best-practices
- https://docs.mender.io/overview/deployment
- https://mender.io/blog/official-release-of-mender-for-microcontrollers-mcus-like-zephyr-and-the-micro-device-tier
