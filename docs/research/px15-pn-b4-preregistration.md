# PX15-PN-B4 preregistration

Status: preregistered before implementation. `PX15-PN-B4` is the repository
owner's candidate identifier. PX14 recommends an MTU/fragmentation experiment
but contains no authoritative later gate identifier.

## Hypothesis

A complete lawful B2-family message can cross a generic bounded MTU using only
ephemeral bounded fragment/reassembly state. Native durable D2/D3 state remains
the only persistent progress and possession authority. Fragment loss is whole
message loss for semantic purposes.

## Registered model

Model A is selected provisionally: a minimal new experimental B4 envelope below
B2/B2F/B2C. It uses a full SHA-256 digest of the complete encoded message as
the reassembly identity, total message length, fragment index/count, payload
length, and a fragment-local CRC32. Reassembly supports unordered fragments and
identical duplicates, rejects conflicting duplicates/cross-message mixing, and
allows only one incomplete message per direction.

Legacy PNF1 is prior art, not the selected contract. Its pure codec is close,
but its 32-bit caller transfer ID and absent inherited B2 total-length bound do
not meet the registered identity/allocation requirements. `transmit_exact()`
also couples fragmentation to stop-and-wait retry and ACK behavior. Model C is
rejected. Model D is falsified by lawful messages above each small MTU.

## Success invariants

```text
FRAGMENT_ROUNDTRIP_MISMATCHES = 0
PARTIAL_FRAGMENT_NATIVE_MUTATIONS = 0
UNBOUNDED_FRAGMENT_ALLOCATION = 0
FALSE_REASSEMBLY = 0
CROSS_MESSAGE_CONTAMINATIONS = 0
PERSISTENT_REASSEMBLY_STATE_REQUIRED = NO
PERSISTENT_FRAGMENT_ACK_STATE = 0
PERSISTENT_FRAGMENT_CURSOR_STATE = 0
APPLICATION_SPECIFIC_FRAGMENTATION_BRANCHES = 0
CONCRETE_BEARER_FRAGMENTATION_BRANCHES = 0
FRAGMENTATION_SPECIFIC_D4_CORE_BRANCHES = 0
DIRECT_REMOTE_STORE_READS = 0
FALSE_CONVERGENCE_AFTER_FRAGMENT_LOSS = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

## Kill criterion

Stop before adding durable fragment bitmaps, ACK ledgers, peer fragment cursors,
reassembly journals, retry protocols, custody, or application-aware framing.
Any partial native mutation or requirement for persistent fragment progress
falsifies the preferred model.

## Registered MTUs and bounds

The generic MTU sweep is 64, 128, 256, 512, 1024, 1500, and 4096 bytes. The
fragment header and limits will be derived before final tests from the actual
encoding and inherited `MAX_B2_MESSAGE_BYTES`. All loops and buffers are finite.
No selected MTU is claimed to model a named bearer.
