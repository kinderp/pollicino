# UC-221 — Application Acceptance Receipt Beyond Bundle Delivery

## Problem and concrete value
A relay can deliver every byte correctly, yet the receiving program may reject the object: the JSON schema is wrong, a Raiatea document cites a missing exact version, or a sensor record belongs to the wrong experiment. A radio-delivery receipt must not be presented as a successful application operation. UC-221 gives the school a way to ask: "Was the message merely delivered, or was it actually accepted by the intended application?"

## Actors and Messina scenario
Originating classroom PC in Messina, 4–6 student relay boards or virtual relay nodes around supervised Villafranca/Rometta/Venetico checkpoints, destination application on a PC/Raspberry Pi, and an optional reviewer. A teacher issues a fictional environmental observation from Messina; a student carries it store-and-forward; the lab in Venetico checks the exact observation schema and either accepts it into a test database or rejects it with an auditable reason. Student identity is not part of the observation payload.

## Why PollicinoNet, and transport/bearer choices
Different acknowledgments may arrive hours apart or out of order. Bind every decision to an exact object ID/hash, intended application ID, schema/policy version, processing attempt, and decision authority. States are distinct:
- RECEIVED_BYTES: transport has the complete object, hash checked;
- VALIDATED_OBJECT: format, identity and permitted schema validated;
- ACCEPTED_FOR_USE: application transaction committed or explicitly authorized;
- REJECTED_FOR_USE: bounded failure reason;
- UNKNOWN: processing has not been evidenced.
Do not infer correctness of the scientific content merely from acceptance.

**LoRa:** tiny object/digest, receipt-request ID, status code, compact rejection reason; **BLE:** receipt exchange or small object; **Wi-Fi/LAN:** full objects and validation logs; **Internet:** optional asynchronous application endpoint; **physical SD/USB carry:** signed full payload and audit evidence. No PHY/MAC change. DISCOVERY advertises capability only; EXACT binds hash and versions; SEMANTIC displays human-friendly status only when grounded in evidence.

## Software-only test (proposed, not executed)
Build two independent local processes and a delayed/reordering queue. Create ten artificial messages with valid/invalid schemas and conflicting versions; inject: good bytes but bad schema, unavailable policy, successful validation but failed database commit, duplicate deliveries, delayed old acceptance, lost acceptance receipt, reboot between validation and commit, an authenticated but wrong application identity, and hash tampering.
Assert: no ACCEPTED_FOR_USE without an exact application commit receipt; duplicate request IDs cannot trigger duplicate side effects; later receipts cannot rewrite unrelated versions; lost receipt results in UNKNOWN rather than success. Report logical false-success count, decision latency, receipt bytes and unresolved states separately from transport delivery rate.

## Real hardware and measurable outcomes
Begin with 4–6 LoRa boards and two laptops at separated supervised school-lab checkpoints. Have one relay physically carry a test object; return a receipt later by LoRa or another relay. Instrument **actual** TX/RX events, bytes verified, application commit IDs and wall/monotonic clock uncertainty. Compare transport-delivery count with validated and accepted count. No field performance estimates are provided until data exist.

## Privacy, security, limitations and difficulty
**Medium-high.** Sign/MAC application decisions using application-specific keys, not merely relay keys; enforce authorization, payload size limits, replay-resistant request IDs, minimal error codes to prevent metadata leakage, bounded retention and no student movement trails. A signed receipt proves the named application **reported** a decision, not that its domain interpretation was scientifically true. No side-effecting actions without a suitable local safety gate.

## Nonduplication check
UC-098 and UC-168 concern forwarding/custody; UC-215 verifies robot docking and exact transfer; UC-175 handles duplicate side effects; UC-221 instead records the separately authorized **application-level acceptance decision after complete transfer**. It can reuse their receipts without renaming them.
