# UC-081 — Offline Distributed CI / Test Farm Courier

## Idea

Turn intermittently connected student laptops, Raspberry Pis and lab machines into a small **delay-tolerant CI/test farm**. An exact source commit plus a test request can move through PollicinoNet, run wherever a compatible worker is available, and return signed/hashed result evidence later.

This is not a replacement for GitHub Actions or a normal CI server when Internet is available. It is an experiment in making software validation survive partitions and heterogeneous local hardware.

## Problem solved

Students may have source code on several machines while connectivity to a central forge/server is unavailable or intentionally removed for the experiment. Some tests also need capabilities that only certain nodes have:

- Linux/x86 versus ARM;
- a particular Python/toolchain version;
- a GPU;
- a LoRa board attached over USB;
- later, a harmless hardware-in-the-loop fixture or Romeo robot.

The questions become:

- who can run this exact test job?
- how do we bind the result to the exact commit/environment?
- what happens if two workers run the same job?
- how do partial results converge when workers are offline at different times?
- how do we distinguish a failed test from a worker that never returned a result?

## Actors / nodes

- developer/student node creating a test request;
- source repository/cache using UC-044 bundle transfer where needed;
- student relay/store-and-forward nodes;
- heterogeneous CI workers: laptops, Raspberry Pis, lab PCs;
- optional school coordinator/dashboard;
- optional UC-061 result cache for already completed deterministic jobs;
- optional UC-062 diagnostics when a worker crashes.

## Why PollicinoNet fits

Most CI coordination metadata is compact; logs/artifacts are not.

- **DISCOVERY:** worker capability, queue state, test-suite class, job availability;
- **EXACT:** repository identity, commit hash, dependency/environment manifest hash, test command/profile, job ID, result/evidence hashes;
- **SEMANTIC:** labels such as `unit-tests`, `arm64`, `hardware-loop`, useful for matching but not authoritative without exact capability/environment binding.

LoRa can advertise jobs, capabilities and result summaries. Git bundles, containers/Nix closures, logs and artifacts move through Wi-Fi/LAN/BLE or physical carry.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** job ID, commit hash prefix/full compact identity as appropriate, capability class, accept/lease state, pass/fail/unknown summary, result manifest hash;
- **BLE:** nearby job handoff and small logs;
- **Wi-Fi/LAN:** repository bundles, dependencies, binaries, test logs and artifacts;
- **Internet:** optional fast path to the forge or package cache when available;
- **physical transport:** student laptop/storage carries the source bundle, dependency cache or returned evidence.

## What we can test now in software

Build a tiny coordinator-less test farm around a public/synthetic repository.

Define a `TestJob` with at least:

```text
repo_id
commit_hash
test_profile
environment_hash
required_capabilities
job_id
expiry
idempotency_key
```

and a `TestResult` with:

```text
job_id
worker_id
commit_hash
environment_hash
started/completed checkpoint
outcome = PASS|FAIL|ERROR|INCOMPLETE
result_manifest_hash
log_hash
```

Test:

- duplicate job propagation;
- two valid workers racing for the same job;
- bounded redundant execution for important jobs;
- wrong commit checked out;
- wrong dependency/environment version;
- worker disappears after accepting;
- test finishes but result receipt is delayed;
- flaky test gives different results on two workers;
- architecture-specific test passes on x86 and fails on ARM;
- result summary arrives over LoRa before the full log;
- exact result already exists in UC-061 cache;
- source bundle arrives after the test request.

A useful rule is:

> `PASS` is meaningful only when bound to the exact commit, test profile and environment identity.

Useful metrics include time-to-first-result, time-to-complete-matrix, duplicate execution, worker utilization, bytes per bearer, stale/invalid result count and evidence retrieval delay.

## What requires real hardware

The first real experiment can use equipment already common in a teaching lab:

- 3–4 laptops/Raspberry Pis with intentionally different environments;
- 3–4 LoRa nodes for control/store-and-forward;
- one repository with a small deterministic test suite;
- one disconnected worker island;
- a student relay carrying job/result state between islands;
- Wi-Fi transfer for the Git bundle/logs.

A later stage can add one harmless hardware-in-the-loop test, for example reading a test sensor or commanding a robot simulator. Real robot motion should remain supervised and constrained; CI must never be allowed to trigger unsafe actuators automatically.

## Messina teaching scenario

This is especially suitable for a programming class. Split students into three islands representing `school`, `Rometta/Venetico` and `Spadafora`. The same project has tests for Python, ARM and one optional hardware profile.

A commit is created in one island. Its compact CI request propagates by LoRa/store-and-forward. Another student's laptop carries the Git bundle when a rich bearer appears. Different workers execute different matrix entries, and result summaries return asynchronously.

The class dashboard may temporarily show:

```text
commit abc123
python-3.13/x86      PASS
python-3.13/arm64    pending
hardware-profile-A   result-known / log-not-yet-retrieved
```

This makes eventual, evidence-bound CI state visible without pretending all machines are simultaneously online.

## Privacy / security

CI workers execute code and therefore require strong containment.

- start with public/synthetic repositories and trusted student code;
- do not distribute repository secrets, tokens or SSH keys to workers;
- run jobs in containers/VMs/sandboxes where practical;
- capability advertisement does not imply authorization to execute arbitrary code;
- bind results to exact commit/environment/test profile;
- sign/authenticate result envelopes;
- treat results from untrusted workers as evidence that may need independent repetition;
- scrub logs for credentials and personal paths/data before propagation;
- never allow an offline CI job to perform irreversible or safety-critical external actions.

## Difficulty

**Medium–High.** A basic worker queue is straightforward. The valuable complexity is reproducibility across heterogeneous environments, delayed evidence, duplicate jobs, trust in workers and exact source/environment binding.

## Why this is distinct from nearby use cases

- **UC-044:** moves Git repository/patch history offline.
- **UC-014:** discovers generic compute capabilities.
- **UC-038:** compares AI model/runtime benchmark behavior.
- **UC-061:** caches completed exact computation results.
- **UC-081:** composes these primitives into a **software-validation workflow with a test matrix, partial asynchronous results and evidence-bound CI state**.

## Research / implementation signal

Local-first developer tools increasingly keep test definitions and execution reproducible without requiring a cloud service, while 2026 work on loosely coupled distributed compute continues to study task orchestration across nodes that can freely join and leave. PollicinoNet can use those ideas while making intermittent physical contact and explicit evidence transport first-class.

References:

- https://doi.org/10.3390/app16073484
- https://git-scm.com/docs/git-bundle
