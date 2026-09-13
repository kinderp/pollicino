# UC-054 — Offline Assignment Submission and Feedback Courier

## Idea

Let students submit an exact version of an assignment, receive a durable receipt, and later receive teacher feedback **without requiring student, school server and teacher to be online at the same time**.

The assignment file itself can move over Wi-Fi/BLE or by physical carry. LoRa carries only compact submission metadata, receipts and status.

## Problem solved

Normal learning platforms assume that a student can reach the school/LMS server around the deadline. In a deliberately partitioned teaching experiment—or in a genuinely weak-connectivity environment—that assumption fails.

The distributed-systems problem is richer than simply sending a file:

```text
Which exact version was submitted?
Was it accepted once or duplicated?
When was it considered submitted if clocks/network were uncertain?
Did the student receive a receipt?
Which feedback version belongs to which submission?
```

A delay-tolerant workflow can preserve these facts even if the payload and acknowledgement travel on different days.

## Actors / nodes

- student laptop/phone/Pollicino node;
- student relay/store-and-forward nodes;
- school/LMS adapter node;
- teacher node;
- optional Raiatea/document store;
- optional Internet gateway when available;
- optional UC-020 trusted-time checkpoint source.

## Why PollicinoNet fits

Assignment state is mostly compact control data plus potentially large exact artifacts.

- **DISCOVERY:** `assignment available`, `submission pending`, `feedback ready`;
- **EXACT:** course/assignment ID, submission ID, artifact hash, version, receipt, accepted-state and feedback-artifact hash;
- **SEMANTIC:** optional labels such as `draft`, `final`, `needs revision`, never a substitute for exact submission state.

This composes naturally with UC-023 private mailbox, UC-006 Raiatea document capsules and UC-033 rich-bearer handoff, but adds education-specific invariants around deadlines, receipts and immutable submitted versions.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** assignment/submission IDs, exact artifact hash, small receipt/status, deadline/freshness metadata and `feedback ready` notice;
- **BLE:** nearby submission/feedback transfer for small or medium artifacts;
- **Wi-Fi/LAN:** PDFs, source archives, notebooks, feedback files and bulk synchronization;
- **Internet:** ordinary LMS fast path when available;
- **physical transport:** a student's or teacher's node carries encrypted submission/feedback artifacts between disconnected groups.

## What we can test now in software

Build a synthetic classroom with several students, one assignment and an intermittently reachable school node.

Test:

- immutable `SubmissionEnvelope` containing assignment ID, student pseudonym, artifact hash and submission version;
- multiple local drafts but only one explicitly submitted version;
- duplicate relay delivery without duplicate logical submission;
- replacement/resubmission only when assignment policy permits it;
- receipt generation after exact artifact verification;
- delayed reverse-path receipt;
- deadline states `on_time`, `late`, `time_uncertain` rather than pretending all clocks are authoritative;
- a submission created before a deadline but delivered after it;
- teacher feedback bound to the exact submitted artifact hash;
- feedback arriving before the student reconnects;
- corrupted/wrong artifact rejection;
- metadata-only LoRa path with file transfer over a simulated rich bearer;
- metrics: submission-to-receipt delay, duplicate suppression, bytes per bearer, unresolved time-state count and feedback turnaround.

A key invariant is:

> the system never silently changes which artifact was submitted; receipts and feedback always bind to an exact submission identity/hash.

## What requires real hardware

- 4+ LoRa nodes split between two classroom/lab groups;
- one student relay moving between groups;
- at least one real PDF/code archive or harmless synthetic assignment;
- real LoRa exchange of compact submission/receipt metadata;
- one UC-033-style Wi-Fi/BLE handoff of the actual artifact;
- measured time from first contact opportunity to accepted receipt and later feedback return.

This is a teaching prototype, not a replacement for institutional LMS policy or official exam-submission infrastructure.

## Messina teaching scenario

Create two disconnected groups representing `Rometta/Venetico` and the school node. Student A finishes a small programming assignment while the school node is unreachable.

The local device freezes the final artifact hash and creates a `SubmissionEnvelope`. A student's relay later carries the metadata and, when a rich bearer appears, the exact archive. The school node verifies the hash and creates a receipt. The reverse receipt may return with a different student relay later in the day.

The teacher then attaches feedback to that exact submission version. A second exercise deliberately creates two drafts and a late relay so students can see the difference between **creation time, submission decision, receipt time and network delivery time**.

## Privacy / security

Schoolwork and grades are personal data.

- encrypt submission and feedback payloads end-to-end;
- avoid names, grades and free-form feedback in LoRa broadcast metadata;
- use pseudonymous classroom identities in experiments;
- authenticate receipts and feedback;
- keep deadlines/policy authoritative at the school adapter, not at an arbitrary relay;
- never infer plagiarism or authorship from transport metadata;
- use harmless synthetic assignments for network testing when possible;
- separate transport proof from academic-policy decisions.

## Difficulty

**Medium.** The payload transport is straightforward; the interesting parts are exact version binding, receipts, deadline uncertainty, idempotence and private feedback.

## Research signal

Offline education systems already treat disconnected work as a real product requirement. Moodle's mobile stack has supported offline assignment-related workflows for years, and current Moodle assignment documentation still models explicit submission state, receipts/status-like transitions and offline grading workflows. PollicinoNet would not replace an LMS; it would study how those exact workflow objects can cross a sparse human-carried network.

References:

- https://docs.moodle.org/500/en/Viewing_an_assignment
- https://moodledev.io/general/app_releases/v3/v3.1.3
