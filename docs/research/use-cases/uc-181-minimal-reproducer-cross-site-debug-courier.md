# UC-181 — Minimal Reproducer and Cross-Site Debug Courier

## Problem solved
A failure observed on a student PC, Raspberry Pi, lab robot or offline edge worker may need a huge log, complex environment and many steps to reproduce. Shipping everything over an intermittent network is slow and risks disclosing unrelated files.

UC-181 asks the originating machine or a nearby sandboxed worker to derive the **smallest practical reproducible failing case**, bind it to its exact environment and ferry it to another site for confirmation and later repair.

## Actors / nodes
Failing student/lab machine, local failure-detector, isolated minimization worker, relay board/data mule, remote reproducer (PC/Pi), reviewer/developer, optional Git/Raiatea issue store.

## Why PollicinoNet fits
`failure_id + build_hash + candidate_reproducer_hash + predicate_hash` is tiny. Reproducer archives, minimized inputs, environment closures and logs travel later over a richer bearer; a teacher can send a compact `MORE_EVIDENCE` query back after initial triage.

## Proposed workflow
1. Capture an exact **synthetic/public** failure with UC-062 crash capsule.
2. Define a deterministic failure predicate and environment/dependency manifest.
3. Use local delta debugging or manual minimization to generate candidate reproducer archives.
4. Verify failure reproducibility on source; ferry manifest/result hashes first.
5. Reproduce in an isolated second environment and return `REPRODUCED / NOT_REPRODUCED / FLAKY / ENV_MISMATCH / UNKNOWN`.
6. Link an optional UC-044 patch and UC-081 regression test without silently asserting the bug is fixed.

## Bearers
- **LoRa:** failure/reproducer ID, exact manifest/predicate hash, candidate size, status, bounded evidence request.
- **BLE:** tiny minimized test input or diagnostic packet.
- **Wi-Fi/LAN / Internet:** source bundle, Nix/container-like environment closure, complete logs and CI artifacts.
- **Physical:** laptop/SSD/SD for large dependencies or captured traces.

## Software tests now
Use a small deliberately buggy Python project with 30 input events, where one rare sequence triggers a deterministic exception. Compare full-capture vs minimized reproducer sizes, steps to re-run, failed/passing predicates, distinct architectures and replay with dependencies intentionally mismatched. Inject worker reboot, flaky failure, duplicated candidate, corrupted archive and reviewer that never comes online.

Metrics: minimization ratio, reproduction agreement across workers, bytes ferried, time-to-first-confirmed-reproducer and privacy-sensitive material removed. A minimal failing input need not prove root cause.

## Hardware experiment — Messina
**4–6 relay boards**, 2 student laptops and one school Pi/isolated robot test fixture. The student reproducer travels via a relay/store-and-forward encounter to a school lab in Messina or Venetico. Use only a scripted harmless software crash; for Romeo/robotics start with simulated actuators, no uncontrolled motion.

## Privacy / security
Explicit local allow-list for input capture, scrub credentials/tokens/user documents, encrypt evidence when needed, sandbox reproduced binaries, resource limits, no executable trust by mere receipt (UC-180). Students must opt in to any collection from their devices; prefer school-owned synthetic fixtures.

## Difficulty
**Medium–high** (high if failures are timing-sensitive).

## Relationship to previous use cases
- **UC-062** collects diagnostic crash information; **UC-181** *minimizes and cross-validates a runnable reproducer*.
- **UC-081** runs exact CI jobs and **UC-044** ferries Git history; these are consumers of a confirmed minimal reproducer.
- **UC-127** replays edge inference; UC-181 covers general software/robotics failure predicates and input minimization.

## Validation boundary / reference
For flaky concurrent faults, preserving the failing predicate can be harder than minimizing bytes; outcomes can remain UNKNOWN. Classical delta debugging: Zeller & Hildebrandt, 2002, https://doi.org/10.1109/32.988498.
