# UC-110 — Near-Duplicate Visual Evidence and Dataset Representative Ferry

## Idea

Before moving many large images through an intermittent network, exchange **compact similarity fingerprints and cluster metadata** so the receiver can request one or a few useful representatives instead of blindly transporting every visually redundant file.

Exact hashes still define exact files. Perceptual hashes or embeddings only answer a different question: `are these images probably near-duplicates?`

## Problem solved

Visual surveys, robots, phones and dataset-collection campaigns can generate many almost-identical images:

- repeated frames of the same harmless target;
- several students photographing the same checkpoint;
- a vehicle/drone capturing overlapping imagery;
- re-compressed/resized copies of an existing picture;
- AI dataset contributions that repeat material already present;
- robot logs containing long sequences with little visual change.

If every near-duplicate is transferred in full, short Wi-Fi/BLE contacts and volunteer caches are wasted. Exact SHA-style deduplication cannot catch crops, resizes, recompression or small viewpoint/lighting changes.

## Actors / nodes

- phones/cameras/robots generating images;
- local fingerprinting node;
- student relay/store-and-forward nodes;
- school/Raiatea/dataset collector;
- optional reviewer who confirms representative selection;
- optional AI dataset curator using UC-056 provenance/consent state.

## Why PollicinoNet fits

The comparison signal is much smaller than the images themselves and can travel before the bulk evidence.

- **DISCOVERY:** similarity-family ID, compact fingerprint/sketch, cluster candidate count and representative availability;
- **EXACT:** original image hash, exact thumbnail/full-image hashes, algorithm/version, fingerprint hash and cluster decision provenance;
- **SEMANTIC:** labels such as `likely-near-duplicate`, `representative-candidate` or `needs-review`, never a claim that two exact files are identical.

LoRa can carry tiny cluster/fingerprint hints only if they fit the existing frozen PHY and experiment budget. Larger fingerprints/embeddings should use BLE/Wi-Fi. Full images stay on richer bearers or physical media.

## Possible bearers

- **LoRa:** image/batch IDs, exact hashes or compact IDs, small duplicate/representative hints and evidence-request status;
- **BLE:** perceptual hashes, small thumbnails and moderate metadata exchange;
- **Wi-Fi/LAN:** embeddings, representative/full images and dataset batches;
- **Internet:** optional comparison against a central/open dataset;
- **physical transport:** phone/SD/laptop carries selected originals when no rich network path exists.

## What we can test now in software

Use public/open image datasets and synthetic transformations.

Build several controlled duplicate classes:

1. exact byte duplicate;
2. JPEG recompression;
3. resize;
4. brightness/contrast change;
5. small crop;
6. rotation/flip;
7. burst frames with small viewpoint change;
8. genuinely different but visually similar images.

Compare:

- exact cryptographic hash;
- pHash/dHash-style perceptual hashes;
- a small embedding model;
- two-stage policy: cheap hash first, embedding/review only for ambiguous pairs.

Test false positives and false negatives, cluster chaining, algorithm-version mismatch, stale cluster state, and the case where a suppressed image later turns out to contain unique evidence.

Useful software metrics include transferred bytes avoided, representative count, false suppression rate, false duplicate rate, clustering latency and review burden. Any network/energy saving remains a hypothesis until measured on real devices and contacts.

A critical invariant is:

> near-duplicate similarity may suppress a transfer candidate, but it must never replace the exact source hash or erase provenance of the original file.

## What requires real hardware

A first physical experiment needs:

- 3–5 LoRa nodes;
- 2–4 phones/cameras or one camera producing burst images;
- a controlled set of harmless visual targets;
- local fingerprint generation;
- one short BLE/Wi-Fi transfer window where not every image fits;
- repeated comparison between `send all` and `representatives first` policies.

Measure actual bytes transferred, contact duration, selected/missed unique images and device compute time. Energy claims require instrumentation.

## Messina teaching scenario

Place fixed test markers at several authorized school/public checkpoints. Multiple student groups photograph the same markers at different times and with different phones while moving between `Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora`.

The collector should first learn that many images are likely redundant, request one or two representatives per cluster, and only retrieve additional originals when review or provenance requires them.

A second variant can use a stationary Romeo/robot camera producing a short burst around the same scene.

## Privacy / security

Perceptual fingerprints and embeddings are not harmless metadata.

- use only staged/public teaching imagery for early experiments;
- avoid faces, plates, homes and private property;
- do not assume a perceptual hash is irreversible or privacy-preserving;
- protect fingerprint/embedding exchange when the underlying imagery is sensitive;
- keep exact provenance for every suppressed original;
- make false-positive suppression recoverable: `not transferred yet` is not `deleted`;
- bind similarity decisions to algorithm/model/version and thresholds;
- retain human review for evidence/dataset decisions where missing a unique image matters;
- preserve UC-056 consent/purpose restrictions and UC-077 deletion semantics.

## Difficulty

**Medium–High.** Fingerprinting is easy to prototype; choosing safe thresholds and proving that selective transfer does not discard unique evidence is the harder part.

## Why this is distinct

- **UC-060:** transports visual-survey summaries and later full imagery.
- **UC-100:** aggregates demand to rebalance caches.
- **UC-101:** uses model disagreement to decide which samples need adjudication.
- **UC-110:** detects **visual near-duplication** so large media/dataset transfers can prioritize representative images while preserving exact provenance.

## Research / implementation signal

A 2026 comparative evaluation of image deduplication reports the expected trade-off between low-cost perceptual hashes and more robust deep embeddings, especially under crops/rotations and other transformations. 2026 dataset-integrity work also continues to use perceptual hashes and embeddings to detect near-duplicate leakage. PollicinoNet should measure its own false-suppression and transfer trade-offs rather than importing those papers' numerical results.

References:

- https://doi.org/10.3390/electronics15071493
- https://research.chalmers.se/en/publication/553456
