# RAPID object-size break-even sweep

Status: model-synthetic research checkpoint, 2026-08-27

## Question

Holding the routing pattern constant, how does object size change whether RAPID's explicit control-plane cost is worth the governed transfer traffic it avoids relative to Epidemic?

The experiment deliberately changes only the object/source-byte size and matching logical contact budget. It does not claim that these byte sizes are representative physical LoRa contact capacities.

## Fixed topology and behavior

For every size:

```text
A -> X   Epidemic replicates; RAPID skips uninformed X
A -> B   both can replicate
B -> D   both deliver at synthetic time 1025
```

RAPID therefore transfers two authoritative copies while Epidemic transfers three. The delivery outcome and delivery time are held equal so the comparison isolates modeled wire cost.

Sizes swept:

```text
16, 32, 64, 128, 256 source bytes
```

Each object is represented as one authoritative chunk; larger payloads may still fragment into multiple PNF1 frames according to the existing governed transfer path.

## Validation

GitHub Actions `33078337251`:

- full project suite: 261 passed, 2 skipped;
- targeted break-even test: PASS.

## Results

`delta = RAPID modeled total - Epidemic wire`.

Negative delta means RAPID is cheaper in this model.

| Object bytes | Epidemic wire | RAPID governed transfer | Full-ID control | Full-ID delta | Indexed control* | Indexed delta* |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 1668 | 1112 | 698 | +142 | 508 | -48 |
| 32 | 1716 | 1144 | 698 | +126 | 508 | -64 |
| 64 | 1890 | 1260 | 698 | +68 | 508 | -122 |
| 128 | 2160 | 1440 | 698 | -22 | 508 | -212 |
| 256 | 2778 | 1852 | 698 | -228 | 508 | -418 |

`*` Shared-u16 control includes one 76-byte canonical four-node dictionary representation, but not network-wide dissemination/fanout or authentication.

## Observed regime

### Self-contained 128-bit pseudonymous IDs

The simple self-contained control representation loses for 16/32/64-byte objects and becomes cheaper somewhere between the observed 64-byte and 128-byte checkpoints.

This is not assumed to be a smooth analytical threshold because existing Pollicino framing/manifest/ACK overhead produces step changes. The experiment reports the observed interval rather than inventing an interpolated exact break-even point.

### Shared u16 indices

Under the explicit assumption that one four-node dictionary representation is enough for the campaign, the indexed model is already cheaper at 16 bytes and its advantage grows as object size increases.

This is intentionally an optimistic shared-context case. Before adopting it we must account how the dictionary is established, refreshed, revoked and distributed across an intermittent network.

## What the sweep proves

It proves a narrow but important point:

> the value of smarter routing depends on the ratio between avoided transfer cost and routing-knowledge cost.

The same algorithm can be the wrong choice for a tiny isolated object and the better choice for a larger object under the same contact pattern.

This directly supports PollicinoNet's policy philosophy: routing should not become more sophisticated merely because a sophisticated algorithm exists. Its control information must pay for itself in the regime/use case being served.

## Relevance to current use cases

### UC-DNA-001

DNA can produce many tiny topic/observation objects. In that regime a per-object high-control routing strategy may be wasteful unless meeting/control state is strongly amortized across many objects and encounters.

This suggests that shared meeting knowledge should be treated as campaign/node state rather than retransmitted independently for every micro-information object.

### UC-CONTENT-001

Content references/manifests and wanted-state exchanges may be small, while the underlying content can be large. RAPID may be most useful when it prevents costly manifest/chunk replication or directs a compact reference toward a node likely to reach a rich resolver/gateway.

Again the relevant metric is total modeled bytes, not object size alone.

## Gate decision

**Decision: RAPID remains PROTOTYPE.**

Do not yet add a general RAPID ranking hook to the common routing comparator.

The next scientifically useful dimension is not another routing algorithm. It is **control-state amortization and network size**:

- how control cost changes with node count;
- how often meeting state must be refreshed;
- how many bundles can reuse one control exchange;
- cost of distributing/reconciling the shared node-index dictionary;
- whether a simple local encounter-history heuristic captures most of RAPID's benefit with less control state.

A simpler heuristic should remain a mandatory baseline under the Use-Case Justification Gate.

## Evidence boundary

All values are deterministic `MODEL_SYNTHETIC` bytes. No physical airtime, range, energy, collision, duty-cycle or field-network superiority is claimed. Those remain behind **GATE PROVE FISICHE HW-006**.
