# UC-MUSTER-001 — Privacy-preserving school muster / assembly reconciliation

Status: PROTOTYPE / educational safety drill

## Problem

During a school evacuation or supervised assembly drill, different teachers/checkpoints may temporarily hold partial attendance state. Wi-Fi or Internet should not be assumed, and sending a full named student list over a broadcast scarce link would create unnecessary privacy exposure.

This use case studies whether PollicinoNet can reconcile **bounded, privacy-minimized muster state** across separated assembly points and later converge at a school coordination node.

It is a drill/research workload, not a certified evacuation or emergency-management system.

## Actors / nodes

- teacher/checkpoint Pollicino nodes;
- student-carried nodes only when the exercise explicitly uses synthetic identities;
- assembly-point nodes;
- school coordination gateway;
- optional BLE/QR companion device;
- optional Wi-Fi/LAN dashboard after connectivity returns.

## Why PollicinoNet fits

Muster state is small, time-sensitive, duplicate-prone and naturally partitioned. The useful network property is eventual convergence under intermittent contact, not continuous connectivity.

PollicinoNet can carry:

- aggregate counts;
- opaque one-time check-in tokens;
- signed checkpoint generations;
- missing-token summaries;
- completion receipts;
- application deadlines and expiry.

The workload is distinct from the task board: the core metric is **reconciliation of who/what has been accounted for without leaking identity**, not claiming and completing work items.

## Possible bearers

- LoRa: small aggregate/checkpoint summaries and reconciliation state;
- BLE: local check-in between a supervised device and checkpoint;
- QR/NFC: optional deliberate local proof-of-presence input;
- Wi-Fi/LAN: full authorized roster reconciliation inside the school network;
- physical carry: teacher/student movement between assembly points.

## Privacy-preserving shapes to compare

Start with synthetic participants and compare progressively:

1. plain synthetic IDs — correctness baseline only;
2. one-time random tokens issued for the drill;
3. checkpoint-local aggregation plus only missing-token summaries;
4. rotating/pseudonymous tokens with a local authorized mapping that never traverses LoRa.

Do not invent a privacy-preserving cryptographic protocol unless the simple forms demonstrably fail the use case.

## What we can test immediately in software

Synthetic exercise:

- 4 classes / groups;
- 3 assembly points;
- 1 school coordination node;
- some participants arrive late or at the wrong checkpoint;
- one checkpoint is temporarily disconnected;
- duplicate scans and out-of-order checkpoint generations occur;
- a teacher physically carries one node between points.

Measure:

- time until the coordinator knows the final synthetic total;
- false missing / false duplicate rate;
- bytes per participant and per checkpoint;
- duplicate suppression;
- stale generation rejection;
- information exposed over the scarce link;
- recovery after node restart.

## What requires real hardware

After HW-006 and a school/privacy governance gate:

- actual assembly-point LoRa contact behavior;
- real check-in latency using QR/BLE/LoRa combinations;
- battery use during a drill-length interval;
- human usability under supervised conditions;
- whether aggregate/checkpoint messages fit real contact opportunities.

The first physical pilot should use staff or synthetic tokens rather than real student attendance data.

## Privacy and security

Attendance and presence are personal data. Therefore:

- no names, home addresses or precise locations over LoRa;
- no persistent student radio identifiers for the drill;
- short-lived random tokens;
- local-only mapping from token to identity when a mapping is necessary;
- short retention and explicit deletion policy;
- authenticated checkpoint generations;
- replay/rollback resistance;
- no automatic operational decision based only on the prototype network.

## Difficulty

**Medium.** Transport is straightforward; privacy-minimized state reconciliation and operational UX are the real design work.

## Success / kill criteria

Continue if privacy-minimized summaries converge to the correct synthetic muster state with substantially less exposed identity information than transmitting a full roster.

Reject any design that requires stable student radio identifiers or broadcasts named attendance to make the workflow work.

## Physical evidence boundary

No LoRa range, capacity or reliability claim follows from the software experiment. The frozen HW-006 campaign remains mandatory before physical conclusions, with the existing 42-byte / 2 dBm first checkpoint sequence.