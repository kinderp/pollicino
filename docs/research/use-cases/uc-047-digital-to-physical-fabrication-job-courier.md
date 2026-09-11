# UC-047 — Digital-to-Physical Fabrication Job Courier

## Idea

Use PollicinoNet to discover a nearby or intermittently reachable fabrication capability—such as a 3D printer, ordinary printer, laser cutter or other **safe school-lab device**—submit an exact job later over a rich bearer, receive compact progress/status asynchronously, and eventually collect the physical result.

This is a concrete vertical built on UC-014 capability exchange, but with an important twist: the final output is a **physical artifact**, not just a digital file.

## Problem solved

A student may need an object produced by equipment that exists elsewhere:

- a 3D printer in the school lab;
- a large-format or ordinary printer;
- a maker-space machine with a specific material/tool;
- a teacher-controlled fabrication station.

The requester may not know which machine is available, compatible or reachable. The file itself may also be too large for LoRa.

PollicinoNet can separate:

```text
find capability
     ↓
reserve/accept job
     ↓
transfer exact digital artifact over rich bearer
     ↓
execute locally
     ↓
return compact status
     ↓
physical pickup/handover
```

## Actors / nodes

- student requester;
- student relay/store-and-forward node;
- school fabrication node;
- authorized teacher/operator;
- paired printer/3D printer/fabrication device;
- optional local slicer/preprocessor;
- optional trusted pickup point;
- physical output object.

## Why PollicinoNet fits

The control plane is compact while the job payload is not.

- **DISCOVERY:** capability class, machine/material hints, queue availability and coarse location;
- **EXACT:** job manifest, source file hash, machine/profile ID, produced-artifact receipt and status IDs;
- **SEMANTIC:** human job description such as `print enclosure`, never a substitute for exact job identity.

A requester can discover that an authorized school node supports a capability, then use UC-033 to transfer the actual file over Wi-Fi/LAN when a suitable contact occurs.

Store-carry-forward is useful because job submission, execution, status and pickup may happen at different times.

The frozen LoRa PHY is unchanged.

## Job model

A first safe `FabricationJob` can contain:

```text
job_id
requester_id
capability_class
source_object_hash
source_format
machine_profile_id?
material_profile_id?
quantity
priority
expiry
operator_approval_required = true
status
result_receipt_hash?
```

For 3D printing, avoid treating arbitrary G-code as automatically trusted. A safer first design submits a known-safe model/object to a controlled slicer/profile or requires operator review before execution.

## Possible bearers

- **LoRa:** capability advertisement, queue hint, job ID, accept/reject/status, small progress/ready-for-pickup notice;
- **BLE:** nearby job metadata and small files if measured practical;
- **Wi-Fi/LAN:** STL/3MF/PDF/G-code or other fabrication payloads, previews and logs;
- **Internet:** optional ordinary remote submission path when available;
- **physical transport:** the finished artifact is carried to the requester or collected at school.

## What we can test now in software

No machine is required for the first stage.

Build a virtual fabrication service with several simulated machines.

Test:

- capability discovery (`3d_print`, `paper_print`, etc.);
- machine/profile compatibility;
- queue acceptance and reservation;
- duplicate job submission without duplicate execution;
- requester retries after lost acknowledgement;
- machine goes offline after accepting;
- job expiry before execution;
- source file hash mismatch;
- result/status arrives before a delayed acceptance message;
- queue fairness and per-user quotas;
- operator approval state;
- cancel-before-start vs cancel-after-start semantics;
- exact source/result provenance;
- physical pickup receipt modeled as a later event;
- integrate UC-033 for large file handoff and UC-042 for optional physical handover tracking.

Useful metrics include time-to-capability, queue wait, duplicate-work prevention, bytes on scarce/rich bearers, failed-job rate, operator intervention count and time-to-physical-pickup.

## What requires real hardware

Start with the safest hardware possible:

- one ordinary paper printer or supervised 3D printer;
- 2–4 requester/relay nodes;
- one school/lab controller;
- a harmless pre-approved test artifact;
- real LoRa capability/status exchange;
- rich-bearer file submission;
- manual operator approval before fabrication;
- physical pickup/receipt.

Only after this works should multiple printers or maker devices be considered.

No unattended remote fabrication of unknown objects should be part of the initial experiment.

## Messina teaching scenario

A student group in `Rometta/Venetico` needs a small pre-approved enclosure for a sensor project. The 3D printer is in the school lab and currently disconnected from the student network.

A PollicinoNet relay carries a compact `NeedCapability(3d_print)` request. The school node later returns a compatible offer with queue/profile metadata. On the next rich-bearer contact, the exact model file is transferred and verified. A teacher/operator approves the job locally.

Later, only compact state travels through the student relay network:

```text
ACCEPTED -> PRINTING -> READY_FOR_PICKUP
```

The physical part is collected at school. A final receipt closes the job.

A second experiment can use an ordinary PDF/paper-print job to show that the protocol is **fabrication-capability generic**, not tied to 3D printing.

## Privacy / security

Fabrication can cross from software into physical safety, so authorization is stricter than ordinary content transfer.

- never auto-execute arbitrary received machine code;
- require an allow-listed capability and operator approval for early prototypes;
- verify source file and profile identities exactly;
- sandbox/preprocess files where possible;
- maintain quotas and reject resource-exhaustion jobs;
- do not fabricate weapons, hazardous devices or regulated items;
- separate requester identity from broad capability advertisements;
- protect private project files during transport;
- record job provenance and approval without exposing unnecessary student data;
- physical pickup should use a safe school/community rendezvous, not private addresses.

## Difficulty

**Medium–High.** Discovery and queues are straightforward; safe execution, idempotency, machine compatibility, operator approval and the digital-to-physical trust boundary make it more demanding than ordinary file delivery.

## Why this is distinct from UC-014

UC-014 is the generic capability/compute primitive. UC-047 is a concrete end-to-end service with a different lifecycle and risk model because the result becomes a **physical object** that must be picked up or handed over.

## Research / implementation signal

Existing 3D-print systems already expose machine/job APIs and local network queues. OctoPrint documents explicit job state operations, while Continuous Print demonstrates LAN queues across multiple printers. These are useful adapters/reference implementations; PollicinoNet's contribution is the delay-tolerant discovery/job-control path around them.

References:

- https://docs.octoprint.org/en/main/api/job.html
- https://smartin015.github.io/continuousprint/lan-queues/
