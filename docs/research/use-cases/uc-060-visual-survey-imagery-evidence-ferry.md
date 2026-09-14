# UC-060 — Visual Survey and Imagery Evidence Ferry

## Idea

Collect photos or short visual survey batches in disconnected places, send **small geospatial/event summaries and exact evidence hashes first**, then move the actual imagery later over Wi-Fi/LAN/Internet or by physical carry.

The first experiment can use students walking with phones/cameras around a controlled school/campus route. A drone or vehicle is only a later optional carrier after permissions, safety procedures and the software workflow are stable.

This use case is about **visual evidence logistics**, not autonomous damage assessment and not live drone control.

## Problem solved

Images are too large for a scarce LoRa control plane, but many field situations need to know quickly that useful imagery exists:

- a route segment or school checkpoint has new photos;
- a post-event survey captured a zone;
- a rural sensor site has a visual inspection batch;
- a robotics experiment produced frames relevant to a fault;
- a drone/vehicle returned with high-resolution imagery but no immediate Internet backhaul.

PollicinoNet can move a compact `VisualSurveySummary` immediately and defer the image bytes until a rich bearer appears.

## Actors / nodes

- student/teacher field observer with phone/camera;
- optional Raspberry Pi/edge camera;
- student relay/store-and-forward nodes;
- school mapping/Raiatea/storage node;
- optional vehicle or drone data mule in later controlled trials;
- optional edge-AI node that produces non-authoritative triage metadata;
- optional UC-017/UC-049 map consumers.

## Why PollicinoNet fits

The summary is small but the evidence is large.

- **DISCOVERY:** `new imagery for zone Z`, capture count, rough time/coverage, priority and evidence availability;
- **EXACT:** survey/batch ID, image hashes, capture manifest, calibration/provenance references and later exact archive root;
- **SEMANTIC:** optional labels such as `possible obstruction`, `inspection`, `change candidate`, never authoritative without evidence/review.

Store-carry-forward allows the summary, thumbnails and full-resolution evidence to arrive at different times and over different bearers.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** survey ID, coarse zone, count, timestamps/uncertainty, compact event labels and exact evidence hashes;
- **BLE:** thumbnail/contact transfer at close range;
- **Wi-Fi/LAN:** full JPEG/RAW/video snippets, photogrammetry inputs and derived map products;
- **Internet:** optional upload to a mapping/storage service;
- **physical transport:** SD card/phone/laptop/vehicle/drone carries the original imagery when no network path exists.

## What we can test now in software

Use an open or synthetic image set first.

Implement:

- canonical `VisualSurveyManifest` with exact file hashes and coarse area/time metadata;
- summary-first, evidence-later delivery;
- thumbnails as optional intermediate representation;
- duplicate images and repeated survey passes;
- missing/corrupt image detection;
- two survey versions for the same zone;
- explicit `unknown / unreviewed / reviewed` status;
- optional edge-AI triage that emits only candidate labels and confidence, never an authoritative damage claim;
- evidence requests through UC-024;
- map attachment through UC-017/UC-049 after exact retrieval;
- archive/checkpoint creation for Raiatea or a content-addressed store;
- compare `send all images immediately` versus `summary first + selective retrieval` on the same synthetic workload;
- metrics: summary latency, evidence-retrieval latency, bytes per bearer, duplicate suppression, missing-evidence rate and reviewer turnaround.

A key invariant is:

> a semantic label may trigger attention, but only the exact retained evidence and its provenance can support later review.

## What requires real hardware

- 3–5 LoRa nodes;
- one or more ordinary phones/cameras or a harmless edge camera;
- a controlled walking route with several survey checkpoints;
- a real summary exchange over LoRa;
- one real Wi-Fi/BLE/physical transfer of the corresponding image batch;
- measurements of contact duration, summary delivery and bulk-transfer behavior.

A drone is not required for the first real experiment. If used later, comply with aviation, privacy and site permissions and keep flight control outside PollicinoNet.

## Messina teaching scenario

Define several coarse survey cells around a school/campus or controlled public route in the Messina hinterland. Student groups collect ordinary non-sensitive photos of fixed harmless targets such as signs, test markers or mock route-obstruction props.

A student relay carries only compact survey summaries between `Messina`, `Villafranca/Rometta` and `Spadafora/Venetico`. The school node sees which zones have new evidence and requests only selected image batches over Wi-Fi when a carrier returns.

A later advanced experiment can use a vehicle or properly authorised drone merely as a **data mule/camera platform**, while the PollicinoNet protocol remains the same.

## Privacy / security

- avoid faces, vehicle plates, home interiors and private property in teaching datasets;
- prefer staged targets and public/school-controlled scenes;
- coarse-grain location in LoRa summaries;
- sign survey manifests and verify exact evidence hashes;
- keep original metadata where needed for provenance but strip unnecessary personal EXIF before broad distribution;
- distinguish captured evidence from human/AI interpretation;
- enforce retention and access policies for imagery;
- do not claim authoritative structural, fire, road-safety or disaster assessment from this prototype.

## Difficulty

**Medium–High.** The transport pattern is straightforward; provenance, geoprivacy, selective retrieval, large-object handling and review semantics require careful design.

## Research / deployment signal

OpenDroneMap provides an established open-source pipeline for turning aerial imagery into orthophotos, point clouds and elevation products. Humanitarian mapping activations in 2026 have also used post-event drone imagery for manually reviewed damage mapping. UC-060 does not reproduce those operational systems; it studies how compact survey availability and exact evidence could move through an intermittent PollicinoNet network before bulk imagery is available centrally.

References:

- https://github.com/OpenDroneMap/ODM
- https://wiki.openstreetmap.org/wiki/Humanitarian_OSM_Team/Open_Mapping_Hub_Eastern_and_Southern_Africa/Cyclone_Gezani_2026
- https://mapping.emergency.copernicus.eu/
