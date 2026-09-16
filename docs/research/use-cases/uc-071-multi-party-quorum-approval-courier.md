# UC-071 — Multi-Party Quorum Approval Courier

## Idea

Some offline actions should not be authorized by one person or one key. PollicinoNet can carry **separate approvals from multiple authorized people** until a required quorum is reached, even when the approvers are never connected at the same time.

The action itself might be harmless but security-sensitive: release a new firmware campaign, unlock a protected dataset, approve a robot mission in a classroom demo, or authorize a destructive maintenance operation on test data. The target executes only when all policy conditions are satisfied.

## Problem solved

UC-026 covers a delegated one-use action ticket. This use case covers a different policy: **M-of-N or ordered approvals**.

Examples:

- teacher + lab administrator must both approve a firmware rollout;
- two independent custodians must approve release of an encrypted dataset;
- a student proposes a robot job, but teacher and safety supervisor both approve the exact mission hash;
- an emergency-drill resource transfer requires two roles before the ledger accepts it.

In a disconnected network the approvals may arrive hours apart and through different relays. We must never confuse `two signatures exist somewhere` with `the exact required quorum for this exact action is complete and fresh`.

## Actors / nodes

- action requester;
- 2–N independent approvers with distinct keys/roles;
- student relay/store-and-forward nodes;
- target/verifier that enforces the quorum policy;
- optional policy/directory node defining who is allowed to approve;
- optional audit/Raiatea node storing the complete approval trail.

## Why PollicinoNet fits

Approvals are small signed objects and naturally tolerate delay.

- **DISCOVERY:** `approval requested`, `1 of 2 approvals present`, `quorum complete`;
- **EXACT:** action hash, policy ID/version, approver identity/key, role, signature, approval sequence, freshness window and resulting authorization receipt;
- **SEMANTIC:** human labels such as `firmware release` or `dataset export`, never a substitute for the exact action hash.

A relay can transport an approval without being able to create or modify it. The target can verify the full quorum offline if it already possesses the required trust/policy state.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** action hash/reference, approval status, individual compact signatures where payload permits, quorum-complete receipt;
- **BLE:** local approval synchronization;
- **Wi-Fi/LAN:** larger policy directories, audit trails and evidence;
- **Internet:** optional fast path to approvers;
- **physical transport:** students carry pending approval state between disconnected groups.

## What we can test now in software

Define a `QuorumPolicy` such as:

```text
policy_id
policy_version
allowed_roles / allowed_keys
mode = threshold | ordered
required = M of N
validity_window
exact_action_hash
```

Then test:

- normal 2-of-3 approval;
- same person/key attempting to count twice;
- valid signatures over two slightly different action hashes;
- approval using an obsolete policy version;
- one approval arriving after the allowed window;
- ordered approval arriving in the wrong sequence;
- revoked approver key;
- duplicated/reordered relay delivery;
- partial quorum surviving node restart;
- action canceled before quorum completion;
- quorum complete but target already executed the one-use action;
- integration with UC-019 revocation, UC-020 freshness, UC-026 action tickets and UC-064 transparency gossip.

A key invariant is:

> quorum completion is evidence that the configured approval predicate passed; it is not proof that the action was executed, safe, or still appropriate.

## What requires real hardware

- 4–6 boards divided among requester, two or more approvers, relay and target;
- approvers intentionally unable to contact the target directly;
- real signatures verified on the target;
- a harmless target action such as toggling a test LED, enabling a synthetic job or unlocking a dummy file;
- measurements of approval convergence time and bytes transmitted.

Never begin with a safety-critical actuator, real destructive command or high-value credential.

## Messina teaching scenario

A test firmware campaign for student boards requires two roles: `teacher` and `lab-admin`. The teacher approves at school in Messina. The lab-admin approval is produced later at another checkpoint. Student relay nodes moving through Villafranca/Rometta carry the partial approval set. A target board may see one valid approval for hours but must remain blocked until the second independent approval arrives and all freshness/policy checks pass.

A second exercise creates two almost-identical actions with different hashes and deliberately splits approvals across them. The system must show two incomplete quorums, not merge them into one valid authorization.

## Privacy / security

- approvals reveal organizational relationships and should not contain unnecessary personal details;
- use role/key identifiers and keep human mappings outside radio payloads where possible;
- bind every signature to exact action hash, policy ID/version and freshness context;
- approvers must be distinct according to policy, not merely represented by different message IDs;
- stale or revoked keys must fail closed;
- quorum status should not leak sensitive action parameters when a hash/reference is enough;
- action execution needs its own idempotency/one-use protection;
- audit conflicting or rejected approvals rather than silently overwriting them.

## Difficulty

**Medium–High.** Cryptographic signing is straightforward; policy versioning, distinctness, ordered trails, cancellation and freshness under delayed delivery are the harder distributed-systems problems.

## Research / standards signal

An IETF Internet-Draft published on 6 September 2026, `draft-schrock-ep-quorum-04`, describes multi-party quorum authorization over exact action-bound human signoffs, including M-of-N and ordered approval trails. It is an Internet-Draft, not an Internet Standard, but it is a timely reference for the policy semantics PollicinoNet can test under disruption.

Reference:

- https://www.ietf.org/ietf-ftp/internet-drafts/draft-schrock-ep-quorum-04.html
