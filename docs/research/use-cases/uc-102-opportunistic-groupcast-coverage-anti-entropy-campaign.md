# UC-102 — Opportunistic Groupcast Coverage and Anti-Entropy Campaign

## Idea

Deliver **one small signed object to many intermittently connected nodes** while limiting redundant forwarding and keeping an explicit estimate of who has, may have or has not yet received it.

This is not just a bulletin application. It is a reusable dissemination experiment for:

- a signed school notice;
- one configuration epoch;
- one small emergency-drill update;
- one topic update from UC-083;
- one experiment manifest from UC-097;
- one trust/revocation checkpoint from UC-019.

The research question is:

> How quickly and with how much duplicate traffic can a bounded signed object spread through a real student store-and-forward network?

## Problem solved

Sending the same object independently to every destination wastes scarce contact opportunities. Pure epidemic forwarding can improve reachability, but may create too many duplicates. A central multicast tree is unrealistic when contacts are intermittent and no stable end-to-end path exists.

We need a delay-tolerant group dissemination profile that can:

- spread one exact object opportunistically;
- suppress obvious duplicate forwarding;
- recover after long partitions;
- distinguish `delivered`, `probably delivered`, `not observed` and `expired`;
- estimate eventual coverage without exposing a permanent membership/attendance list;
- remain bounded enough for a student LoRa experiment.

## Actors / nodes

- publisher/origin node;
- student relay/store-and-forward nodes;
- subscriber/group-member nodes;
- optional coverage collector;
- optional rich-bearer cache for the full object when the LoRa announcement is only a manifest.

## Why PollicinoNet fits

Groupcast is naturally compatible with human mobility and repeated opportunistic encounters.

- **DISCOVERY:** node indicates support for campaign/profile X and a coarse group/topic capability;
- **EXACT:** campaign ID, object hash, publisher signature, epoch, expiry, dissemination policy and optional receipt token;
- **SEMANTIC:** `covered`, `missing`, `unknown`, `expired`, `duplicate-suppressed` or `needs-rich-fetch` are local/collector interpretations.

For a tiny signed object, LoRa may carry the full payload. For larger objects, LoRa carries only manifest/hash and discovery while BLE/Wi-Fi/physical transport carries the content.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** signed small object or manifest, campaign epoch, compact inventory/digest, suppression hint and bounded delivery receipt;
- **BLE:** nearby anti-entropy exchange of small inventories or missing-object request;
- **Wi-Fi/LAN:** full content when the advertised object is too large;
- **Internet:** optional publisher/collector fast path;
- **physical transport:** student device carries the object between otherwise disconnected groups.

## What we can test now in software

Implement several dissemination policies over synthetic and later UC-008 contact traces:

1. naive send-to-every-contact;
2. epidemic forwarding with duplicate cache;
3. bounded-copy forwarding;
4. inventory/digest-first anti-entropy;
5. probability/contact-history aware forwarding;
6. priority-aware forwarding under UC-095 budgets.

Define a `GroupcastCampaign`:

```text
campaign_id
object_hash
publisher_id
publisher_signature
epoch
expiry
audience_profile
dissemination_policy_id
max_copies_or_budget_optional
receipt_profile
```

Each node keeps only bounded state such as:

```text
campaign_id
object_hash
seen_state
first_seen_epoch_optional
forward_budget_remaining_optional
receipt_token_optional
```

Test:

- two disconnected islands that later meet through one relay;
- duplicate encounters with the same carrier;
- stale campaign after a newer epoch exists;
- publisher cancellation or superseding version;
- relay buffer pressure;
- node joining late;
- corrupted object with matching campaign ID but wrong hash;
- signed object whose key is later revoked;
- coverage collector receiving receipts before some forwarding traces;
- privacy mode where only aggregate coverage is reported;
- large object where LoRa carries manifest only and rich-bearer fetch is delayed.

Useful metrics include eventual delivery fraction, time-to-X%-coverage, number of duplicate forwards, control bytes per newly reached node, copy count, expired-undelivered fraction and difference between simulated and physically observed contact traces.

## What requires real hardware

This should become one of the first larger student-network experiments because it scales naturally.

Start with 6–10 boards:

1. divide them into 2–3 groups that cannot all communicate directly;
2. publish one harmless signed campaign object;
3. let selected student relays move between checkpoints;
4. compare at least two forwarding/suppression policies on equivalent scripted contact schedules;
5. recover detailed logs later over Wi-Fi/physical transport;
6. repeat on natural mobility only after the controlled experiment is understood.

Do not claim coverage radius, dissemination speed or reliability from simulation. Those require the real campaign traces.

## Messina teaching scenario

A school node in Messina publishes a new signed `course-pack-index-v7` or experiment manifest. Groups in Villafranca, Rometta/Venetico and Spadafora are not simultaneously online.

Students carrying PollicinoNet nodes gradually bridge the partitions. Instead of every relay blindly retransmitting the object on every encounter, nodes first exchange a compact campaign inventory and suppress known duplicates.

At the end, the class can plot:

```text
time -> reached nodes
copies -> reached nodes
control bytes -> newly reached nodes
```

and compare controlled mobility with the real contact graph collected by UC-008.

For civil-protection-related teaching, the payload must remain a **drill message** until the system has independent validation.

## Privacy / security

- sign publisher objects and bind campaign state to the exact object hash;
- do not infer identity/attendance from missing receipts;
- support aggregate coverage instead of named membership reporting;
- use experiment-scoped pseudonyms for detailed trials;
- expire campaign/receipt state after a bounded retention window;
- protect against replay of superseded epochs;
- enforce local forwarding/storage budgets from UC-095;
- do not let untrusted publishers create unlimited high-priority campaigns;
- avoid broadcast amplification by hard copy/airtime/queue budgets;
- emergency/safety messages remain drills until independently validated;
- a coverage estimate is only as complete as the receipts/contact evidence available.

## Difficulty

**Medium-high.** Basic gossip is easy; bounded duplicate suppression, privacy-preserving coverage accounting, versioning and fair coexistence with other traffic are the valuable parts.

## Why this is distinct from nearby use cases

- **UC-002:** defines a signed bulletin application; UC-102 studies the reusable many-recipient dissemination/coverage mechanism.
- **UC-019:** defines trust/revocation state; UC-102 can be one mechanism for spreading such state.
- **UC-083:** defines persistent topic subscriptions; UC-102 focuses on how one resulting update propagates efficiently to a group.
- **UC-097:** orchestrates experiments; UC-102 is a concrete campaign that UC-097 can run and measure.
- **UC-098:** records selected relay contribution receipts; UC-102 can consume those receipts to analyze dissemination paths.

## Research / implementation signal

Epidemic and gossip-based forwarding are long-standing approaches for disconnected/mobile networks because they tolerate topology changes without a stable multicast tree. For PollicinoNet, the useful research step is not to reproduce generic epidemic routing, but to measure bounded-copy, anti-entropy and duplicate-suppression strategies on the actual student mobility/contact graph while keeping coverage accounting privacy-minimized.

References:

- https://www.rfc-editor.org/rfc/rfc4838.html
- https://www.rfc-editor.org/rfc/rfc9171.html
