# UC-CITSCI-001 — Student field-observation and citizen-science ferry

Status: PRIMARY USE CASE / PROTOTYPE-DRIVING

## Problem

Students can produce useful structured field observations even where continuous connectivity is unavailable or undesirable. The observation itself may be tiny — category, timestamp bucket, coarse area, confidence, short note — while the rich evidence such as a photo, audio clip or larger sensor attachment can wait until Wi-Fi or Internet is available.

Examples suitable for an educational pilot include:

- biodiversity observations using non-sensitive/public species;
- coastal litter or beach-condition counts;
- school garden/phenology observations;
- shade/heat-comfort surveys without personal data;
- simple geology or landscape observations;
- public cultural-heritage condition notes that are explicitly non-authoritative.

The network carries compact signed or attributable observation metadata and later resolves richer evidence through normal storage/network links.

## Actors / nodes

- student observer;
- student-carried Pollicino node;
- school/lab gateway;
- optional teacher/reviewer node;
- optional home Wi-Fi/NAS endpoint;
- optional public or school citizen-science repository.

## Messina educational scenario

Students from different territorial clusters record observations during ordinary activities, then carry metadata toward the school mixing hub.

```text
coastal observation -> student node --+
hill observation    -> student node --+--> school mixing hub
school garden       -> local node   --+        |
                                             v
                                    Wi-Fi / review / rich media
```

Town or landscape labels are scenario labels only. No radio coverage between real locations is assumed.

## Why PollicinoNet fits

This differs from `UC-IOT-001`: observations are human-created, sparse and semantically rich rather than continuous fixed-sensor telemetry.

It stresses:

- small structured records;
- provenance and confidence;
- geographic relevance without exact-location disclosure;
- duplicate/near-duplicate observations;
- delayed rich-media resolution;
- topic/subscription dissemination compatible with DNA-like interests;
- review/validation state that may return later.

## Possible bearers

- LoRa for compact observation descriptors and review state;
- BLE for local exchange during field/lab activities;
- Wi-Fi for photos/audio/data attachments;
- Internet for final upload or public dataset synchronization;
- physical movement for store-carry-forward.

## What can be tested now in software

Without boards we can model:

1. observation generation by territorial/topic cohort;
2. coarse-area interest filters;
3. duplicate and near-duplicate reports;
4. confidence/review state;
5. photo/audio represented only by content hashes/URLs/CIDs;
6. teacher-review acknowledgements returning through the DTN;
7. finite buffers and aging;
8. public versus restricted observation classes;
9. delivery-before-lesson or delivery-before-survey-close deadlines.

A useful comparison is full broadcast versus topic/geographic interest filtering versus pull of only missing observation summaries.

## What requires real hardware

Hardware is required before claiming:

- useful observations transferred per encounter;
- field battery life;
- body/hand/carry effects on contacts;
- real student encounter patterns;
- real upload latency from territory to school;
- practical ergonomics of recording and reviewing observations.

HW-006 remains the first RF evidence gate.

## Privacy / security

Requirements:

- no faces or identifiable people in the default pilot;
- coarse area rather than home address or continuous GPS trail;
- sensitive-species locations must be generalized or suppressed;
- separate public observations from restricted classroom data;
- integrity/provenance for reviewed records;
- allow correction/retraction of erroneous observations;
- avoid using the network as an authoritative environmental or heritage reporting channel without domain review.

## Implementation difficulty

**Medium.** The transport primitives already fit; new work is mainly the observation schema, review lifecycle, duplicate policy and privacy-aware geographic metadata.

## Minimal measurable hypotheses

- H1: compact observation metadata can spread through the student network with far fewer scarce-link bytes than attached media.
- H2: topic/coarse-area filtering materially reduces forwarding while preserving useful discovery.
- H3: delayed review/acknowledgement can return reliably through the same store-carry-forward paths.

## Metrics

- observations discovered/delivered;
- useful observation ratio per subscriber;
- scarce-link bytes per accepted observation;
- duplicate suppression rate;
- review turnaround time;
- stale/expired observation count;
- rich-media references resolved later;
- per-bearer TRC.

## Gate decision

**PROTOTYPE.** This is a strong educational field pilot because it produces meaningful application traffic without requiring private messages, large LoRa payloads or safety-critical claims.

## Related research precedent

Mobile crowdsensing/citizen-science systems use participants and mobile sensing to collect distributed observations. CrowdSenSim explicitly models participatory and opportunistic mobile crowdsensing in realistic urban environments: https://doi.org/10.1016/j.pmcj.2017.04.004 .

A student-friendly precedent for mobile environmental sensing is NITOS BikesNet, which used volunteer-carried mobile sensing nodes and handled intermittent connectivity: https://doi.org/10.1109/MDM.2014.17 .
