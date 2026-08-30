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

## What this proves

At host/model scope, Pollicino can now apply a concrete subscription policy above the transport layer and then reuse exactly the same governed object and bearer runtime for accepted DNA micro-information.

This closes the first software slice of the `topic/subscription-scoped DNA information` requirement in `UC-DNA-001` without turning Topic into a new routing protocol or adding DNA semantics to PollicinoNet core.

## What this does not prove

This checkpoint does not define the future authoritative DNA Topic/Subscription contract, subscription dissemination, privacy policy, conflict resolution, persistence/UI, RF capacity or LoRaMesher performance.

It also does not change the physical evidence boundary. Range, interference, wall/floor penetration, real airtime and energy remain behind **GATE PROVE FISICHE HW-006**.

## Next concrete software step

After this gate is green, the next product step should remain use-case driven: persist/select subscriptions at the carried-node application boundary and exercise more than one subscribed DNA micro-information item across the school -> carry -> territory/home lifecycle. The filtering semantics should move into DNA itself only when DNA publishes an authoritative contract.
