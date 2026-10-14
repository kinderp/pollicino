# UC-202 — Controlled Selective-Forwarding and Queue-Loss Audit

## Problem and concrete scenario
A test message was emitted near Villafranca but did not reach a school checkpoint at Rometta. Was it never received by the relay, rejected by policy, discarded by a full queue, lost after a reboot, or selectively not forwarded? A missing destination receipt alone cannot answer this. A controlled experiment can characterize these failures **without treating an actual student as an adversary**.

## Actors / nodes
Synthetic bundle generator and ground-truth sender; 4–8 school-owned relay boards, one designated fault-injection relay; destination checkpoint; experiment observer. Optional two-island test splits Messina/Villafranca and Rometta/Venetico groups.

## Why PollicinoNet fits and precise contract
At a limited number of *consenting lab nodes*, create opaque `probe_id` and a minimal signed receipt sequence `TRANSMIT_ATTEMPT`, `RECEIVED_VERIFIED`, `ACCEPTED_TO_QUEUE`, `OFFERED_NEXT`, `FORWARDED_VERIFIED`, `EVICTED_REASON`. Each claim states its **evidence quality**; missing receipt does not imply misconduct. A trusted simulator schedules failures including deliberate dropping, while the observer compares reports with the known injected ground truth. The production network need not distribute complete per-hop histories.

## Bearers
- **LoRa:** small synthetic probe/bundle, compact receipts where budget allows.
- **BLE:** optional local receipt synchronization after contact.
- **Wi-Fi/Internet:** laboratory log and ground-truth reconciliation.
- **Physical USB/SD:** sealed experiment logs when disconnected; transport of devices between authorized checkpoints.

## Software-only experiment (proposed; not run)
Model 8 nodes, 100 synthetic probes and known packet/contact loss. Baselines: honest forwarding, queue overload, radio receipt lost, deliberate selective drop by object class, delayed receipt, two conflicting logs. Compute a confusion matrix with explicit `UNKNOWN`; false-positive rate for any fault classification is as important as detection. Repeat with non-synchronized clocks and rotated identifiers. Avoid turning an injected-classifier benchmark into a claim of live adversary detection.

## Physical test and measurements needed
4–8 school-owned boards in a supervised laboratory; one firmware-independent *application policy fixture* intentionally refuses or drops synthetic messages on schedule. Do not modify radio PHY. Separate ground-truth transmitter counters, receiver logs and verified destination receipts; power-cycle one node and compare. Measure observed delivery and logging completeness for each injected scenario, never impute lost logs as confirmed drops.

## Privacy, security, difficulty
**High.** Use artificial payloads and temporary probe identities only. No covert monitoring, permanent reputation scores or accusation of participating minors. Authenticated receipts are not automatically trustworthy if the emitting endpoint is compromised; record the trust assumption of each measurement source. Rate-limit extra audit traffic and enforce legal radio airtime.

## Distinction from existing catalog
UC-196 compares independent receiver observations, UC-098 transports bounded delivery receipts, UC-178 accounts for missing logs, and UC-143 estimates liveness. **UC-202 tests causal *forwarding failure modes under controlled fault injection*** and evaluates the risk of wrong attribution.

## Guardrails
Not an intrusion-detection product or disciplinary instrument. PHY LoRa frozen; no measured RF results claimed until field data exist.