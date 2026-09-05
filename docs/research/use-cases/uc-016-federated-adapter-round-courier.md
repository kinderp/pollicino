# UC-016 — Federated Adapter Round Courier

## Idea

Study whether small AI updates can move through an intermittent student network without centralizing the raw training data. Each participating laptop trains a tiny local adapter or model update on a prepared local dataset, while PollicinoNet carries **round metadata, version coordinates and availability information**. The actual adapter bytes travel over Wi-Fi/LAN/Internet or by physical carry unless they are demonstrably small enough for the scarce link.

The first experiment should use synthetic or public data and a tiny model. This is a networking/reproducibility lab, not a claim that LoRa is suitable for transporting full LLM updates.

## Problem solved

Federated learning assumes that clients periodically contribute updates, but real edge nodes can be offline, bandwidth-limited and heterogeneous. A student node may complete local training long before it can reach the aggregator. We need to know which base model and round it trained against, whether its update is stale, where that exact update can be retrieved, and how to resume after missed contacts.

## Actors / nodes

- student laptops or small edge computers training locally;
- LoRa boards acting as discovery/store-and-forward companions;
- school aggregator/server;
- `PollicinoStore` caches for base models, adapters and round manifests;
- optional mobile relay transporting manifests or exact adapter objects.

## Why PollicinoNet fits

`DISCOVERY` can advertise compact tuples such as model family, round, adapter coordinate and expiry. `EXACT` identifies the base model, local dataset manifest where appropriate, adapter/update object and aggregate result by full cryptographic hashes. Store-and-forward naturally handles late clients and missed rounds. Content-addressed storage can avoid retransmitting a base model already cached at a node.

PollicinoNet remains the transport/discovery layer; training and aggregation stay in the AI application. The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** round ID, model/version hint, adapter coordinate, status, priority, expiry and compact authenticator;
- **BLE/Wi-Fi/LAN:** adapter/update transfer and base-model synchronization;
- **Internet:** remote artifact resolution or aggregation when available;
- **physical transport:** student-carried storage can ferry exact adapters/datasets between disconnected network islands.

## What we can test now in software

- use a tiny public/synthetic dataset split non-IID across virtual clients;
- train a small model or LoRA-style adapter locally and content-address every artifact;
- simulate clients missing one or more aggregation rounds;
- define policy for accepting, rejecting or rebasing stale updates;
- compare full-update transfer cost with adapter-only transfer cost;
- simulate contact windows and cache-aware artifact retrieval;
- verify every received adapter and aggregate artifact by exact hash;
- record round completion time, participating-client fraction, bytes per bearer, staleness and model quality separately.

A useful negative control is a client that advertises the wrong base-model hash: its update must not be silently aggregated.

## What requires real hardware

- at least two real training clients plus an aggregator;
- real LoRa exchange of round/availability metadata;
- at least one adapter transferred through a richer local bearer after LoRa rendezvous;
- measurements of actual metadata delivery and end-to-end round time.

No claim about LoRa energy, range or federated-training efficiency should be made without those measurements.

## Privacy / security

Federated learning is **not automatically private** merely because raw data remain local: model updates can leak information. Classroom experiments should therefore use public or synthetic data first. Updates and manifests need authentication, replay protection and exact base-model binding. Secure aggregation, differential privacy and poisoning defenses are separate research problems and should not be claimed until implemented and evaluated.

## Difficulty

**High.** It is strategically interesting because it joins PollicinoNet, edge AI and content-addressed artifacts, but the AI protocol, security and stale-round semantics add substantial complexity.

## Research signal

2025–2026 work on federated LoRA and other parameter-efficient fine-tuning methods continues to focus on heterogeneous clients and communication-constrained participation. The relevant lesson for PollicinoNet is architectural: exchange compact coordination information on the scarce bearer and move larger exact artifacts only when a suitable path exists.
