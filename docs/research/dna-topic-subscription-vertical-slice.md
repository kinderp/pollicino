# DNA Topic/Subscription product-facing vertical slice

Status: host/model prototype checkpoint, 2026-08-30

## Use-case gate

This slice implements the next concrete step of `UC-DNA-001`: student-carried nodes should exchange only DNA micro-information relevant to an explicit local subscription instead of flooding every valid DNA trace through the school mesh.

It deliberately does not change H2/PHY, PNF1, PNB1, PNC1, PCM1, PNA1, bearer selection, LoRaMesher routing semantics or the DNA v0.1 wire schemas.

## Contract boundary

The current DNA v0.1 repository defines `DNATrace` with canonical `domains` and `intentCodes`, but it does not yet publish a durable Topic/Subscription schema.

Pollicino therefore adds an explicitly experimental application-layer gate in:

```text
src/pollicino/integrations/dna_subscription.py
```

The gate treats existing `DNATraceV01.domains` and `DNATraceV01.intent_codes` as the only authoritative selectors. It does not add topic fields to PND1 or invent a parallel DNA wire contract.

## Matching semantics

`DNATopicSubscription` has two optional selector classes:

- `domains`;
- `intent_codes`.

Rules are intentionally small and deterministic:

1. an empty selector class is a wildcard for that class;
2. a non-empty domain selector matches when at least one canonical DNA domain overlaps;
3. a non-empty intent selector matches when at least one canonical DNA intent code overlaps;
4. when both selector classes are non-empty, both classes must match;
5. an entirely empty subscription accepts every valid `DNATraceV01`.

The result is a `DNATopicDecision` with explicit match evidence and a bounded reason (`matched`, `wildcard`, `domain_miss`, `intent_miss`).

## Publication gate

`publish_governed_trace_if_subscribed()` evaluates the trace before calling the existing node runtime.

Rejected trace:

```text
DNATrace
   |
   v
subscription decision = reject
   |
   +--> no PCM1 manifest
   +--> no PNB1 bundle
   +--> no PNC1 custody
```

Accepted trace:

```text
DNATrace
   |
   v
subscription decision = accept
   |
   v
existing dna_trace_to_descriptor()
   |
   v
PollicinoNodeRuntime.publish_governed()
```

No network-core change is required.

## Forward gate

`forward_governed_trace_if_subscribed()` does not trust a caller-supplied topic label. It reconstructs the authoritative canonical trace bytes already present in the source node store, parses them as `DNATraceV01`, and evaluates the subscription before invoking `NodeBearerTransport`.

Rejected forwarding returns before bearer evaluation or data-plane transfer. Therefore rejection creates no target manifest/custody state and cannot accidentally select a bearer or emit modeled wire bytes.

Accepted forwarding delegates to the existing `NodeBearerTransport.send_governed()` path unchanged.

## LoRaMesher vertical evidence

`tests/test_dna_topic_subscription_vertical_slice.py` covers three product-facing properties:

1. subscription matching uses only canonical DNA domains/intent codes and validates unsupported/duplicate selectors;
2. a mismatching trace is rejected before governed publication, leaving object/bundle counts unchanged;
3. a source-held mismatching trace is rejected before bearer selection, while a matching trace crosses the already validated LoRaMesher application-byte bridge and preserves the existing governed custody/accounting path.

The accepted path must still report:

```text
loramesher_host_application_bytes
```

for both governance and inner transfer accounting.

Validation: GitHub Actions `33293440813` — PASS for the complete project test suite and the targeted DNA Topic/Subscription vertical-slice tests.

## Persistent carried-node subscription lifecycle

`src/pollicino/integrations/dna_subscription_store.py` adds a node-bound application registry for local subscriptions. It is deliberately kept outside `PollicinoNodeRuntime`: the network/runtime layer persists governed objects and custody, while the application layer owns which DNA micro-information the carried node wants to accept.

The registry persists:

- a local subscription identifier;
- canonical DNA domain selectors;
- canonical DNA intent-code selectors;
- the currently active subscription;
- a SHA-256 integrity digest over canonical state;
- the owning node ID, so a registry cannot be silently reopened as a different node.

It does not disseminate subscriptions over the network and does not define a new DNA wire contract.

`tests/test_dna_subscription_persistence_lifecycle.py` validates the product-facing daily flow with more than one micro-information item:

```text
school / student A
    |
    | publishes social/700 + travel/17 DNATrace objects
    v
student B / active persisted subscription social/700
    |
    | travel/17 rejected before mule ingestion
    | social/700 accepted through LoRaMesher governed path
    | custody hop = 1
    v
mode -> OPPORTUNISTIC_DTN + process/runtime restart
    |
    | active subscription survives
    | social object/bundle/custody survive
    | rejected travel object remains absent
    v
territorial opportunistic bearer
    |
    | only persisted social/700 object is forwarded
    v
home gateway / RICH_HOME
    |
    | custody hop = 2
    | canonical DNATrace reconstructed exactly
```

Validation: GitHub Actions `33293580711` — PASS for the complete project test suite and the targeted subscription-persistence lifecycle tests.

## DNA application coordinator

`src/pollicino/integrations/dna_application.py` closes the manual-policy plumbing left by the first two slices.

`DNAApplicationCoordinator` binds one `PollicinoNodeRuntime` to the node-owned persistent `DNASubscriptionRegistry` and exposes two product-facing operations:

- `publish_active()` resolves the node's active subscription automatically before governed publication;
- `offer_to()` delegates acceptance to the target node's coordinator, so the target resolves and applies its own active subscription before bearer evaluation or transfer.

The target-owned decision is intentional. A sender does not need to persist or invent another node's interests merely to offer a DNA object. This preserves a clean future boundary for privacy, subscription exchange and transport-agnostic matching.

The coordinator fails closed when no active subscription exists, rejects a registry belonging to another node, and does not add any network or DNA wire fields.

`tests/test_dna_application_coordinator.py` validates a multi-item daily lifecycle:

```text
school publishes
    social/700 A
    social/700 B
    social/701
    travel/17
        |
        v
student mule subscription = social/700
        |
        +-- social/701 -> intent_miss before bearer selection
        +-- travel/17  -> domain_miss before bearer selection
        +-- social/700 A -> LoRaMesher governed hop / custody 1
        +-- social/700 B -> LoRaMesher governed hop / custody 1
        |
        v
carry + runtime restart
        |
        | coordinator reconstructed from persisted runtime + registry
        v
territorial opportunistic bearer
        |
        +-- social/700 A -> home / custody 2
        +-- social/700 B -> home / custody 2
        |
        v
RICH_HOME
```

Validation: GitHub Actions `33294244095` — PASS for the complete project test suite and the targeted DNA application-coordinator tests.

## What this proves

At host/model scope, Pollicino can now apply a concrete subscription policy above the transport layer and reuse exactly the same governed object and bearer runtime for accepted DNA micro-information.

The carried-node application persists/selects subscriptions across mode changes and process restarts. The application coordinator removes caller-supplied subscription plumbing: the target node owns its acceptance policy, multiple subscribed micro-information items survive the full school -> carry -> territory/home lifecycle, and non-subscribed items stop before ingestion/transfer.

This closes the Pollicino-side software slice required to exercise `topic/subscription-scoped DNA information` in `UC-DNA-001` without turning Topic into a routing protocol or adding DNA semantics to PollicinoNet core.

## What this does not prove

This checkpoint does not define the authoritative DNA Topic/Subscription contract, subscription dissemination, privacy/visibility policy, conflict resolution, user-facing subscription UI, RF capacity or LoRaMesher performance.

It also does not change the physical evidence boundary. Range, interference, wall/floor penetration, real airtime and energy remain behind **GATE PROVE FISICHE HW-006**.

## Next contract step belongs in DNA

The next architectural step should now happen in the DNA repository rather than by expanding the experimental Pollicino model.

DNA should define an authoritative, transport-independent Topic/Subscription contract that can replace `DNATopicSubscription` without requiring changes to the Pollicino network core. At minimum the DNA work must decide:

- whether `domains` and `intentCodes` remain the canonical subscription selectors or are wrapped by a richer topic expression;
- exact AND/OR/wildcard matching semantics;
- stable identifiers and versioning;
- ownership, privacy and visibility of subscriptions;
- local-only versus shareable subscription representations;
- expiry/lifetime and revocation semantics;
- canonical serialization and validation;
- relationship to `DNATrace`, discovery and transport envelopes;
- whether subscription dissemination is a separate optional protocol rather than part of the core contract;
- migration/adaptation from the validated Pollicino experimental semantics.

Until DNA publishes that authoritative contract, Pollicino should keep the current selector model explicitly experimental and avoid adding new subscription wire formats.
