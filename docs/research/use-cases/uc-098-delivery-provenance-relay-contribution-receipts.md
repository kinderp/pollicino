# UC-098 — Delivery Provenance and Relay-Contribution Receipts

## Idea

Record a **privacy-minimized application-layer journey** for selected PollicinoNet bundles: which relay accepted, forwarded, delivered or dropped an exact bundle, without turning the network into a permanent student-tracking system.

The goal is not to trace people. It is to answer a network-engineering question:

> Which relay opportunities actually contributed to successful store-and-forward delivery, and where did delivery fail?

This complements the contact graph of UC-008 with evidence about **actual bundle progress**.

## Problem solved

A contact trace tells us that node A met node B. It does not tell us whether:

- the relevant bundle was present at that moment;
- B accepted custody/storage for it;
- B later forwarded it;
- the bundle expired or was deleted under buffer pressure;
- a particular route delivered the message sooner than another;
- a relay policy is helping or merely creating traffic.

Without delivery provenance, route tuning can confuse *possible contact* with *useful forwarding*.

## Actors / nodes

- bundle producer/requester;
- student relay/store-and-forward nodes;
- final recipient;
- optional experiment collector;
- optional privacy-preserving aggregator that receives only coarse contribution summaries.

## Why PollicinoNet fits

PollicinoNet already depends on delayed forwarding, local storage and human mobility. Compact forwarding receipts are therefore native evidence about its behavior.

- **DISCOVERY:** a node supports receipt profile `rp1` or can aggregate relay evidence;
- **EXACT:** bundle digest, receipt type, experiment/session pseudonym, previous receipt/hash, local sequence number;
- **SEMANTIC:** labels such as `accepted`, `forwarded`, `delivered`, `expired`, `buffer-rejected` or `unknown` derive from exact receipt events.

The important design choice is to make receipts **selective and bounded**, not mandatory for every packet. RFC 9171 explicitly warns that status reports can create substantial extra traffic when requested for many bundles; PollicinoNet should inherit that caution rather than build a verbose per-hop telemetry channel.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact receipt/status digest, bundle ID/hash, reason code and optional aggregate counters;
- **BLE:** nearby exchange of a short receipt chain or missing-receipt request;
- **Wi-Fi/LAN:** complete experiment trace or signed receipt bundle;
- **Internet:** optional upload when a node later regains connectivity;
- **physical transport:** laptop/phone/SD returns the full experiment log to school.

## What we can test now in software

Define a compact `RelayReceipt`:

```text
bundle_id
bundle_hash
experiment_id
relay_pseudonym
receipt_seq
event = ACCEPT | FORWARD | DELIVER | DELETE | REJECT
reason_optional
previous_receipt_hash_optional
local_time_with_uncertainty_optional
signature_or_mac
```

Then simulate:

- duplicate receipts;
- missing intermediate receipts;
- receipt arriving before the corresponding bundle trace;
- two candidate relay paths for the same bundle;
- buffer rejection under UC-095 budgets;
- expiry and deletion;
- malicious or corrupted receipt;
- a relay claiming `FORWARD` without later evidence of reception by anyone;
- receipt sampling, for example only one instrumented bundle in every N experiment bundles;
- path reconstruction with `UNKNOWN` gaps rather than invented hops.

Useful metrics include:

- end-to-end delivery delay;
- number of relay accept/forward events per delivered bundle;
- duplicate-forward ratio;
- receipt overhead in bytes;
- percentage of path segments with evidence versus unknown gaps;
- bundle loss/deletion reason distribution;
- contribution distribution across relay pseudonyms;
- difference between predicted useful relays from UC-008 and observed useful relays here.

## What requires real hardware

A first physical test needs 5–8 boards and a small number of instrumented bundles.

Suggested controlled scenario:

1. place two endpoint groups at separate school/public checkpoints;
2. let 3–5 student nodes move between them as relay/store-and-forward carriers;
3. instrument only the experiment bundles with receipt generation;
4. deliberately configure one relay with a small buffer so a rejection can occur;
5. recover full traces later over Wi-Fi or physical transport;
6. compare contact opportunities with actual bundle progress.

Do not infer PDR, range, relay usefulness or optimal routes before the physical traces are collected.

## Messina teaching scenario

A message starts in Messina and is destined for a node near Rometta/Venetico. Several students independently move through Villafranca, Rometta and Spadafora during the day.

At the end, the class should be able to distinguish:

```text
contact observed       != bundle forwarded
bundle forwarded       != bundle delivered
no receipt             != proof of failure
relay contribution     != person tracking
```

The receipt chain can become a practical dataset for comparing UC-073 route planning and UC-095 fair-share policies against what really happened.

## Privacy / security

- use experiment-scoped pseudonyms rather than student names;
- never publish a persistent per-student route history;
- avoid precise home coordinates, private schedules and unnecessary wall-clock timestamps;
- allow local policy to disable or sample receipts;
- authenticate receipts so another relay cannot impersonate a contribution event;
- treat missing evidence as `UNKNOWN`, not guilt or failure;
- retain detailed receipt chains only for bounded experiments and then aggregate/delete them;
- do not build public rankings of students by relay contribution;
- a receipt proves only that a node reported an event under the selected trust model; stronger claims require stronger attestation and cross-evidence.

## Difficulty

**Medium-high.** The record format is simple; the hard parts are privacy, bounded overhead, incomplete evidence and distinguishing useful diagnostics from surveillance.

## Why this is distinct from nearby use cases

- **UC-008:** observes contact opportunities; UC-098 records selected bundle-progress evidence through those contacts.
- **UC-093:** reconstructs causal order among distributed events; UC-098 provides a domain-specific source of forwarding events that UC-093 may later order.
- **UC-095:** decides fair local relay budgets; UC-098 can measure how those policies affect actual delivery.
- **UC-097:** orchestrates experiments; UC-098 is one concrete experiment/evidence profile.

## Research / implementation signal

Bundle Protocol v7 defines optional status reports for reception, forwarding, delivery and deletion, and explicitly notes that enabling them broadly can generate unacceptable extra traffic. This is a good design signal for PollicinoNet: selective application-layer receipts can be useful, but only with sampling, bounded retention and privacy controls.

References:

- https://www.rfc-editor.org/rfc/rfc9171.html
- https://www.rfc-editor.org/info/rfc4838/
