# UC-CONSENT-001 — Delay-tolerant consent and retention-policy ferry

Status: RESEARCH / PRIVACY INFRASTRUCTURE PROTOTYPE, synthetic policy fixtures only until governance is defined

## Problem

A disconnected node can hold a perfectly intact object while having stale information about whether that object is still allowed to be retained, forwarded or exposed to a particular application.

The concrete question is:

> can PollicinoNet move small, signed, monotonic policy updates through the same delayed network as the data itself, so a node can stop forwarding or retaining an object after it learns a newer restriction without pretending that disconnected nodes have instantaneous policy state?

This is distinct from `UC-TRUST-001`. TRUST concerns keys, trust roots and revocation of security credentials. CONSENT concerns **authorization/usage state attached to data or a data scope**: for example retention, visibility, allowed topic, allowed resolver or an explicit withdrawal where consent is the chosen lawful basis.

It is also not a claim that a technical protocol alone satisfies GDPR or school privacy obligations. Consent is only one possible legal basis, and legal/organizational requirements remain outside this prototype.

## Actors / nodes

- data subject or synthetic policy owner;
- school/privacy authority or application authority that signs policy generations;
- Pollicino nodes carrying data and policy state;
- DNA/DNATrace application layer where topic/visibility/expiry semantics already exist;
- optional home/school gateway with richer policy-resolution access;
- auditor/test harness that checks what a node knew at each forwarding decision.

## Why PollicinoNet fits

The policy object is small but time-sensitive, while the network is explicitly intermittent. Pollicino already has exact objects, TTL/hop governance, custody, persistent stores and delayed multi-hop delivery.

A useful policy record can remain application-level and compact:

```text
policy_scope = opaque-data-scope
policy_generation = 17
issued_at = ...
retention_until = ...
forwarding = deny | allow
allowed_topics = [...]
allowed_resolvers = [...]
reason_code = ...
signature/reference = ...
```

The scarce link should not carry personal profile data merely to enforce the policy.

## Possible bearers

- LoRa: compact signed policy generations and acknowledgement state;
- BLE/NFC/QR: local policy handoff during an authorized interaction;
- Wi-Fi/LAN/Internet: complete policy resolution, audit and richer authorization services;
- physical carry: student-carried nodes propagate newer generations between otherwise disconnected clusters.

## What we can test immediately in software

Use only synthetic identities and objects.

Example experiment:

1. nodes A/B/C all know policy generation 10 and hold an authorized synthetic object;
2. authority publishes generation 11 with `forwarding=deny` and shorter retention;
3. only A learns generation 11 immediately;
4. B and C remain partitioned and continue under the last policy they actually know;
5. the new policy propagates through later contacts;
6. every forwarding decision records the policy generation available locally at that moment.

Compare:

- TTL-only behavior;
- latest-known policy generation with no negative state;
- explicit signed `deny` generation with persistent anti-rollback state;
- optional policy reference resolved later on a rich link.

Metrics:

- stale-policy exposure window;
- post-update forwards made before versus after the node learned the new generation;
- bytes spent on policy dissemination;
- anti-rollback failures detected;
- retained objects purged after the policy becomes locally effective;
- number of objects whose policy cannot be resolved and therefore fail closed.

The prototype must never claim that a disconnected peer could have obeyed a policy version it had no way to receive.

## Messina student-network scenario

A future school pilot could use only synthetic teaching objects and pseudonymous logical clusters such as `Rometta-like`, `Spadafora-like`, `Saponara-like` and `Villafranca-like`.

A morning school hub can issue policy generation 21. Students then carry nodes into afternoon clusters. Some nodes receive generation 21 only hours later. The experiment measures propagation and enforcement without encoding student names, addresses or real consent records.

A later DNA integration can test topic/visibility/expiry semantics, but no real student profile should be introduced merely to make the experiment realistic.

## What requires real hardware

After HW-006 and a separate privacy/security gate:

- persistence across reboot/power loss;
- verification cost of signed policy records on the embedded target;
- actual propagation latency through measured contacts;
- storage-pressure interactions when a policy requires purge;
- behavior when the board loses power between receiving and committing a newer generation.

## Privacy and security

- use synthetic policy owners and synthetic data first;
- policy generations must be authenticated and rollback-resistant;
- a stale peer must not overwrite a newer deny/restriction with an older allow state;
- minimize policy metadata so it does not reveal the subject or sensitive purpose over radio;
- encryption keys and access control may be required in addition to forwarding policy;
- do not treat deletion from one node as proof that all disconnected copies have been erased;
- document the difference between technical policy state and legal compliance.

Where processing is actually based on consent, GDPR Article 7(3) provides that consent can be withdrawn at any time. That legal fact motivates the technical stale-policy problem; this prototype does not decide the lawful basis or compliance process.

## Difficulty

**High**, mostly because correctness under stale state, rollback resistance and privacy semantics matter more than transport complexity.

## Success / kill criteria

Continue if a small monotonic policy object materially reduces unauthorized post-update forwarding after propagation, with explicit and measurable stale windows and modest wire cost.

Defer any generic policy framework if the real applications can safely use simpler expiry/TTL or if the prototype cannot give a precise answer to: “which policy generation did this node know when it forwarded the object?”

## Related-work note

The legal and privacy ecosystem already distinguishes consent/authorization state from the data itself, and consent withdrawal creates a real update problem. PollicinoNet's research question is narrower: how to propagate and enforce a small monotonic application-policy generation in a disconnected store-carry-forward network.

## Physical evidence boundary

No real policy-propagation latency, student privacy claim or compliance claim is supported until physical/contact evidence and governance exist. The frozen LoRa PHY and HW-006 sequence remain unchanged.