# RAPID control-state amortization study

Status: MODEL_SYNTHETIC research checkpoint, 2026-08-27

## Research question

UC-DNA-001 and UC-CONTENT-001 can generate many small independent objects while the same nodes reuse knowledge about who tends to meet whom. The routing-control question is therefore not only:

> Is RAPID cheaper for one object?

but also:

> If the same meeting knowledge is reused across many topic messages, references or manifests, how many objects are required before that shared knowledge pays for itself?

This study deliberately avoids changing the one-selection-per-encounter RAPID runner. It is an explicit accounting sensitivity model, not a claim that the current runner already schedules many objects optimally in one encounter.

## Decomposition rule

For this first model, control bytes from the established 64-byte RAPID checkpoint are separated conservatively into:

### Shared within one reuse scope

- meeting/inter-meeting knowledge;
- optional shared node-index dictionary/bootstrap representation.

### Bundle-specific

- replica advertisements/tombstones;
- final-delivery state;
- queue/opportunity quote for that bundle.

This decomposition is intentionally visible in `rapid_amortization.py`; the module does not decide silently that arbitrary state is shareable.

It does **not** yet model:

- periodic refresh of meeting state;
- dictionary dissemination/fanout;
- authentication/encryption;
- topology changes;
- eviction or stale-state repair;
- multiple-object scheduling interactions.

## 64-byte checkpoint inputs

The prior validated one-object checkpoint was:

```text
Epidemic governed wire                         1890 B / object
RAPID governed transfer                       1260 B / object
```

### Full 128-bit pseudonymous IDs

From the explicit control breakdown:

```text
meeting knowledge (shared)                     384 B
replica + delivery + queue (per object)         314 B
bootstrap                                         0 B
```

One object therefore recomposes to:

```text
1260 + 384 + 314 = 1958 B
```

which is 68 B more than Epidemic.

### Shared u16 node indices

```text
meeting knowledge                               188 B
four-node dictionary representation              76 B
shared subtotal                                  264 B
replica + delivery + queue per object            244 B
```

One object:

```text
1260 + 264 + 244 = 1768 B
```

which is 122 B less than Epidemic under the already documented optimistic dictionary assumption.

## Amortization formula

For `N` otherwise-similar bundle decisions sharing the same reusable control state:

```text
Epidemic(N)
  = N * baseline_per_bundle

RAPID(N)
  = shared_control
  + N * (rapid_transfer_per_bundle + per_bundle_control)
```

No shared cost is divided away or ignored; it is paid once and its cost per bundle decreases only because more bundles reuse it.

## Validated sweep

GitHub Actions `33116687295` — PASS.

The validation ran the complete project suite plus `tests/test_net_rapid_amortization.py`; the targeted test confirms that the single-bundle checkpoints recompose exactly and that full-ID RAPID becomes cheaper at the second reused object under this explicit decomposition.

### Full-ID control

| Bundles reusing state | Epidemic | RAPID modeled | Delta RAPID - Epidemic | Shared control / bundle |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1890 | 1958 | +68 | 384.0 |
| 2 | 3780 | 3532 | -248 | 192.0 |
| 5 | 9450 | 8254 | -1196 | 76.8 |
| 10 | 18900 | 16124 | -2776 | 38.4 |
| 20 | 37800 | 31864 | -5936 | 19.2 |

Under these assumptions the observed one-object loser becomes cheaper at the second reused object.

### Shared-u16 indexed control

| Bundles reusing state | Epidemic | RAPID modeled | Delta RAPID - Epidemic | Shared control / bundle |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1890 | 1768 | -122 | 264.0 |
| 2 | 3780 | 3272 | -508 | 132.0 |
| 5 | 9450 | 7784 | -1666 | 52.8 |
| 10 | 18900 | 15304 | -3596 | 26.4 |
| 20 | 37800 | 30344 | -7456 | 13.2 |

Again, this indexed case remains optimistic because one dictionary representation is counted, not its intermittent-network distribution/authentication lifecycle.

## Interpretation for DNA micro-information

This result explains why a high-control strategy can be inappropriate if every tiny DNA observation pays the full routing-knowledge bootstrap independently, yet become reasonable if dozens of observations reuse one local encounter model.

The intended conceptual shape is therefore:

```text
node/campaign knowledge
  meeting history
  local topology hints
  scoped identities
          |
          +---- topic observation A
          +---- topic observation B
          +---- alert C
          +---- availability D
          +---- ...
```

rather than embedding a complete routing-state exchange into every micro-information object.

## Interpretation for content/reference mule

The same shared knowledge can guide multiple:

- magnet/info-hash references;
- URL/CID references;
- wanted-list entries;
- manifests;
- provider hints;
- chunk-transfer decisions.

The routing-control investment is then campaign/node state that can potentially serve many objects during the school/home mobility cycle.

## Gate implications

This study strengthens the case for keeping meeting knowledge separate from bundle identity, but it does **not** yet justify a general RAPID ranking API.

Before adoption, the next required questions are:

1. how long meeting knowledge remains useful before refresh;
2. how dictionary/state dissemination scales beyond a local scope;
3. whether a much simpler local encounter-history heuristic captures most of the same benefit;
4. how multiple bundles compete for one finite encounter budget;
5. whether these results survive trace-driven and later physical contact data.

## Evidence boundary

Every byte here is deterministic `MODEL_SYNTHETIC` accounting derived from the existing governed-transfer and research control-wire models. No physical airtime, range, collision, duty-cycle or energy superiority is claimed.

Real LoRa calibration remains behind **GATE PROVE FISICHE HW-006**.
