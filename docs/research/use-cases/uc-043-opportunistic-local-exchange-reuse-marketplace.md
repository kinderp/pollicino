# UC-043 — Opportunistic Local Exchange and Reuse Marketplace

## Idea

Use PollicinoNet to match **local needs and offers for ordinary physical goods** even when the participants are not online at the same time and may live in different towns.

The first teaching scenario can be the September market for used school textbooks, but the protocol must remain generic enough for:

- textbooks and ordinary books;
- calculators and school supplies;
- uniforms and sports equipment;
- harmless electronic/lab components;
- tools and maker equipment;
- spare parts for teaching projects;
- donation, swap, loan or resale of reusable goods.

PollicinoNet does not need to become a payment network. The first version should do discovery, matching, reservation, private rendezvous and handover, while payment—if any—stays outside the protocol.

## Problem solved

Local reuse markets often have a simple information problem: one person needs an item and another person nearby already has it, but they do not know about each other at the right time.

A centralized Internet marketplace solves this when everyone is online. A sparse school/province network can instead let compact `Need` and `Offer` records move opportunistically until they meet.

Example:

```text
Need:
category = textbook
exact_id = ISBN 978...
edition = 2025
condition_min = good
price_max = 18 EUR
zone = Rometta/Venetico
expiry = 20 September

Offer:
category = textbook
exact_id = ISBN 978...
edition = 2025
condition = good
price = 15 EUR
zone = Spadafora
```

The same state machine also works for `calculator`, `uniform`, `Arduino shield`, `tripod`, `lab sensor` or `donation box`.

## Actors / nodes

- requester/buyer/borrower/donee;
- holder/seller/lender/donor;
- student relay/store-and-forward nodes;
- optional school rendezvous/cache node;
- optional teacher/moderator for a controlled classroom pilot;
- optional trusted pickup point such as the school;
- physical item itself as the final non-digital payload.

## Why PollicinoNet fits

This scenario composes several existing primitives cleanly:

- **UC-024 Content-Need Rendezvous:** `Need` can travel until it meets a compatible `Offer`;
- **UC-015 Resource Ledger:** listing/reservation/expiry state must converge under partitions;
- **UC-023 Private Mailbox:** negotiation and rendezvous can remain end-to-end private;
- **UC-042 Physical Asset Chain-of-Custody:** optional signed handover/receipt for the physical item;
- **UC-033 Rich-Bearer Handoff:** photos and larger descriptions can move after LoRa discovery.

The key PollicinoNet property is that the seller, buyer and relays do not need to be connected simultaneously.

The frozen LoRa PHY is unchanged.

## Information model

Keep the scarce-bearer record compact and generic.

```text
ExchangeNeed
  need_id
  category
  exact_item_id?        # ISBN, SKU, model/part ID, asset class...
  compatibility_tags
  condition_min?
  price_or_mode?        # sell/swap/loan/donate; optional price bound
  coarse_zone
  expiry
  privacy_class

ExchangeOffer
  offer_id
  category
  exact_item_id?
  compatibility_tags
  condition
  price_or_mode
  coarse_zone
  expiry

Reservation
  match_id
  offer_id
  need_id
  expiry
  state
```

A broad semantic description may help discovery, but any exact compatibility requirement must stay exact. For textbooks, for example, title similarity is not enough when ISBN/edition matters.

## Possible bearers

- **LoRa:** compact need/offer digest, exact item identifier, price/mode bucket, condition code, reservation state, expiry and rendezvous token;
- **BLE:** nearby detailed listing exchange and small photos;
- **Wi-Fi/LAN:** photos, descriptions, full listing synchronization and optional local marketplace UI;
- **Internet:** optional fast path or federation with a school/community service;
- **physical transport:** the item itself is carried from holder to receiver, possibly through a trusted pickup point.

## What we can test now in software

Build a deterministic exchange simulator with synthetic users/items.

Test:

- exact match by ISBN/model/part number;
- broader category/compatibility matching that resolves to an exact item before reservation;
- delayed propagation of needs and offers;
- duplicate/reordered listing delivery;
- one offer matched by multiple requesters;
- reservation conflicts and deterministic expiry;
- seller withdraws an offer while a stale copy is still circulating;
- buyer cancels before handover;
- donation/swap/loan modes in addition to sale;
- private negotiation using UC-023 rather than broadcasting names/phone numbers;
- optional photo/detail fetch through UC-033;
- final handover receipt without requiring an always-online central database;
- comparison of direct centralized matching vs delay-tolerant matching over UC-008 contact traces.

Useful metrics include match rate, time-to-match, stale-offer rate, reservation-conflict rate, duplicate overhead and time from match to completed handover.

## What requires real hardware

A first school/province experiment can use harmless synthetic listings and 4–6 student nodes:

1. two groups start with different offers/needs and no direct connection;
2. student-carried boards relay compact listing state;
3. one match is discovered only after a relay crosses groups;
4. the pair performs a measured LoRa discovery and UC-033 BLE/Wi-Fi detail exchange;
5. the physical object is handed over at a controlled school pickup point;
6. a receipt/reservation close event later converges through the network.

Start with textbooks, calculators or inert lab components. Do not infer radio range, match latency or reliability from simulation.

## Messina teaching scenario

At the beginning of the school year, prepare synthetic or opt-in listings distributed across coarse zones such as `Messina`, `Villafranca`, `Rometta/Venetico`, `Spadafora` and `Milazzo`.

A student in Rometta needs a specific textbook edition. The matching offer exists only on a Spadafora node. Neither party has a direct path. A third student's node ferries the compact need/offer state through ordinary controlled contacts. After a match, only a pseudonymous rendezvous token is propagated publicly; detailed communication remains private and pickup happens at school.

Run the same protocol a second time for a non-book item (for example a calculator or harmless electronics component) to prove that the protocol is **resource-generic**, not a special textbook application.

## Privacy / security

This use case can involve minors and social/economic information, so metadata discipline is essential.

- never broadcast home addresses, phone numbers, real names or exact habitual locations;
- use pseudonymous listing IDs and coarse zones;
- prefer school/community pickup points over private-home rendezvous;
- keep private negotiation end-to-end encrypted;
- avoid public exposure of a student's purchase history or financial limits;
- require explicit opt-in and short listing retention;
- authenticate state changes such as withdraw/reserve/complete;
- never treat a stale advertisement as proof that an item is still available;
- do not integrate payment, credit or financial custody into the first prototype;
- disallow unsafe, regulated or inappropriate goods in the teaching deployment.

## Difficulty

**Medium–High.** The network payloads are small and the user story is simple. The interesting distributed-systems problems are stale listings, conflicting reservations, privacy-preserving rendezvous and the boundary between digital matching and physical handover.

## Why this is distinct from existing use cases

UC-024 finds content; UC-015 reconciles resources; UC-042 tracks physical custody. UC-043 combines them into a **human exchange lifecycle**:

```text
NEED/OFFER
   ↓
MATCH
   ↓
PRIVATE NEGOTIATION
   ↓
RESERVATION
   ↓
PHYSICAL HANDOVER
   ↓
RECEIPT / CLOSE
```

That lifecycle is useful for many reusable goods, with used textbooks merely the best first seasonal demonstration.

## Research signal

Recent 2026 circular-economy research continues to treat community reuse and digital platforms as real social infrastructure for extending product lifetimes and enabling monetary and non-monetary exchange. PollicinoNet's research question is narrower: can the **matching and reservation control plane** remain useful under intermittent, store-carry-forward connectivity?

References:

- https://doi.org/10.26034/zh.ijccr.2026.9555
- https://doi.org/10.1177/00420980261418799
