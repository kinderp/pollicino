# UC-079 — Intermittent Computation Checkpoint and Resume Courier

## Idea

Allow a long-running computation on an intermittently powered or intermittently reachable node to **save exact progress, survive reboot/power loss, and resume later**, potentially on another compatible worker after the checkpoint has been carried through PollicinoNet.

UC-058 moves a local service between hosts. UC-079 is narrower and more correctness-focused: preserve the causal progress of one computation despite repeated interruption.

## Problem solved

A field node, low-power edge device or student Raspberry Pi may lose power, reboot, leave the network or become unreachable while processing a job. Restarting from zero can waste scarce compute/energy and may create inconsistent external actions if the task already emitted partial results.

The hard cases are not simply "save a file":

- checkpoint N+1 arrives before N at another node;
- a stale checkpoint is resumed after newer progress already exists;
- a task is replayed and performs the same external action twice;
- two workers resume the same checkpoint concurrently;
- checkpoint data is corrupted or produced by an incompatible runtime;
- the original device disappears permanently but the job should still be recoverable.

## Actors / nodes

- intermittent worker node;
- stable school/server node or checkpoint sink;
- student relay/data-mule node;
- optional second compatible worker for migration/resume;
- optional UC-061 result cache;
- optional UC-020 time/freshness checkpoint.

## Why PollicinoNet fits

Checkpoint control data is small even when checkpoint payloads are large.

- **DISCOVERY:** task/checkpoint available, worker compatibility, latest-known checkpoint generation;
- **EXACT:** task ID, checkpoint hash, parent checkpoint hash, runtime/image hash, sequence/generation and resume receipt;
- **SEMANTIC:** labels such as `training-step`, `batch-index`, `simulation-epoch`, useful only for display/scheduling.

LoRa can announce durable progress and missing generations. The checkpoint itself moves over a richer bearer or by physical carry.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** checkpoint ID/hash, lineage summary, latest-generation hint, worker capability and resume status;
- **BLE:** nearby checkpoint metadata exchange and small state objects;
- **Wi-Fi/LAN:** checkpoint blobs, container/runtime layers and logs;
- **Internet:** optional remote checkpoint mirror;
- **physical transport:** SD card/laptop/student relay carries exact checkpoint bytes between disconnected hosts.

## What we can test now in software

Start with a deterministic long-running program whose state is explicit, for example a multi-stage data transform or numerical simulation.

Implement a checkpoint envelope such as:

```text
task_id
checkpoint_id
parent_checkpoint_hash
generation
runtime_hash
input_hash
state_hash
created_epoch
external_effect_cursor
```

Then inject failures at arbitrary points:

- process kill;
- host reboot;
- checkpoint write interrupted halfway;
- checkpoint duplicated or reordered in the network;
- stale checkpoint presented as latest;
- worker version/runtime mismatch;
- two workers try to resume the same logical task;
- result emitted, but the acknowledgement is lost;
- latest checkpoint disappears and recovery must fall back to an earlier valid one.

Useful policies/tests:

- append-only checkpoint lineage;
- exact hash verification before resume;
- monotonic generation selection;
- idempotent external-effect markers;
- explicit `orphan`, `superseded`, `resumable`, `completed` states;
- checkpoint frequency tradeoff between lost work and transfer/storage cost.

Useful metrics include lost work after failure, resume success, bytes per checkpoint, recovery latency, duplicate external effects and checkpoint storage overhead.

## What requires real hardware

A first hardware experiment can use:

- 2 Raspberry Pi/laptops or one Pi plus one laptop;
- 2–3 PollicinoNet boards/relay roles;
- a deterministic CPU job lasting long enough to interrupt repeatedly;
- deliberate power removal/reboot of the worker;
- checkpoint retrieval over Wi-Fi after a LoRa discovery/control exchange;
- optional migration to the second compatible worker.

Only measured hardware runs may support claims about restart time, energy saved or reliability.

A later extension can use an energy-harvesting or battery-limited node, but the initial experiment does not need specialized hardware.

## Messina teaching scenario

A small compute job starts on a classroom Raspberry Pi. The node becomes unavailable before finishing. A student's relay later carries the newest checkpoint manifest and, over a richer bearer, the checkpoint blob toward another classroom/lab node.

The class deliberately introduces a stale checkpoint from an earlier generation and verifies that the destination refuses to roll the task backward silently. A second exercise kills the worker after an externally visible but harmless event, such as writing one numbered output record, and checks that resume does not duplicate it.

The scenario can be run entirely within the school first; geographic separation across Messina/Rometta/Spadafora becomes useful only after the correctness model works.

## Privacy / security

Checkpoints can contain far more sensitive state than normal output.

- treat checkpoint blobs as sensitive by default;
- encrypt them end-to-end when relays are not authorized to inspect state;
- exclude secrets, credentials and unnecessary raw memory from checkpoint formats;
- bind checkpoints to exact code/runtime/input identities;
- reject unsigned or hash-mismatched checkpoints;
- make rollback explicit rather than silently accepting older state;
- prevent two workers from causing duplicate irreversible actions;
- use harmless tasks in teaching experiments.

## Difficulty

**High.** Saving state is easy; preserving exactly-once-or-explicitly-reconciled semantics across failures, migrations, duplicate messages and stale checkpoints is the difficult part.

## Why this is distinct from nearby use cases

- **UC-058:** migrates a live/local service and service state between hosts.
- **UC-061:** reuses a completed deterministic computation result.
- **UC-062:** reports crashes and diagnostics.
- **UC-079:** preserves **in-progress computational state and causal recovery** across interruption.

## Research signal

Intermittent edge systems remain an active research problem. 2026 work on causal checkpointing/recovery specifically targets devices that lose power and connectivity and highlights the difficulty of preserving distributed consistency rather than only local checkpoint state. PollicinoNet can reproduce the small, falsifiable parts of that problem without importing external performance claims.

Reference:

- https://doi.org/10.1109/EDGE72783.2026.00033
