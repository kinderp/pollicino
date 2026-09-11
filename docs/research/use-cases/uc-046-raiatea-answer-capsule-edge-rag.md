# UC-046 — Raiatea Answer Capsule / Offline Edge RAG

## Idea

Move a compact natural-language question through PollicinoNet to a node that already owns a Raiatea/document corpus and local model, then return a **small answer capsule tied to exact source references**.

UC-034 already returns ranked document/object references. UC-046 adds one more optional layer: local retrieval + generation at the data node, so the requester may receive a short useful answer before fetching the full source document.

The AI answer is never the authority. Exact evidence references remain first-class and can be retrieved later over richer bearers.

## Problem solved

A disconnected requester may need one fact or explanation, while the source corpus, vector index and local model are far too large to move.

Example:

```text
Requester:
"What is the difference between a Workspace and a Surface?"

School/Raiatea node:
- has the full corpus/index/model
- retrieves exact source passages
- creates a compact answer
- returns source object IDs / section IDs / evidence hashes
```

Instead of moving gigabytes, the network moves the question, compact answer and proof coordinates.

## Actors / nodes

- student/teacher requester;
- Raiatea/document corpus node;
- local retrieval engine;
- optional local LLM/SLM;
- student relay/store-and-forward nodes;
- optional school server/NAS/GPU node;
- optional rich-bearer provider for full evidence retrieval.

## Why PollicinoNet fits

The request and answer can be tiny relative to the corpus and model.

- **DISCOVERY:** which node can answer a corpus/domain/version;
- **EXACT:** query ID, corpus/index version, source object IDs, section/chunk IDs and evidence hashes;
- **SEMANTIC:** natural-language question, retrieval/reranking and generated answer.

The semantic layer may be wrong. The exact evidence layer tells the requester what source was actually used.

Store-carry-forward allows query and answer to travel at different times through different relays.

The frozen LoRa PHY is unchanged.

## Answer capsule

A first deterministic envelope can look like:

```text
AnswerCapsule
  query_id
  corpus_version
  model_id
  retriever_id
  answer_text
  confidence_or_status
  evidence_refs[]
  created_epoch
  expiry
  signature
```

Useful statuses should include at least:

```text
ANSWERED
INSUFFICIENT_EVIDENCE
AMBIGUOUS
REFUSED_BY_POLICY
MODEL_UNAVAILABLE
```

It is better to return `INSUFFICIENT_EVIDENCE` than fabricate a fluent answer.

## Possible bearers

- **LoRa:** compact query, status, very short answer capsule and exact evidence IDs when measured encoded size/airtime permits;
- **BLE:** longer answer/evidence snippets;
- **Wi-Fi/LAN:** full source documents, larger context, embeddings or model updates;
- **Internet:** optional fallback model/provider only under policy;
- **physical transport:** a student node carries queued encrypted questions/results between disconnected requester and corpus node.

## What we can test now in software

Use a small public/versioned teaching corpus and a local model.

Test:

- query delivered after long delay;
- corpus version changes before query arrives;
- retrieval-only result vs generated answer;
- answer always carries exact evidence refs;
- evidence ref points to wrong/stale corpus version and is rejected;
- deliberate unanswerable questions;
- two corpus nodes produce different answers for the same query;
- model/retriever version is explicit;
- duplicate query suppression;
- cached answer reuse only when query + corpus/model policy allow it;
- encrypted query envelopes so relays cannot read sensitive questions;
- compact answer mode vs richer answer mode;
- selective final source fetch through UC-024/UC-033;
- hallucination test set where the expected behavior is abstention.

Useful metrics include query turnaround, answer/evidence bytes, evidence-fetch rate, abstention rate, stale-answer rejection and factual agreement with a manually checked source set.

## What requires real hardware

A first physical experiment needs:

- one requester board/device;
- one moving relay;
- one laptop/RPi/server running the local Raiatea-like corpus and model;
- real LoRa transport of compact query/status/answer metadata where payload measurements allow it;
- optional BLE/Wi-Fi retrieval of the selected source document;
- measured end-to-end turnaround and encoded byte counts.

Do not claim that a particular answer size or latency is practical over LoRa until measured with the actual PollicinoNet encoding and PHY configuration.

## Messina teaching scenario

Put a versioned local knowledge base on a school server containing course notes, school technical documentation or public-domain reference material.

A requester in another network island asks a harmless course question. A student relay carries the encrypted query to school. The Raiatea node returns:

1. a short answer capsule;
2. exact source object/section references;
3. a flag if evidence was insufficient.

The relay carries the capsule back. If the student wants the full source PDF or Markdown page, UC-024/UC-033 retrieves it later over Wi-Fi/BLE.

This makes an excellent visible demonstration because a real question is answered while the large corpus and model never leave the server.

## Privacy / security

Questions can reveal sensitive interests even when the corpus is public.

- encrypt private queries for the intended answer node;
- minimize query retention and logs;
- expose only coarse capability/corpus discovery metadata;
- treat generated text as untrusted semantic output;
- bind every answer to exact corpus/model/retriever versions;
- retain exact evidence references;
- do not use the teaching prototype for medical, emergency, legal or other safety-critical decision making;
- never let an AI answer grant authorization or trigger privileged actions by itself;
- allow explicit abstention when evidence is missing.

## Difficulty

**High.** Transport is easy compared with evaluation. The hard part is provenance, hallucination/abstention behavior, version binding, privacy and deciding how much generated text is worth sending over a scarce bearer.

## Why this is distinct from UC-034

UC-034 answers:

> "Which documents/passages should I look at?"

UC-046 optionally answers:

> "Given those passages, can the edge node return a short source-bound explanation now?"

The full evidence remains retrievable later, so UC-046 extends rather than replaces UC-034.

## Research signal

Offline/local RAG projects in 2026 are already experimenting with source-cited answers and radio-friendly compact response modes for disconnected use. This validates the design question—not any performance result for PollicinoNet.

References:

- https://github.com/bdkoeh/survivalRAG
- https://www.reddit.com/r/meshtastic/comments/1rlz555/i_open_sourced_an_offline_survivalmedical_rag/
