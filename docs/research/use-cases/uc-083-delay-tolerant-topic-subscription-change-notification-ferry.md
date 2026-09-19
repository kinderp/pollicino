# UC-083 — Delay-Tolerant Topic Subscription and Change-Notification Ferry

## Idea

Let a node express a **standing interest** such as `course/python`, `map/rometta`, `sensor/air-quality`, `software/romeo` or `bulletin/school`, then receive later change notifications even when publisher and subscriber are never connected at the same time.

This differs from a one-shot content request. A subscription remains active for a bounded period, can be renewed or cancelled, and may produce many future notifications.

## Problem solved

UC-024 lets a node ask for one content item or need. UC-002 distributes a signed bulletin. Real users also need something in between:

- “tell me whenever this course pack changes”;
- “notify me when a newer map bundle for this coarse area exists”;
- “send me only future alerts from this sensor campaign”;
- “tell me when a new signed firmware release is available”;
- “notify this classroom cache when Raiatea gains a newer document version.”

A normal pub/sub system assumes a broker or continuous route. In a sparse student network, subscription state and later events may have to travel independently through different relays.

## Actors / nodes

- subscriber student/device;
- publisher such as a school server, sensor gateway, Raiatea node or software-release node;
- student relay/store-and-forward nodes;
- optional topic cache/broker that is not continuously reachable;
- optional Internet gateway when available.

## Why PollicinoNet fits

Subscription control and notification metadata are naturally small.

- **DISCOVERY:** topic namespace, subscription existence, publisher availability, newest-version hint;
- **EXACT:** subscription ID, exact topic/version namespace, publisher identity, notification sequence/version, object hash and expiry;
- **SEMANTIC:** human labels such as `python-course`, `route-update` or `environment`, useful for discovery but never a substitute for exact object identity.

A relay can carry a subscription toward publishers, and later carry matching notifications back toward the subscriber. Bulk content still moves over a richer bearer.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** topic/subscription ID, version summary, expiry, cancellation, compact notification metadata and object hash;
- **BLE:** nearby synchronization of pending subscriptions/notifications;
- **Wi-Fi/LAN:** actual document/model/map/update payloads and large event history;
- **Internet:** optional fast path to an authoritative publisher;
- **physical transport:** a student device carries subscription state one way and notifications/content later in the opposite direction.

## What we can test now in software

Define a bounded `Subscription`:

```text
subscription_id
subscriber_pseudonym
topic_id
publisher_scope
start_epoch
expiry
last_seen_version
priority
privacy_class
```

and a `ChangeNotification`:

```text
topic_id
publisher_id
version
object_hash
created_epoch
expiry
notification_id
```

Then test:

- subscriber and publisher never online simultaneously;
- duplicate subscription propagation;
- one subscription matching many later versions;
- cancellation overtaking an older renewal;
- expired subscription arriving late;
- missed versions followed by reconciliation;
- publisher rollback or conflicting version announcements;
- several publishers under one semantic topic but different exact identities;
- bounded fan-out when many subscribers want the same topic;
- notification summary arriving before the actual content;
- privacy-preserving opaque topic IDs versus human-readable topics.

Useful metrics include time-to-first-notification, notification delivery ratio, redundant copies, stale-notification count, missed-version recovery and bytes per bearer.

A useful invariant is:

> a notification may be delayed or duplicated, but it must remain bound to the exact publisher/topic/version that created it.

## What requires real hardware

A first physical experiment needs only:

- 4–6 LoRa nodes;
- one publisher node at school;
- two subscriber groups intentionally disconnected from it;
- one or two student relays moving between groups;
- a small versioned payload transferred later over Wi-Fi/BLE.

Example: subscriber A asks for future updates of a Python course pack; publisher releases v2 while A is offline; a relay later transports only the compact notification; the exact PDF/package is retrieved when a rich bearer appears.

## Messina teaching scenario

Create coarse islands such as `school/Messina`, `Villafranca`, `Rometta-Venetico` and `Spadafora`. Students subscribe to harmless synthetic topics before leaving school. During the day the school node publishes a new version to only one island. Relay nodes carry subscription summaries and later notifications across the remaining islands.

The exercise should compare one-shot polling against bounded subscriptions on the same measured contact traces from UC-008.

## Privacy / security

Subscriptions reveal interests, sometimes more sensitively than the content itself.

- do not broadcast human-readable sensitive topics;
- prefer opaque topic IDs or coarse public namespaces;
- give subscriptions explicit expiry and retention limits;
- authenticate publishers;
- treat cancellation and renewal as exact state transitions;
- never infer that a user still wants a topic merely because an old subscription reappears;
- do not place student names, class details, health topics or home-location interests in public LoRa metadata;
- possessing a notification does not automatically authorize access to the referenced content.

## Difficulty

**Medium.** Basic pub/sub state is simple. The interesting work is expiry, cancellation races, missed-version recovery, fan-out control and privacy of long-lived interests.

## Why this is distinct from nearby use cases

- **UC-002:** pushes individual signed bulletins.
- **UC-024:** represents a one-shot need/request.
- **UC-040:** predicts replica placement from demand/contact traces.
- **UC-083:** adds a persistent, bounded **future-interest contract** that can generate multiple notifications over time.

## Research / implementation signal

Publish/subscribe has long been studied for delay-tolerant sensor networks because asynchronous event delivery naturally matches intermittent connectivity. PollicinoNet can revisit this pattern with modern identity, exact-content binding, privacy and measured student mobility rather than assuming a permanent broker.

References:

- https://doi.org/10.3390/s91007580
- https://www.rfc-editor.org/rfc/rfc9171.html
