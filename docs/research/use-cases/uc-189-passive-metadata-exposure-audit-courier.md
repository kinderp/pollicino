# UC-189 — Passive Metadata Exposure and Linkability Audit Courier

## Idea and problem

Even when payloads are encrypted, a person watching radio transmissions might infer that the same board appears near a checkpoint every morning, identify a group from traffic size/timing or guess what kind of objects it transports. Encrypting bytes alone does **not** prove that a student-operated DTN protects privacy.

UC-189 creates a controlled **passive-observer privacy audit** for PollicinoNet's existing application-visible metadata. It makes leakage measurable without implementing interception, tracking real people or modifying the frozen radio PHY.

## Actors / nodes

Synthetic board identities, student-owned test boards with explicit consent, fixed school/test relay nodes, a local analysis workstation, an offline policy reviewer and a collector of **aggregate risk scores only**.

## Why PollicinoNet fits

In a fragmented store-and-forward network, routing IDs, bundles, receipts, group memberships, contact timing and metadata may survive for days. An audit capsule can ferry bounded observations such as 'same synthetic identity linkable across epochs', 'plaintext content class leaked' or 'suppression policy passed'. The **audit result**, not sensitive raw traces, may move over PollicinoNet.

## Bearers

- **LoRa:** ordinary permitted test traffic and compact audit job/result state only; never introduce a new PHY or surveillance feature.
- **BLE:** optional audited companion metadata and local pairing behavior.
- **Wi-Fi/LAN:** synthetic traffic records and privacy test reports at school.
- **Internet:** optional access-controlled policy review; not needed for the trial.
- **Physical carry:** encrypted test datasets carried between labs.

## Software-only now

1. Create synthetic traffic records for 10–30 virtual relay identities rotating every epoch, with bundles of different classes and intercontact intervals.
2. Model an observer who sees only chosen permitted metadata fields and timestamps (not private payloads), then compare 'no rotation', 'naive ID rotation', 'scoped IDs plus batching' and 'size bucketing'.
3. Measure whether the synthetic observer can link epochs or classify traffic above a documented chance baseline; never call a simulated attack success a real-world privacy measurement.
4. Inject forwarding receipts (UC-098), availability notices (UC-174), vouchers (UC-137) and mailbox discovery (UC-023) to spot accidental reidentification through stable secondary IDs.
5. Generate a minimization report identifying fields that can be suppressed or coarsened **at the application layer**. No packet format/radio change in this phase.

## Real-hardware experiment

Use **4–8 boards inside an authorized laboratory or school test area**, configured with explicitly synthetic identities. Capture only **the experiment's own transmitted diagnostic/application records** on managed test endpoints. Repeat scripted role swaps and ID rotations; compare analysis on collected application metadata with known test identity mapping held in a separate sealed file. Additional receiver/sniffer hardware is not required. Report observer capability assumptions and limitations. Do not eavesdrop on students' everyday traffic.

## Messina scenario

Three simulated roles ('Rometta lab relay', 'Villafranca checkpoint', 'Messina collector') run at school with scripted contact windows mimicking islanded areas. Before any voluntary provincial trial, ask whether an outsider could infer recurring attendance or movement from the public control-plane metadata. Publish only aggregate leakage checks and remediations, never raw paths.

## Privacy and security

Synthetic participants first; privacy-by-design and purpose limitation. No passive surveillance of third-party transmissions; consent and school authorization required for any human participants; separate keys for raw laboratory traces; retention window; audit trails; access controls; no publication of stable node IDs or student contact graphs. Metadata transformations must preserve authorization, delivery correctness and anti-replay semantics; weakening security to hide timing is not acceptable.

## Evaluation and difficulty

**High** because the observer model and ethics matter more than code. Metrics: linkability precision/recall on known synthetic ground truth, unnecessary field count, size/timing inference baseline, retention volume, protocol regressions. A laboratory result does not certify anonymity in a provincial deployment.

## Why distinct

UC-011 models encounter capsules, UC-090 private witness discovery, UC-095/137 volunteer budgets, UC-111 payload redaction and UC-173 private reachability queries. **UC-189 independently audits residual traffic-analysis risk created by the combination of those features**, before student field deployment.

Background: https://www.edpb.europa.eu/edpb_en
