# PollicinoNet bundle governance

This note defines the first governance layer above durable store-and-forward.
It is intentionally transport-independent and can be validated without a live
radio.

## Why this layer exists

Store-and-forward answers *how verified chunks move*. It does not by itself
answer:

- how long a bundle may remain alive;
- how many custody handoffs it may traverse;
- which peer currently holds verified partial/full custody;
- whether an orchestrator replayed the same encounter twice;
- how much governance traffic itself costs on the wire.

The governance layer closes those gaps without changing PNF1, PCM1 or PNA1.

## PNB1 forwarding envelope

`ForwardBundle` is bound to both:

- the PCM1 manifest fingerprint;
- the SHA-256 digest of the originating PND1 discovery descriptor.

The PND1 descriptor supplies:

- `ttl_seconds`;
- `hop_limit`;
- `nonce`.

The bundle ID is stable across the route. A PNB1 forwarding envelope carries a
`current_hop`, but that mutable route position is deliberately excluded from
the bundle identity.

TTL is evaluated at the beginning of an encounter using explicit experiment
logical time. If the bundle is expired, the encounter is rejected before any
PNB1/PNF1 byte is transmitted.

The hop limit counts custody handoffs. Origin custody is hop 0. A bundle with
`hop_limit=1` may move origin -> relay but the relay may not hand it to a third
peer.

## PNC1 custody receipt

After a forwarded contact, the target recomputes actual verified storage state
and returns a PNC1 custody receipt containing:

- bundle ID;
- target peer ID;
- acquisition time;
- hop count;
- number of currently verified chunks;
- complete/partial state.

A custody record is **not** a cryptographic promise that a peer will keep data
forever. It is an experiment-level statement that the target had verified
local custody when the receipt was produced.

For a peer reached again through a longer path, the ledger preserves its
shortest known hop count while refreshing the current verified inventory.

## Duplicate suppression

Duplicate suppression is intentionally narrow and reproducible.

Each scheduled encounter has an explicit `contact_id`. Replaying the same
bundle/contact ID is a zero-wire no-op. This protects orchestration restart and
log replay from duplicating an already committed encounter.

A genuinely new physical encounter must use a new contact ID. It still sends
normal control traffic, while PNA1 suppresses chunks that the target already
possesses.

This distinction is important: contact-id idempotency is not claimed as a
general anti-flooding or routing-deduplication algorithm.

## Durable custody ledger

`CustodyLedger` can be written atomically with a SHA-256 checksum and reloaded
after a process restart. The ledger contains custody observations and processed
contact IDs; actual chunk truth remains the content-addressed store.

If disk content is corrupt, the store's SHA-256 verification wins over a stale
custody observation. A later real encounter should use a new contact ID and can
repair the missing/corrupt chunk through ordinary PNA1-driven forwarding.

The checksum protects against accidental corruption, not a hostile writer.
Authentication/encryption remain separate security policy work.

## Governed route and TRC

`run_governed_store_forward_schedule` applies TTL, hop and duplicate rules to a
sequence of intermittent contacts.

The governed end-to-end TRC includes non-overlapping bytes for:

```text
PND1 discovery copies
+ PNM1 rendezvous copies
+ PNB1 forwarding control
+ PNC1 custody receipts
+ PCM1 manifest transfer
+ PNA1 availability
+ chunk payload
+ primary ACK
+ retransmission data
+ retransmission ACK
+ optional FEC
```

Blocked TTL/hop contacts and duplicate-suppressed contacts consume zero route
wire bytes in the current model because they are rejected by already-known
local governance state before transmission.

## When physical tests become necessary

Physical boards are **not required** to validate:

- bundle identity;
- TTL/hop semantics;
- custody persistence;
- explicit contact-id idempotency;
- deterministic schedule behavior;
- exact reconstruction;
- logical/non-overlapping TRC accounting.

Physical HW-006 evidence becomes required before making any claim about:

1. how often a usable LoRa contact actually occurs at a given geometry;
2. how long that contact remains usable;
3. how many bytes/chunks can realistically fit inside a contact window;
4. packet-loss/retry behavior in the distance/NLOS transition region;
5. a realistic TTL/contact budget derived from the radio rather than chosen as
   an experiment parameter;
6. automatic bearer selection or routing decisions justified by measured LoRa
   reliability/throughput;
7. changing the frozen PHY on the basis of observed limits.

Current historical physical traces are mainly 42-byte transaction evidence.
They must not be silently extrapolated to differently sized PNB1/PNC1 or other
control frames. When physical access returns, the HW-006 campaign should first
establish the transition region with the frozen 42-byte / 2 dBm baseline, then
measure the specific control/data frame sizes needed to calibrate governed
store-and-forward.
