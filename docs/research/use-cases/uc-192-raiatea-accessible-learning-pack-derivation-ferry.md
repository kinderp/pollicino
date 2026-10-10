# UC-192 — Raiatea Accessible Learning-Pack Derivation and Review Ferry

## Idea and problem

A teacher's complete PDF may be available at one school while another disconnected classroom needs an **accessible, exact-version learning pack**: structured headings, searchable text, image alternatives, readable equations, captions and a simpler navigation structure. Uploading a full collection is often unnecessary, but an automatically generated adaptation must not silently become 'approved teaching material'.

UC-192 requests only the necessary adaptation jobs, performs work on a capable local or later-reached worker, returns review receipts and distributes usable derived packs with verifiable source/version references.

## Actors / nodes

Teacher/publisher, Raiatea corpus and provenance store, edge OCR/accessibility/MathML worker, reviewer/educator (not automated approval), classroom receiver, student relay/store-and-forward nodes, optional permitted Internet worker.

## Why PollicinoNet fits

A compact job announces `source_hash`, `course_pack_id`, requested `accessibility_features` (e.g. structured-text, captions, image-descriptions, equation-text), tool/version, destination and review state. LoRa carries metadata, approval/revision notifications and cache availability; complete accessible derivatives travel via richer bearer or physical carry.

## Bearers

- **LoRa:** manifest, 'needs derivative', artifact hash, status and review receipts only.
- **BLE:** text-only/low-size verified teaching packs nearby.
- **Wi-Fi/LAN:** accessible HTML/EPUB/PDF, image descriptions, audio and associated source materials.
- **Internet:** optional tool installation, licensed content retrieval or language processing where authorized.
- **Physical carry:** approved complete course-pack artifacts on school-managed encrypted media.

## Software-only now

1. Prepare a **public or teacher-authored** STEM pack containing headings, images, a code sample, a table and mathematical formulas; publish exact source hash.
2. Derive at least two outputs: structured navigable HTML/EPUB and a compact printable/text-first pack. Record tool versions, input hash, policy and revision.
3. Inject inaccessible image scans, wrong reading order, incorrect alt text, broken equation semantics, failed captions and a source edit after a derivative was reviewed.
4. Validate machine-checkable properties with relevant WCAG/EPUB tooling, but require human review for educational correctness and actual usability; log `GENERATED / NEEDS_REVIEW / REVIEWED / REJECTED / STALE`.
5. Simulate two isolated classrooms, offline derivative requests and source supersession; compare time to **reviewed usable** first asset against sending the original PDF only.

## Required real-hardware evidence

Use **4–6 LoRa boards**, 2–3 laptops/Pi with disconnected Raiatea content caches, one teacher reviewer, and a small **non-sensitive** public lesson. Run actual interrupted contacts over LoRa discovery and BLE/Wi-Fi bulk; verify hash, renderer behavior and human review status at the receiving checkpoint. Test keyboard navigation/screen-reader compatibility on chosen target software with a willing adult tester or established synthetic checks; do not collect students' disability/health profiles.

## Messina teaching scenario

A teaching resource on C or Python is prepared at a Messina lab and requested from a classroom cache in Rometta/Venetico. A relay carries the job manifest over LoRa; a capable worker creates structured HTML with corrected code and equation markup; an authorized teacher reviews it; later relay contact ferries the approved pack to Villafranca or Spadafora. Version changes invalidate obsolete adaptations. No student identity is needed in the transport metadata.

## Privacy / security

Work with public/authorized materials, respect copyright and derivative permissions (UC-076), avoid transmitting individualized BES/DSA/disability labels, authenticate source/reviewer/artifact lineage, mark machine-generated features clearly, maintain UC-120 invalidation. **Automated accessibility checks do not establish accessibility certification or pedagogical equivalence.** Any real personalization must be handled separately with institutional data governance.

## Evaluation and difficulty

**Medium–High.** Metrics: fraction of requested features available, reviewer corrections, stale adaptation detections, human-confirmed reading order, exact variant hash verification, time-to-approved-pack in simulated versus real contacts and bytes moved per bearer.

## Why distinct

UC-006 distributes Raiatea documents; UC-099 produces search/index artifacts; UC-106 handles multilingual **emergency bulletin** derivation; UC-141 offers fidelity ladders; UC-147 follows missing evidence. **UC-192 targets iterative accessibility testing, teacher review and distribution of educational material**, not simply lower-fidelity copies or AI translation.

References:
- https://www.w3.org/TR/epub-a11y/
- https://www.w3.org/TR/WCAG22/
