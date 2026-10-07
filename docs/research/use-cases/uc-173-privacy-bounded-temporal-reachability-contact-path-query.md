# UC-173 — Privacy-Bounded Temporal Reachability and Contact-Path Query

## Problem solved
After a delayed-delivery failure or a controlled emergency/network exercise, we may want to answer a narrow question such as: **was there any plausible store-carry-forward path from checkpoint A to checkpoint B between time T0 and T1?** Centralizing every student's full encounter history would answer the question, but would create an unnecessary tracking dataset.

UC-173 studies a bounded query-to-local-history approach: each node keeps its encounter history locally and contributes only the minimum evidence needed to establish, refute or leave unknown one temporal-reachability question.

## Actors / nodes
Student relay boards, authenticated school/public checkpoints, query issuer, local encounter-log processors, optional verifier/aggregator.

## Why PollicinoNet fits
PollicinoNet already has encounter capsules, contact observation, delayed receipts and query-to-data patterns. Temporal reachability is naturally delay tolerant: the query can move to where the logs live, and compact candidate/witness evidence can return later without exporting complete trajectories.

The result must remain explicit: REACHABLE, NO_EVIDENCE, UNKNOWN, or CONFLICTING, with a time-uncertainty bound where relevant.

## Bearers
- LoRa: query ID, bounded time window, checkpoint classes, compact partial-reachability hints and result status.
- BLE/Wi-Fi/LAN: larger signed encounter fragments or proof material selected after a match.
- Internet: optional later verification/aggregation.
- Physical transport: offline trace/evidence packs for controlled experiments.

## Software test now
Generate a time-expanded contact graph with known ground truth, then split the trace across simulated nodes. Test exact/no path, missing logs, pseudonym rotation, clock uncertainty, contradictory evidence and a query whose privacy policy hides one intermediate node.

Compare centralized ground truth, naive raw-log collection, and bounded local query with minimal evidence. Metrics: correctness class, metadata disclosed, bytes exchanged, nodes consulted and unresolved-query rate.

## Real hardware
Use 8–15 boards divided among 3–4 school/public islands. Run scripted encounters and later issue bounded reachability queries. Start with synthetic node identities and public/checkpoint locations only. Physical results must report only actually observed contacts and query outcomes; do not infer provincial coverage or mobility statistics from the scripted trial.

## Messina / provincial teaching scenario
A bundle is injected at a school/public checkpoint in the Messina area and is expected to reach another checkpoint through students acting as relay/store-and-forward nodes. After the exercise, ask whether a temporally valid path **could have existed** during a bounded window without collecting everybody's complete movement history.

## Privacy / security
- No home addresses or continuous GPS.
- Query authorization and rate limiting are required.
- Prefer coarse checkpoint classes and short retention.
- Return only the minimum witness evidence required by the experiment.
- NO_EVIDENCE is not proof that two people/nodes never met.
- Do not repurpose the mechanism for health, disciplinary or surveillance decisions.

## Difficulty
**High.**

## Distinct from existing cases
UC-008 observes the contact graph; UC-011 stores pseudonymous encounter capsules; UC-093 reconstructs causal event ordering; UC-098 records actual relay contribution; UC-169 uses encounter history to make forwarding decisions. UC-173 instead answers a **post-hoc bounded temporal-reachability query without centralizing the full encounter graph**.

## Validation boundary
The software phase can validate query semantics against known synthetic ground truth. Any claim about usefulness on the real student network requires real encounter traces and measured disclosure/communication costs.