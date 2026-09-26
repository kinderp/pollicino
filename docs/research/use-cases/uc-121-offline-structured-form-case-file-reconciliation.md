# UC-121 — Offline Structured Form and Case-File Reconciliation Courier

## Idea

Let multiple disconnected teams fill or update the same structured form/case file and later merge their changes without silently losing one person's work. The result keeps field-level provenance and explicit conflicts. The frozen LoRa PHY is unchanged.

## Problem solved

Field work often uses structured records rather than free text: equipment inspection, damage-assessment drill, maintenance form, classroom inventory, environmental observation or volunteer task record.

Two groups can update the same record while disconnected. One may change status, another may add an observation, both may edit the same field differently, or one may close a case while another adds new evidence. Last-write-wins can destroy useful information, especially when clocks are unreliable.

## Actors / nodes

- field/student data-entry nodes;
- relay/store-and-forward nodes;
- case-file replicas;
- reviewer/coordinator;
- optional schema/rule publisher.

## Why PollicinoNet fits

Field-level operations and record digests are compact.

- **DISCOVERY:** form/schema ID, case ID, revision summary and conflict-present flag.
- **EXACT:** operation IDs, field path, value hash, actor pseudonym/role, predecessor revision, attachment hash and review state.
- **SEMANTIC:** form labels and human-readable conflict explanations.

LoRa can carry compact operation summaries and conflict status; BLE/Wi-Fi carries full form deltas and attachments.

## Possible bearers

- **LoRa:** case/revision digest, operation inventory, conflict alert;
- **BLE:** small form delta;
- **Wi-Fi/LAN:** full case record, photos or documents;
- **Internet:** optional final archive;
- **physical transport:** encrypted case bundle.

## What we can test now in software

Define a synthetic form with fields such as condition, priority, note, quantity and attachment. Simulate concurrent edits to different fields, concurrent edits to the same field, case close versus new evidence, schema version change, duplicate operation, reboot, clock skew and merge after days offline.

Compare simple last-write-wins against explicit per-field conflict handling or CRDT-like structures. Measure lost updates, unresolved conflicts, metadata size and merge convergence.

## What requires real hardware

Use 4–6 boards and 3–4 laptops/phones. Divide a synthetic inspection drill between groups, disconnect them, create intentional conflicting updates, then let student relays carry deltas until all replicas converge.

No real personal, medical, disciplinary or emergency-sensitive records are needed.

## Messina teaching scenario

A school can create a fictional civil-protection or equipment-inspection exercise with several checkpoints. Teams in separate areas update the same set of case files while disconnected. Relays moving between groups gradually reconcile the forms and surface only the records that need a human conflict decision.

## Privacy / security

- use synthetic or low-sensitivity data in the first deployments;
- separate student identity from record actor pseudonyms;
- authenticate edits and retain an audit trail;
- do not let an automatic merge hide a genuine semantic conflict;
- minimize precise location and attachment metadata;
- apply UC-117 validation rules to the merged result where useful.

## Difficulty

**Medium–High.**

## Why this is distinct

UC-028 is a collaborative free-form notebook, UC-013 ferries field reports, and UC-051 is a survey/ballot. UC-121 focuses on **structured field-level records with concurrent offline edits, workflow state and explicit merge conflicts**.

## Research / implementation signal

Offline-first systems increasingly use CRDT-style reconciliation for replicas that must continue working during disconnection.

References:

- https://ideas.repec.org/a/gam/jftint/v18y2026i4p180-d1903759.html
- https://doi.org/10.1145/3777470
