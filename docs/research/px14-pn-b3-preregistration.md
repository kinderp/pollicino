# PX14-PN-B3 preregistration

Status: preregistered before implementation. The identifier is the repository
owner's candidate; PX13 recommends independent-process byte I/O but supplies no
authoritative post-PX13 identifier.

## Hypothesis

The existing bounded B2/B2F/B2C/B2A message model can cross a real OS process
and byte-stream boundary without a new persistent correctness authority.
Each worker opens only its own durable D2/D3 root. The relay moves bytes and
accounts for I/O, but never reads endpoint state or computes a missing set.

The existing 42-byte experimental envelopes are preregistered as the only
stream delimiter. Stream reassembly adds no protocol bytes and is not network
fragmentation.

The in-process compact runner's local outcome return is not available across
the process boundary. The registered byte-only experiment uses the existing
B2C summary symmetrically: when an initial summary yields equality or a
detectable decode failure, the responder sends its own summary. The initiator
then establishes equality or starts the existing PX11 exact fallback from the
received bytes. Loss, truncation, corruption, timeout, or process exit never
counts as compact-capacity evidence.

## Success invariants

```text
SHARED_ENDPOINT_OBJECTS = 0
DIRECT_REMOTE_STORE_READS = 0
PARENT_PROTOCOL_SEMANTIC_AUTHORITY = 0
PROCESS_BOUNDARY_CANONICAL_STATE_MISMATCHES = 0
STREAM_SEGMENTATION_DEPENDENT_STATE = 0
PARTIAL_MESSAGE_NATIVE_MUTATIONS = 0
UNBOUNDED_REMOTE_ALLOCATION = 0
PERSISTENT_PROCESS_SESSION_STATE_REQUIRED = NO
PERSISTENT_PEER_PROGRESS_AUTHORITIES = 0
PERSISTENT_ADAPTIVE_POLICY_STATE = 0
APPLICATION_SPECIFIC_PROCESS_IO_BRANCHES = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
FALSE_CONVERGENCE_AFTER_IO_FAILURE = 0
PROCESS_IO_EXTRA_WIRE_BYTES = 0
ONE_PROTOCOL_WRITER_PER_DIRECTION = YES
```

## Kill criteria

Stop before adding persistent ACKs, process/session journals, peer cursors, or
custody state. Partial native mutation from an incomplete message falsifies the
model. If the existing envelope cannot delimit bounded messages, only the
smallest explicitly classified boundary extension may be considered.

## Bounds and exclusions

The reader inherits the largest existing experimental B2 message bound and
rejects an oversized declared body before buffering it. Every worker has a
finite input limit and coordinator timeout. No TCP, UDP, radio, daemon, PNF1,
fragmentation, authentication, encryption, or stable-wire claim enters PX14.

