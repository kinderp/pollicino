# UC-FL-001 — Delay-tolerant federated evaluation and learning rendezvous

Status: RESEARCH / SOFTWARE PROTOTYPE

## Problem

Edge devices may collect local data or run local evaluation/training while connectivity to an aggregator is intermittent. When they finally meet a relay or school gateway, their contribution can already be based on an old model generation. In federated learning this **staleness** can change convergence and fairness; simply delivering every old update eventually is not necessarily correct.

This use case is materially different from `UC-AI-001`:

- `UC-AI-001` asks whether nodes have the same model/adapter/dataset artifacts and how to retrieve missing versions;
- `UC-FL-001` asks how asynchronous **computed contributions** are admitted, weighted, rejected or deferred when they were produced from different model generations.

The first PollicinoNet experiment should use synthetic/public datasets and tiny models. It must not assume that full modern neural-network gradients fit in a LoRa contact.

## Actors / nodes

- edge clients: laptops, small computers, robots or sensor gateways with local synthetic/public data;
- school/lab model aggregator;
- student-carried relay nodes;
- optional home Wi-Fi gateways;
- optional GPU workstation for richer aggregation.

The LoRa board may be the network/storage courier even when local ML computation happens on a companion device.

## Messina educational scenario

The school publishes model generation `G20`. Several pseudonymous territorial clients evaluate or train locally during the afternoon. Client A returns an update based on `G20`; client B stays disconnected and returns two days later after the school model has reached `G23`.

PollicinoNet can carry small descriptors such as:

```text
update_id
base_model_generation
artifact_hash/reference
sample_count_bucket
compact evaluation metrics
created_at + uncertainty
```

Tiny model deltas may be used in a controlled experiment. Larger gradients/checkpoints should remain references and move through Wi-Fi/LAN/physical storage unless later measured evidence justifies otherwise.

## Why PollicinoNet fits

The network already studies exactly the conditions that make asynchronous edge learning difficult:

- intermittent contacts;
- physical mobility;
- finite contact/storage budget;
- version/generation reconciliation;
- delayed delivery;
- multiple bearers;
- replayable synthetic contact windows and, later, `UC-TRACE-001` measured traces.

The interesting question is not “can LoRa train an LLM?”. It is whether delay-tolerant object/state handling can make **staleness and contribution provenance explicit** while rich bearers carry large artifacts.

## Possible bearers

- LoRa for model generation, update descriptors, evaluation summaries, hashes and very small synthetic deltas;
- BLE for companion-device exchange;
- Wi-Fi/LAN for model weights, checkpoints and larger update payloads;
- Internet for optional central aggregation/artifact retrieval;
- physical carry for delayed update/model movement.

## What can be tested now in software

Start with a tiny linear/logistic model or similarly transparent test model.

1. non-IID synthetic client datasets;
2. clients with different contact/inter-contact schedules;
3. synchronous FedAvg-style baseline;
4. naive asynchronous “accept everything” baseline;
5. staleness threshold/rejection baseline;
6. simple staleness-weighted aggregation;
7. participation fairness when the same clients meet the hub more often;
8. compressed/tiny update versus reference-to-rich-update regimes;
9. model generation rollback/replay;
10. compare synthetic mobility with future TRACE replay without changing the ML workload.

Keep networking metrics and ML metrics together: a scheme that saves bytes but destroys convergence is not a win, and a scheme that improves accuracy by assuming impossible contact capacity is not evidence.

## What requires real hardware

Hardware is required before claiming:

- compute time or energy on target edge devices;
- actual size fraction deliverable during LoRa contacts;
- companion BLE/Wi-Fi handoff reliability;
- real contact/inter-contact distributions;
- thermal/battery feasibility;
- any advantage of a mobile relay on real training wall-clock time.

HW-006 remains the RF gate. Separate compute/energy measurement is also needed; HW-006 alone does not validate ML feasibility.

## Privacy / security

Federated learning is **not automatically private** merely because raw data stays local.

Requirements:

- synthetic/public data first;
- no student grades, biometrics, personal messages or mobility histories as training data;
- signed model-generation and update provenance;
- explicit replay/rollback protection;
- poisoning/outlier handling before any untrusted-client experiment;
- treat model updates as potentially sensitive;
- encryption in transit/storage as appropriate;
- secure aggregation or differential privacy, if ever needed, must pass their own use-case/security gates rather than being assumed here.

## Implementation difficulty

**High.** The network descriptors are simple, but correct ML evaluation requires controlling model/data heterogeneity, staleness, fairness, poisoning and communication cost simultaneously.

## Minimal measurable hypotheses

- H1: intermittent mobility creates staleness patterns that make naive “eventually aggregate everything” measurably worse than a simple staleness-aware baseline.
- H2: Pollicino generation/reference primitives can represent the required provenance without a new general wire protocol.
- H3: small evaluation summaries and update references create useful LoRa traffic even when full ML deltas remain on rich bearers.

## Metrics

Networking:

- bytes per contribution;
- delivery/update age;
- contribution drop/expiry rate;
- relay forwards/storage;
- rich-bearer bytes versus LoRa bytes.

Learning:

- validation loss/accuracy;
- rounds or wall-clock model time to target quality in the synthetic model;
- staleness distribution;
- contribution share by client/cohort;
- divergence/failure under stale updates.

## Success / kill criterion

**Continue** only if a small reproducible model demonstrates a real interaction between contact-induced staleness and learning behavior that is not already covered by `UC-AI-001` artifact synchronization.

**Defer** any embedded/full-gradient work if the research value is already captured by descriptors/references and rich-bearer transfer.

## Gate decision

**RESEARCH + ISOLATED SOFTWARE PROTOTYPE.** No production FL stack, new PHY or new cryptographic protocol is justified yet.

## Related research precedent

Mobility-aware asynchronous FL research explicitly studies intermittent connectivity, contact/inter-contact time, model staleness and gradient sparsification: https://arxiv.org/abs/2506.07328 .

Recent work continues to show that stale updates and heterogeneous client participation are first-class FL problems, for example FedStale: https://doi.org/10.3233/FAIA240849 .

These results motivate a workload; they are not performance claims for PollicinoNet.
