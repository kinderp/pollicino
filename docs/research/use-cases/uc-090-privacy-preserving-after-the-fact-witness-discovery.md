# UC-090 — Privacy-Preserving After-the-Fact Witness Discovery

## Idea

After a harmless event has already happened, distribute a **coarse, bounded witness query**. Nodes compare that query locally against private encounter/sensor/location evidence and may return a pseudonymous “possible match” without publishing everybody’s historical movements or logs.

The raw evidence stays local until the holder explicitly opts in to disclose a selected item over a richer bearer.

## Problem solved

Sometimes we do not know in advance which nodes will have useful evidence.

Examples for controlled experiments:

- “did any node observe the synthetic marker near checkpoint B during window T?”;
- “does anyone have a sensor sample from this coarse zone/time?”;
- “did any student-carried node encounter test tag X after it left the lab?”;
- “does any node have a photo of the staged object used in today’s exercise?”

A central trace database would make this easy but would also create a detailed history of people and devices. PollicinoNet can instead move the **question** to local evidence stores and return only opt-in matches.

## Actors / nodes

- query originator;
- student relay/store-and-forward nodes;
- witness nodes holding local private logs/evidence;
- optional verifier or teacher-controlled evidence sink;
- optional Raiatea/DNATrace component for evidence indexing.

## Why PollicinoNet fits

This is a natural query-to-data pattern under intermittent connectivity.

- **DISCOVERY:** coarse witness-query class and expiry;
- **EXACT:** query ID, bounded time window, coarse zone/checkpoint ID, target pseudonym/hash or event predicate, evidence hash and response nonce;
- **SEMANTIC:** human descriptions can help create the query but should not be propagated as precise private metadata.

The query can travel through many relays while private historical evidence remains on the node that collected it.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** opaque query ID, coarse predicate, expiry, optional-match notice and evidence hash/reference;
- **BLE:** local private confirmation between nearby parties;
- **Wi-Fi/LAN:** selected photo/log/sensor evidence after consent;
- **Internet:** optional later upload to an authorized sink;
- **physical transport:** a student device carries the query and later returns a consented evidence package.

## What we can test now in software

Define a `WitnessQuery`:

```text
query_id
issuer_id
predicate_type
coarse_zone_id
time_window
optional_target_commitment
created_epoch
expiry
purpose_id
```

and a local `MatchResponse`:

```text
query_id
responder_pseudonym
match_class = NONE | POSSIBLE | OPTED_IN
evidence_commitment
response_nonce
created_epoch
```

Then test:

- query arrives long after the event;
- node has no matching evidence;
- node has several possible matches;
- duplicate query propagation;
- query cancellation/expiry;
- evidence retained locally but not disclosed;
- explicit opt-in after a possible match;
- false/coarse matches caused by wide time windows;
- malicious over-broad query rejected by policy;
- query issuer changes the predicate after responses exist;
- evidence body transferred later and verified against the earlier commitment;
- deletion/retention policy removes local evidence before the query arrives.

Useful metrics: query propagation delay, match latency, false/coarse-match rate, opt-in rate, bytes of private evidence disclosed, and number of nodes that can answer locally without sending raw history.

A key invariant is:

> non-matching nodes should reveal as little as possible about where they were, what they observed, or whether they possess unrelated evidence.

## What requires real hardware

A first safe physical experiment needs:

- 4–6 LoRa nodes carried between predefined public/school checkpoints;
- one synthetic event/tag/marker;
- local logs containing only pseudonymous checkpoint encounters;
- one relay path that prevents direct originator-to-witness contact;
- optional phone camera or sensor for an evidence package.

The event and identities should be completely synthetic. No real incident investigation is required or appropriate for the first experiment.

## Messina teaching scenario

Create a route through school, Villafranca, Rometta/Venetico and Spadafora using only coarse predefined checkpoints. A synthetic test object is shown at one checkpoint during a known time window. Later, the school issues a witness query. Student nodes locally test whether their private logs match and only matching volunteers return a pseudonymous response.

This makes privacy measurable: compare a naive central trace upload against query-to-local-log discovery on the same synthetic trace set.

## Privacy / security

Privacy is the primary requirement.

- use coarse zones and bounded time windows;
- avoid names, home addresses and continuous GPS history;
- queries need an explicit purpose and expiry;
- local policy should reject over-broad or repeated fishing queries;
- prefer pseudonymous/rotating responder identities;
- do not reveal `NONE` responses individually if silence is safer;
- selected evidence requires explicit opt-in/authorization;
- bind disclosed evidence to the earlier commitment/hash;
- retention/deletion policy must remain enforceable;
- do not use this mechanism to track students, infer attendance, investigate real misconduct or expose sensitive personal history.

## Difficulty

**High.** Local matching is easy; preventing the query/response pattern itself from becoming a tracking mechanism is the hard part.

## Why this is distinct from nearby use cases

- **UC-011:** records pseudonymous encounter capsules for later consent-oriented discovery.
- **UC-034:** moves document queries to Raiatea corpora.
- **UC-050:** searches for a specifically lost tagged object.
- **UC-090:** issues a **post-event bounded predicate** to many private local histories so potential witnesses can self-select without centralizing everyone’s traces.

## Research / implementation signal

Recent privacy work continues to explore proving proximity/location properties without revealing exact coordinates. Zero-Knowledge Location Privacy (IEEE S&P 2025) is one example showing that “prove a coarse spatial fact without disclosing the precise location” is technically meaningful. PollicinoNet does not need zero-knowledge proofs in the first prototype, but the privacy goal is aligned: local evidence should answer the minimum necessary predicate.

References:

- https://doi.org/10.1109/SP61157.2025.00057
- https://discovery.ucl.ac.uk/id/eprint/10211442/
