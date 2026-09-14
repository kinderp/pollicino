# UC-059 — Mutual-Aid Skill and Service Rendezvous

## Idea

Let people advertise **what help or skill they can offer** and what help they need, then allow those small requests/offers to meet through a delay-tolerant student/community network.

This generalizes beyond UC-043's exchange of physical goods. The resource here is a human capability or short service: tutoring, a repair skill, translation help, carrying a package between approved checkpoints, lending technical expertise, helping configure a device, or volunteering for a harmless community task.

The first profile is non-commercial and low-risk: PollicinoNet performs discovery, matching and private rendezvous, not payments or emergency dispatch.

## Problem solved

Local communities often contain the needed capability but no always-online directory showing who can help, when and in which coarse area. During an Internet outage or in a rural/offline setting, a centralized matching platform becomes unavailable.

A compact `HelpNeed` can travel until it encounters a compatible `SkillOffer`. The parties can then use UC-023 for private negotiation and arrange an in-person or online/rich-link interaction later.

## Actors / nodes

- student/community requester;
- volunteer or peer offering a skill/service;
- student relay/store-and-forward nodes;
- school/community node holding trusted categories or optional verification state;
- optional teacher/coordinator for supervised exercises;
- optional UC-048 credential/entitlement evidence for skills that need verification.

## Why PollicinoNet fits

Needs and offers can be represented as very small, expiring objects.

- **DISCOVERY:** coarse capability tag, availability window, zone/radius and request priority;
- **EXACT:** request/offer IDs, policy constraints, expiration, pseudonymous contact/rendezvous token and optional credential reference;
- **SEMANTIC:** human-readable tags such as `python-help`, `electronics-repair`, `translation`, `transport`, used only for matching and never as proof of qualification.

Store-carry-forward is useful because requester and helper do not need to be simultaneously connected.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact skill/need category, coarse availability, expiry, zone and rendezvous token;
- **BLE:** nearby private introduction/bootstrap;
- **Wi-Fi/LAN:** richer profiles, documents or remote-help session on a local network;
- **Internet:** optional fast path when available;
- **physical transport:** the people themselves move between communities/checkpoints while their pending need/offer records travel with relay nodes.

## What we can test now in software

Create synthetic `HelpNeed` and `SkillOffer` objects and a delayed matching engine.

Test:

- exact versus broader semantic matching;
- availability windows and expiry;
- one helper matched to several competing needs;
- one need satisfiable by several helpers;
- cancellation after a match;
- duplicate/reordered need/offer propagation;
- private rendezvous token issued only after policy checks;
- optional verified-skill flag backed by UC-048 rather than a self-asserted label;
- trust/reputation kept local or policy-scoped rather than globally broadcast;
- false/stale availability;
- requester/helper pseudonym rotation;
- metrics: time-to-match, stale-match rate, redundant-match overhead, unmatched demand and privacy metadata exposed over each bearer.

A useful invariant is:

> matching a label is not the same as verifying a person, qualification or suitability for a task.

## What requires real hardware

- 4–6 student nodes split across two or three controlled groups;
- synthetic or harmless skill/need profiles;
- one moving relay;
- real LoRa need/offer exchange;
- optional BLE/Wi-Fi private rendezvous after a match;
- measured time-to-match and contact behavior.

The first physical experiment should use classroom-safe needs such as `help with Python exercise`, `soldering demo available`, `need a USB cable`, or `can explain Git`, never medical, legal, safeguarding or emergency-response tasks.

## Messina teaching scenario

Create coarse groups such as `Messina`, `Villafranca/Rometta` and `Spadafora/Venetico`. One student group publishes a short-lived synthetic need for `Python debugging help`. Another group has a student/teacher node advertising `Python peer tutoring` during a later time window.

There is no direct link. A third student acts as relay and carries the compact objects between groups. The match produces only a pseudonymous rendezvous. Richer identity/contact details are exchanged later over an authorized private channel.

A second experiment can simulate a civil-protection **training** context with harmless roles such as `radio setup`, `map printing` or `battery inventory helper`, while explicitly avoiding real emergency dispatch claims.

## Privacy / security

Human needs and skills can reveal sensitive information.

- use coarse zones, not home addresses;
- minimize broadcast profile detail;
- use pseudonymous short-lived request/offer IDs;
- keep direct contact details off broadcast LoRa;
- separate self-declared skills from verified credentials;
- require explicit opt-in and easy cancellation;
- do not expose minors' personal information or create unsupervised adult/minor rendezvous workflows;
- rate-limit spam and abusive requests;
- do not use the first profile for medical/legal/safeguarding/high-risk services;
- do not infer reliability or trustworthiness from radio contact frequency.

## Difficulty

**Medium–High.** Matching is simple; safe identity disclosure, consent, availability, abuse prevention and optional credential verification are the harder parts.

## Research / deployment signal

Current community platforms already treat requests/offers of skills and services as a useful mutual-aid primitive. Systems such as Shareish and Hylo expose local requests/offers, while Sam coordinates goods and services for trusted civil-aid organisations. UC-059 explores the same social primitive under intermittent connectivity and with deliberate metadata minimization.

References:

- https://shareish.org/
- https://www.hylo.com/
- https://hello-sam.eu/en/
