# Resumable EXACT sessions and RF replay

PollicinoNet now separates three reliability scopes that must not be conflated:

```text
PNF1 frame retry
    |
    v
verified chunk persistence
    |
    v
resumable exact session
```

The radio/H2 protocol is not changed by this layer.

## Why resumability lives above PNF1

PNF1 already provides deterministic fragmentation, CRC, stop-and-wait retry and duplicate-tolerant reassembly for one exact transfer. Making PNF1 itself remember long-lived application progress would couple a small transport frame format to higher-level synchronization policy.

Instead, `ExactSyncSessionState` coordinates the existing PN-005 chunk store:

1. obtain or transfer the PCM1 chunk manifest;
2. receiver advertises a PNA1 availability summary;
3. transfer at most the configured number of currently missing chunks;
4. store each chunk only after full SHA-256 verification;
5. return serializable session state;
6. on the next step, regenerate availability from the receiver store and skip chunks already present;
7. reconstruct only when every manifest chunk is verified;
8. verify the complete object hash.

This makes interruption safe at verified chunk boundaries without altering PNF1.

## State versus durable content

The session state is serializable and records:

- manifest fingerprint;
- next PNF1 transfer ID;
- whether the manifest has already been delivered;
- step count;
- cumulative manifest/availability/chunk wire accounting;
- cumulative retransmission count;
- accounting semantics;
- completion state.

The current `PollicinoStore` is an in-memory content-addressed store. Therefore process/device-restart durability still requires a persistent store implementation. This is the next software step; the current session proves the protocol/state model without pretending RAM survives a reboot.

## Synthetic versus physical replay accounting

The default session transmitter is the deterministic `ScarceLinkProfile` simulator. Its modeled data and ACK byte counts are exact within that model.

A session can instead receive `RFReplayTransmitter.transmit_exact` as its transfer primitive.

Physical replay has a stricter evidence boundary. For an untethered HW-006 failed transaction we know the local frame was transmitted, but we do not know whether the remote node:

- failed to receive/decode it;
- received it but failed to answer;
- transmitted a PONG/ACK that was lost on the return path;
- reset or lost power.

Therefore replay accounting reports:

```text
local transmitted data bytes = exact
confirmed returned ACK bytes  = lower bound
failed-attempt remote bytes    = unknown
```

The resumable session stores this accounting mode and refuses to mix it with deterministic-model exact accounting in the same session.

## Frame-size compatibility

Physical outcomes are conditioned by the transmitted frame size. A recorded 42-byte HW-006 transaction cannot automatically become evidence for a 58-byte session control frame.

`RFReplayTransmitter` therefore checks frame size by default and fails before consuming the physical sample when sizes differ.

`strict_frame_bytes=False` is available only for explicit what-if/extrapolation tests. Results produced in that mode are not new physical evidence.

This is useful scientifically: rather than hiding a missing measurement, the software tells us exactly which physical frame-size evidence must be collected later.

## Current end-to-end software path

The tested path is now:

```text
recorded RF outcomes
        |
        v
RFReplayTransmitter
        |
        v
PNF1 stop-and-wait retry
        |
        v
ExactSyncSessionState
        |
        v
PNA1 receiver availability
        |
        v
only missing verified chunks
        |
        v
SHA-256 exact object reconstruction
```

## Next step

Add a durable content-addressed receiver store plus atomic session-state checkpointing. That will allow a test that stops one process, creates a new process, reloads both store and session state, and resumes without retransmitting already verified chunks.
