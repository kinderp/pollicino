# UC-175 — Idempotent Side-Effect Command and Duplicate-Suppression Courier

## Problem solved
Store-and-forward systems intentionally retry. That is safe for a document, but dangerous for a side-effecting command: move a servo, start one capture or create one job must not accidentally execute twice because the command arrived through two relays.

UC-175 studies application-level idempotency: **at-least-once delivery with one logical effect**.

## Actors / nodes
Command issuer, relay nodes, safe actuator/robot or software service, execution ledger and optional verifier.

## Why PollicinoNet fits
Retries, duplicates, reordering and delayed receipts are normal in PollicinoNet. A compact control envelope can bind a unique command ID, command fingerprint/hash, authorization and expiry, execution state and result digest. The executor remembers completed IDs long enough to return the previous result instead of repeating the side effect.

## Bearers
- LoRa: compact command envelope, duplicate/result status and receipt.
- BLE/Wi-Fi/LAN: detailed job payload, logs or richer result.
- Internet: optional later audit.
- Physical transport: large job inputs while idempotency state remains compact.

## Software test now
Build a deterministic state machine and inject duplicate delivery over two relays, same ID with different payload hash, executor crash before effect, crash after effect but before receipt, receipt loss and retry, expiry, stale authorization and concurrent arrival of the same command.

Compare naive retry against idempotency-key + fingerprint + durable execution state.

## Real hardware
Use 4–6 boards plus a harmless LED/servo/tabletop robot or a software-only job executor. Send the same command through two independent relay paths and intentionally lose the first receipt. Measure observed executions and state transitions; do not use safety-critical actuators.

## Messina / provincial teaching scenario
A student relay carries a bounded robot/sensor command toward a lab node. A second student happens to carry the same command by another route. The lab must execute one logical operation and return the same recorded result for the duplicate.

## Privacy / security
Authenticate and authorize commands. Bind the idempotency key to the exact payload fingerprint and scope. A reused ID with a different payload must fail closed. Keep anti-replay identity/nonce semantics distinct from idempotency semantics. Bound ledger retention and avoid putting student identities into command IDs.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-026 authorizes a narrow offline action; UC-010 provides a robot mission mailbox; UC-133 rejects commands from stale control epochs; UC-089 tracks alarm acknowledgement/escalation. UC-175 focuses on **duplicate-safe execution semantics after legitimate retries and multi-path delivery**.

## Standards signal
The expired IETF HTTPAPI Idempotency-Key draft is not a PollicinoNet standard, but it is a useful design reference: retries of one logical operation can be identified so the service can return the stored result instead of executing the operation again. PollicinoNet should implement the concept at its application layer rather than assume exactly-once transport.

## Validation boundary
Exactly-once delivery is not claimed. The experiment can only demonstrate duplicate-safe application behavior for the tested executor and persistence model.