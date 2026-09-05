# PollicinoNet use-case catalog

Status: living research catalog

This catalog records concrete use cases that justify PollicinoNet research and implementation work. New algorithms, protocol changes, dependencies and architectural abstractions must be evaluated against `use-case-justification-gate.md` before adoption.

## UC-DNA-001 — School hub / student data mule for topic-scoped DNA information

### Summary

A student's portable Pollicino node participates in two very different network conditions during the same day:

1. **school / connected phase** — many student nodes are physically co-located and can form a contemporaneously connected LoRa mesh, potentially using LoRaMesher or another connected-mesh bearer;
2. **home / territorial phase** — the same nodes disperse across different towns/areas and no permanent end-to-end path is assumed. Nodes continue as an opportunistic DTN/off-grid network using store-carry-forward.

The student and the node therefore become a **data mule**: information acquired while the contact graph is dense at school is physically carried to another geographic cluster and may be forwarded later without Internet.

DNA sits above PollicinoNet and decides **what the information means, who is interested, where it is relevant, how long it remains valid and what provenance/verification applies**. PollicinoNet decides **how to move only the information that the receiving node actually needs across scarce/intermittent links**.

### Actors

- student-carried Pollicino node;
- school peers;
- home/territorial peers;
- optional school/home gateway;
- DNA Discovery / DNA Commons / DNA Exchange;
- PollicinoNet bearer, reconciliation, cache and DTN layers.

Node identifiers used in experiments must be pseudonymous. The pilot must not encode or publish exact student home locations.

### DNA concepts already available

This use case should reuse existing DNA semantics rather than invent a parallel application model:

- `DNATrace` for minimal discovery;
- `DNAFragment` for authorized exact information exchange;
- `Topic` and `GeoRoom` in DNA Commons;
- `Subscription` with geo/topic filters;
- `DNAIntent` when an item represents an active need or availability;
- `GeoAnchor` / coarse geo scope;
- expiry;
- provenance;
- verification state;
- transport-independent communication policy.

`DNATrace` remains a discovery signal, not a generic container for all micro-information.

### Example information classes

The transported object can be very small. Examples include:

- public/emergency notice;
- transport disruption;
- event-state update;
- local service availability;
- sensor observation;
- public price/availability observation;
- school/community announcement suitable for the pilot policy;
- topic-state or subscription-state update.

Sensitive/private profile data is not implied by this use case and must remain subject to DNA consent/privacy rules.

### Daily contact pattern

```text
morning / school

node A ---- node B ---- node C
   \          |          /
       dense connected mesh

        reconciliation
        topic filtering
        cache convergence

              |
              | student mobility
              v

afternoon / territorial clusters

cluster A       cluster B       cluster C
   A               B               C
   |               |               |
local/off-grid   local/off-grid   local/off-grid
contacts         contacts         contacts
```

A node may learn an item at school, retain it through the mode transition, and later make it available in a territorial/off-grid encounter.

### Functional flow

1. DNA policy/subscriptions identify topics/scopes of interest.
2. School nodes advertise minimal state/trace information.
3. Peers reconcile inventories instead of retransmitting complete topic histories.
4. The school contact graph allows rapid convergence while many peers are together.
5. The student leaves school carrying verified cached objects/bundles.
6. The connected school mesh disappears; the node enters opportunistic DTN/off-grid operation.
7. A later territorial contact identifies useful missing information for the new peer.
8. PollicinoNet transfers only the required object/chunks/state within the available contact budget.
9. Expired or unauthorized DNA information is not propagated.
10. A later Wi-Fi/Internet gateway may complete synchronization or resolve richer content.

### Responsibility split

```text
DNA
- topic / intent / subscription
- geo relevance
- consent / visibility
- expiry
- provenance / verification
- application priority semantics

PollicinoNet
- object identity / exact reconstruction
- inventory reconciliation
- cache
- custody / TTL / hop policy
- contact scheduling
- store-carry-forward
- bearer selection
- scarce-link byte accounting

Bearer
- connected LoRa mesh / raw LoRa / Wi-Fi / other physical delivery
```

### Why this use case matters

The school is not merely a gateway. It is a **high-contact mixing hub**. Human mobility then transforms that dense morning exchange into later territorial connectivity.

The central hypothesis is:

> a dense period of shared knowledge can substantially reduce the information that must cross later sparse/scarce contacts.

DNA provides **semantic reduction**: only information relevant to the receiver's topic/subscription/scope is considered.

PollicinoNet provides **transport/reconciliation reduction**: among relevant information, only what the receiver lacks must cross the scarce link.

### Current baseline

Simplest baseline:

- flooding/broadcast every eligible item;
- no topic filtering beyond application selection;
- no inventory reconciliation;
- store-and-forward of full objects/messages.

Literature/practical baselines to compare where relevant:

- FreakWAN-style off-grid flooding;
- Epidemic DTN routing;
- Spray-and-Wait;
- connected LoRaMesher segment;
- current PNA1 bitmap availability exchange.

### Measurable hypotheses

H1. Topic/subscription filtering reduces candidate objects presented to the network compared with unfiltered synchronization.

H2. Reconciliation reduces scarce-link bytes further by suppressing objects/chunks already known to the receiver.

H3. A school-hub + student-data-mule contact pattern improves territorial delivery compared with an otherwise equivalent network without the dense school mixing phase.

H4. Connected-mesh operation during the school phase and opportunistic DTN operation after dispersion can preserve the same Pollicino object/custody state without losing exactness or provenance.

### Metrics

Track at least:

- relevant objects discovered;
- irrelevant objects filtered by DNA policy;
- already-known objects/chunks suppressed by Pollicino reconciliation;
- useful source bytes transferred;
- total wire bytes/TRC;
- delivery ratio by topic/priority;
- time-to-delivery;
- number of physical/logical carries before delivery;
- duplicate transmissions;
- expired items suppressed;
- cache hit ratio;
- per-bearer traffic;
- storage pressure;
- privacy exposure class;
- exact SHA-256 reconstruction success for EXACT objects.

### Minimal synthetic experiment

Use pseudonymous clusters only:

```text
school-hub
home-cluster-A
home-cluster-B
home-cluster-C
```

Generate two phases:

1. dense morning contacts among nodes at `school-hub`;
2. sparse afternoon contacts inside/between home clusters, with a subset of the school nodes acting as data mules.

Generate multiple topic classes and subscriptions. Compare:

- flood everything;
- topic-filtered only;
- topic-filtered + PNA1 reconciliation;
- later PNA2 codec candidates when justified.

Do not derive LoRa byte capacity from synthetic contact duration.

### Success criteria

This use case justifies further architecture/prototypes if experiments show at least one practically meaningful regime where:

- semantic filtering materially reduces candidate traffic;
- reconciliation materially reduces transmitted bytes beyond semantic filtering alone;
- the school mixing phase materially increases later territorial delivery;
- state survives bearer/mode transitions exactly and deterministically.

No fixed percentage is preregistered yet; thresholds must be set before any experiment intended to support an adoption claim.

### Kill/defer criteria

Defer or simplify proposed architecture if:

- the dense school phase adds negligible delivery benefit in realistic synthetic contact patterns;
- simple flooding/list-based exchange performs as well with much lower complexity;
- bearer-mode switching requires protocol/state duplication rather than preserving one Pollicino object layer;
- privacy requirements would require exposing stable identities or precise student locations;
- the scenario requires physical claims that are not yet supported by HW-006 evidence.

### Architectural implications allowed by the gate

This use case provides concrete support for studying a shared Pollicino node runtime that can preserve one object/cache/custody state across different network modes.

However implementation is still **PROTOTYPE/RESEARCH**, not automatic adoption.

Potential future abstraction:

```text
DISCOVERING
   |
   +--> CONNECTED_MESH
   |
   +--> OPPORTUNISTIC_DTN
```

The transition must never discard bundle state, cache state, reconciliation state, provenance or expiry information.

A dedicated bearer-runtime abstraction should be adopted only after this use case and at least one additional independent use case demonstrate that it reduces total system complexity, consistent with the architecture gate.

### Physical evidence boundary

The use case can be studied synthetically now.

Real claims about:

- school LoRa connectivity;
- number of simultaneous reachable student nodes;
- transition-region capacity;
- useful bytes per real encounter;
- range between territorial nodes;
- routing superiority on real hardware;

remain blocked by the existing **HW-006 physical-evidence gate**.

### Decision

**Status: PRIMARY USE CASE / PROTOTYPE-DRIVING.**

The use case is concrete enough to guide routing, reconciliation, bearer-mode and DNA/Pollicino integration experiments, but it does not by itself authorize new wire formats, LoRaMesher adoption, FreakWAN integration or a new runtime architecture without separate measured comparisons.
