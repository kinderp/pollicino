# PollicinoNet intermittent store-and-forward

This note defines the first application-independent store-and-forward model for PollicinoNet.

## Goal

The network must be able to complete an exact object delivery even when no permanent path exists from origin to destination.

Example:

```text
time 1: origin <-> relay
time 2:             relay <-> destination
time 3: origin <-> relay
time 4:             relay <-> destination
```

At no time is an `origin -> destination` link required.

## Verified custody

A peer may advertise or forward only material it can verify locally.

For a PCM1 object:

- the PCM1 manifest is stored by its SHA-256 fingerprint;
- each content chunk is stored by its SHA-256 digest;
- a relay forwards only missing chunks that its own `PollicinoStore` reports as valid;
- a corrupt durable chunk is treated as unavailable and is not forwarded;
- exact reconstruction happens only after every manifest chunk is present and the final object hash verifies.

This preserves the existing rule that content addressing is an integrity/reuse mechanism, not hidden reconstruction information.

## One finite contact

`forward_contact()` models one directional opportunity:

```text
source peer
   |
   | PCM1 manifest, only if target lacks it
   v
target peer
   |
   | PNA1 verified availability summary (reverse control direction)
   v
source peer
   |
   | up to N source-owned missing chunks
   v
target peer
```

The contact has an explicit `max_chunks` bound and its own PNF1 transfer-id range.

Later contacts do not need a hidden session object. The target's verified content-addressed store is the durable truth: its new PNA1 summary causes already stored chunks to be skipped naturally.

## Intermittent restart

`DirectoryPollicinoStore` makes custody survive process/device restart.

A later contact may recreate the relay object from the same store directory and continue forwarding previously verified chunks. The origin and destination do not need to have remained connected or alive during the interval.

## No false forwarding after corruption

If a durable relay chunk is altered on disk:

```text
stored filename says digest X
          |
          v
read bytes -> SHA-256 != X
          |
          v
has(X) == false
          |
          +--> not advertised
          +--> not forwarded
```

The route may remain incomplete, which is preferable to asserting a false exact reconstruction.

## End-to-end TRC

The first end-to-end accounting helper combines:

```text
DISCOVERY / PND1 transmissions
+ rendezvous / PNM1 transmissions
+ PCM1 manifest primary data
+ PNA1 availability primary data
+ chunk payload primary data
+ primary ACKs
+ retry data
+ retry ACKs
+ explicit FEC bytes (currently normally zero)
```

These categories are non-overlapping.

Discovery and rendezvous transmission counts are explicit parameters. The implementation does not assume that a descriptor or resolved manifest crossed the scarce link exactly once; experiments may model zero, one or multiple forwards.

The report therefore answers:

> how many accounted bits crossed the modeled delivery path from discovery through exact reconstruction?

It does **not** by itself claim all of those bytes used the same physical bearer. Future work should add per-bearer accounting when mixed LoRa/BLE/Wi-Fi/Internet routes are measured.

## Current boundaries

This model does not yet provide:

- epidemic/gossip routing;
- automatic peer selection;
- trust or authorization policy for relays;
- relay storage quotas/eviction;
- bundle TTL/expiry enforcement;
- custody acknowledgements distinct from PNF1 link ACKs;
- FEC;
- route optimization;
- a deployment packet-loss claim.

Those are intentionally later layers. The current primitive establishes deterministic, verified custody and forwarding first.

## Next experiments

1. heterogeneous contact schedules with several relays;
2. TTL/hop-budget enforcement;
3. duplicate-suppression/custody records;
4. compare direct, one-relay and multi-relay TRC;
5. inject RF replay traces per contact when frame-size evidence exists;
6. eventually execute an intermittent two/three-node physical experiment after HW-006 link characterization.
