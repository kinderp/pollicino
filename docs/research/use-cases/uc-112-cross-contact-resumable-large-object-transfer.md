# UC-112 — Cross-Contact Resumable Large-Object Transfer

## Idea

Make a large exact object continue transferring across **multiple separate contact windows** without restarting from zero each time two nodes meet.

The receiver persists verified transfer progress, and a later encounter resumes from the missing chunks/ranges. The protocol must remain safe if contacts are reordered, two relays carry overlapping chunks, or the sender/receiver reboots between encounters.

## Problem solved

Many PollicinoNet objects are larger than one opportunistic BLE/Wi-Fi contact:

- AI models and datasets;
- map packs;
- Raiatea document/index archives;
- backup objects;
- image/video evidence;
- software/container artifacts;
- erasure-coded or version-delta objects.

A naive transfer wastes every interrupted attempt if it restarts from byte zero. UC-045 already schedules which item/chunk to send during one short encounter, but PollicinoNet also needs a durable **cross-contact progress contract** for a single large object.

## Actors / nodes

- sender/cache holding the complete exact object;
- receiver accumulating verified partial content;
- optional student relay(s) carrying different chunks;
- optional object manifest publisher;
- optional UC-018 erasure-coded source or UC-104 delta source;
- observatory/experiment collector measuring real contact windows.

## Why PollicinoNet fits

The control state is small while the object is large.

- **DISCOVERY:** `object X partially present`, progress class, missing-range/chunk summary and resume capability;
- **EXACT:** object hash, manifest/chunk layout, verified chunk/range set, transfer-session generation and final exact target hash;
- **SEMANTIC:** labels such as `model-pack` or `map-bundle` can help prioritization but never define transfer correctness.

LoRa can advertise compact resume state or the fact that useful chunks are still needed. BLE/Wi-Fi/LAN carries the large bytes. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** object/manifest ID, compact progress digest, missing-chunk request, resume generation and completion status;
- **BLE:** repeated nearby chunk transfer;
- **Wi-Fi/LAN:** normal bulk transfer and high-rate resume;
- **Internet:** optional alternate source for missing ranges;
- **physical transport:** student devices, SD/USB/SSD or a vehicle can carry partial object stores between islands.

## What we can test now in software

Use deterministic chunking first, then compare range-based or content-defined chunking where useful.

Test:

1. one sender/one receiver interrupted repeatedly;
2. reboot of sender and receiver between contacts;
3. receiver loses only volatile state but retains verified chunks;
4. two relays provide overlapping chunks;
5. chunks arrive out of order;
6. stale progress advertisement;
7. corrupted chunk requiring retransmission;
8. object version changes mid-transfer;
9. resume bitmap is too large and needs a compact summary/digest;
10. partial transfer expires and is garbage-collected;
11. UC-104 delta transfer itself is interrupted and resumed;
12. UC-018 coded shards are transferred incrementally without confusing shard completeness with source-object completeness.

Compare:

- restart-from-zero;
- linear offset resume;
- fixed chunk bitmap;
- chunk inventory with integrity verification;
- multiple-source chunk resume.

Useful metrics include completed-object rate, re-sent bytes, useful bytes per contact, partial-storage occupancy, time-to-completion and control metadata size. These are software/transfer metrics until measured on real devices.

A key invariant is:

> final completion is accepted only after the exact target object hash verifies, regardless of how many contacts or sources contributed chunks.

## What requires real hardware

A first physical experiment needs:

- 4–6 LoRa nodes;
- two laptops/Pi or phones providing a BLE/Wi-Fi bulk path;
- one large public test object that cannot fit into the chosen short contact window;
- deliberately interrupted contacts repeated several times;
- at least one device reboot between contacts;
- comparison against a restart-from-zero baseline using the same object and controlled contact schedule.

Measure actual bytes re-sent, successful resume point, contact duration, completion time and failure/recovery behavior. Any energy claim needs explicit instrumentation.

## Messina teaching scenario

Place the full public object at a school/cache node and give a student receiver only a partial copy. During several controlled encounters across `Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora`, the receiver should make monotonic verified progress even though no single Wi-Fi/BLE window is long enough for the whole object.

A second student relay can carry a disjoint subset of chunks so the final receiver completes the object from more than one source.

This is a particularly clear classroom demonstration because students can see a transfer progress from, for example, 20% to 45% to 80% to 100% across physically separate encounters while the final hash remains exact.

## Privacy / security

- partial possession may reveal interest in an object; expose only necessary resume metadata;
- encrypt sensitive objects end-to-end or at rest as required;
- verify every chunk/range against a signed/authenticated manifest or exact reconstruction rule;
- bind progress state to an exact object/version so old chunks cannot complete a different target;
- prevent malicious peers from advertising fake progress to suppress needed transfers;
- cap partial-storage lifetime and size;
- preserve UC-076 usage policy and UC-077 deletion/retention semantics;
- do not interpret `100% chunks received` as complete until final verification succeeds.

## Difficulty

**Medium–High.** Basic chunk resume is straightforward; persistent multi-source progress, stale state, version changes and bounded metadata under repeated intermittent contacts are the interesting parts.

## Why this is distinct

- **UC-018:** reconstructs an object from enough independent coded shards.
- **UC-045:** decides which queued data to harvest first during one scarce contact.
- **UC-104:** transfers an exact delta between two artifact versions.
- **UC-112:** makes one large-object transfer **persist and resume across multiple interrupted encounters**, potentially with multiple sources.

## Research / implementation signal

Bundle Protocol v7 explicitly supports fragmentation when intermittent contacts are too short to forward an entire bundle. HTTP work also continues to standardize resumable uploads: the July 2026 `draft-ietf-httpbis-resumable-upload-12` describes querying persisted upload state and appending only the remaining data after interruption. These are useful design references; PollicinoNet still needs to test its own chunk/progress representation on real student contact windows.

References:

- https://www.rfc-editor.org/rfc/rfc9171.html#section-5.8
- https://httpwg.org/http-extensions/draft-ietf-httpbis-resumable-upload.html
- https://tus.io/protocols/resumable-upload
