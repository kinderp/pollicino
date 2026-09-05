# Literature round 2 — summary and corrected priorities

Status: 2026-08-25

This checkpoint consolidates the use-case-gated studies added in the same round:

- `dtn-routing-baselines-use-case-study.md`
- `pna2-reconciliation-regime-study.md`
- `lora-substrate-use-case-study.md`

## What changed

The project should pause invention of new routing/mesh architecture and use literature baselines to test whether custom work is justified.

### Routing

Implement established strategies as benchmark controls before adding new custom algorithms:

1. Direct Delivery / First Contact
2. Epidemic
3. Spray-and-Wait
4. PRoPHET
5. reduced RAPID-like utility baseline
6. MaxProp later when finite-buffer/drop experiments are active

### PNA2

A previous million-chunk example was hypothetical and outside current PCM1, which caps manifests at 65,535 chunks. The current maximum PNA1 bitmap is still 8,231 bytes, enough to justify a real scarce-link use case.

The key insight is that current chunk indices fit in uint16, so simple codecs are exceptionally competitive:

- sparse missing list: roughly 2 bytes per missing chunk;
- missing ranges: roughly 4 bytes per contiguous range;
- minisketch16: roughly 2 bytes per configured difference element, but gains symmetric reconciliation semantics;
- IBLT/rateless: only justified in more difficult partial/partial or unknown-difference regimes.

Therefore PNA2 should be a codec/regime benchmark, not an IBLT feature.

### LoRa substrate

- raw LoRa remains the evidence/reference bearer;
- LoRaMesher passes the gate only for the connected-cluster use case and should be prototyped/benchmarked as an underlying bearer;
- Reticulum remains research/overhead comparison because adopting a new heterogeneous secure network substrate has not passed the architecture gate;
- practical projects such as FreakWAN/Meshtastic remain external baselines.

## Near-term order after literature

1. build canonical DTN routing baseline scaffold;
2. build PNA2 codec benchmark with simple codecs first;
3. write BPv7 semantic ADR without implementing BPv7;
4. prototype host-side LoRaMesher bearer only after the more central baselines exist;
5. add The ONE trace interoperability when canonical routing baselines are available;
6. keep Reticulum on the research shelf until at least two concrete adoption use cases emerge.

## Hardware boundary

None of the literature/baseline work above requires new HW-006 measurements.

HW-006 becomes necessary before claiming that any routing algorithm or substrate is superior on the real LoRa student network, or before converting physical contact duration/geometry into scheduling capacity.
