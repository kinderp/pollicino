# UC-219 — Opportunistic Compute Independent Result Cross-Check

## Problem
A remote AI/data worker may produce an incorrect result: a correct signature authenticates the sender, not the computation. UC-219 sends exact, bounded jobs to independent workers and preserves `verified`, `disputed` or `unknown` outcomes, even when verification returns much later.

## Actors and practical scenario
Two or three isolated school PCs/Pis (labelled Messina, Villafranca, Venetico), a reviewer, a task owner, and 4–6 relay boards. Students ferry tiny signed result digests; large deterministic test inputs move on higher-capacity links.

## Why PollicinoNet and bearer choice
Store-carry-forward permits asynchronous task submission, independent checking, dispute and review without common online time. **LoRa:** exact job/digest/challenge and disposition. **BLE/Wi-Fi:** logs and full results. **Internet:** optional reference, not mandatory. **Physical:** encrypted SD/USB.

## Software now
Run a deterministic Python job on public synthetic data with fixed code, input and environment hashes. Inject one deliberately corrupted worker, wrong version, mismatched seed, missing checker, duplicates, malicious equivocation and two matching but wrong results. Assign bounded independent rechecks according to explicit cost/criticality policy. Compare detected injected faults, false positives, bytes and delay. Two equal hashes show agreement, **not a mathematical proof of correctness**.

**Acceptance gate:** corruption and version mismatch are never silently accepted as verified; unresolved work stays `unknown` or `disputed`. All decisions include exact manifests and provenance.

## Hardware later
2–3 supervised computers with 4–6 LoRa boards, programmed contact partitions, logged test messages and explicitly injected errors. Measure observed transport/verification delays separately from synthetic traces.

## Privacy, security and distinctness
Synthetic/public datasets only, no private student data. Sandboxed jobs with CPU/time/storage limits; never execute arbitrary received code on a privileged classroom device. Authenticate workers, limit access, preserve minimal reproducers. **Difficulty: high.** UC-061 caches results, UC-081 runs CI and UC-096 verifies builds; UC-219 addresses **generic outsourced computation verification**.
